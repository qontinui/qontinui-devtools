"""PyPI client for fetching package information.

This module provides a client for interacting with the PyPI JSON API to fetch
package metadata, versions, release dates, and license information with caching
and rate limiting support.
"""

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class PackageInfo:
    """Package information from PyPI."""

    name: str
    latest_version: str
    versions: list[str]
    release_dates: dict[str, datetime]
    license: str | None
    homepage: str | None
    repository: str | None
    maintainers: list[str]
    dependencies: list[str]
    download_count: int
    description: str
    requires_python: str | None

    def get_release_date(self, version: str) -> datetime | None:
        """Get release date for a specific version."""
        return self.release_dates.get(version)


class PyPIClient:
    """Client for fetching package information from PyPI.

    Provides caching, rate limiting, and robust error handling for PyPI API requests.
    """

    PYPI_JSON_API = "https://pypi.org/pypi/{package}/json"
    DEFAULT_CACHE_DIR = Path.home() / ".cache" / "qontinui-devtools" / "pypi"
    DEFAULT_CACHE_TTL = timedelta(hours=24)
    DEFAULT_RATE_LIMIT = 1.0  # seconds between requests

    def __init__(
        self,
        cache_dir: Path | None = None,
        cache_ttl: timedelta | None = None,
        rate_limit: float | None = None,
        offline_mode: bool = False,
        timeout: int = 10,
    ):
        """Initialize PyPI client.

        Args:
            cache_dir: Directory for caching responses
            cache_ttl: Time-to-live for cached entries
            rate_limit: Minimum seconds between requests
            offline_mode: Use only cached data
            timeout: Request timeout in seconds
        """
        self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
        self.cache_ttl = cache_ttl or self.DEFAULT_CACHE_TTL
        self.rate_limit = rate_limit or self.DEFAULT_RATE_LIMIT
        self.offline_mode = offline_mode
        self.timeout = timeout

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._last_request_time = 0.0
        self._request_count = 0

    def get_package_info(self, package_name: str) -> PackageInfo | None:
        """Fetch package information from PyPI.

        Args:
            package_name: Name of the package

        Returns:
            PackageInfo object or None if not found
        """
        # Normalize package name
        normalized_name = self._normalize_package_name(package_name)

        # Try to load from cache
        cached_data = self._load_from_cache(normalized_name)
        if cached_data:
            return self._parse_package_data(cached_data)

        # If offline mode and no cache, return None
        if self.offline_mode:
            return None

        # Fetch from PyPI
        try:
            data = self._fetch_from_pypi(normalized_name)
            if data:
                self._save_to_cache(normalized_name, data)
                return self._parse_package_data(data)
        except Exception:
            # Silent failure, return None
            pass

        return None

    def get_latest_version(self, package_name: str) -> str | None:
        """Get the latest version of a package.

        Args:
            package_name: Name of the package

        Returns:
            Latest version string or None
        """
        info = self.get_package_info(package_name)
        return info.latest_version if info else None

    def get_all_versions(self, package_name: str) -> list[str]:
        """Get all available versions of a package.

        Args:
            package_name: Name of the package

        Returns:
            List of version strings
        """
        info = self.get_package_info(package_name)
        return info.versions if info else []

    def get_package_license(self, package_name: str) -> str | None:
        """Get package license.

        Args:
            package_name: Name of the package

        Returns:
            License string or None
        """
        info = self.get_package_info(package_name)
        return info.license if info else None

    def clear_cache(self, package_name: str | None = None) -> None:
        """Clear cached data.

        Args:
            package_name: Specific package to clear, or None for all
        """
        if package_name:
            cache_file = self._get_cache_file(package_name)
            if cache_file.exists():
                cache_file.unlink()
        else:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()

    def _normalize_package_name(self, name: str) -> str:
        """Normalize package name (lowercase, replace underscores)."""
        return name.lower().replace("_", "-")

    def _get_cache_file(self, package_name: str) -> Path:
        """Get cache file path for a package."""
        # Use hash to avoid filesystem issues with special characters
        name_hash = hashlib.md5(package_name.encode()).hexdigest()
        return self.cache_dir / f"{package_name}_{name_hash}.json"

    def _load_from_cache(self, package_name: str) -> dict[str, Any] | None:
        """Load package data from cache if valid.

        Args:
            package_name: Name of the package

        Returns:
            Cached data or None
        """
        cache_file = self._get_cache_file(package_name)

        if not cache_file.exists():
            return None

        # Check if cache is expired
        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if cache_age > self.cache_ttl:
            return None

        try:
            with open(cache_file) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    def _save_to_cache(self, package_name: str, data: dict[str, Any]) -> None:
        """Save package data to cache.

        Args:
            package_name: Name of the package
            data: Data to cache
        """
        cache_file = self._get_cache_file(package_name)

        try:
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except OSError:
            pass  # Silently fail on cache write errors

    def _fetch_from_pypi(self, package_name: str) -> dict[str, Any] | None:
        """Fetch package data from PyPI API.

        Args:
            package_name: Name of the package

        Returns:
            Package data or None
        """
        # Rate limiting
        time_since_last = time.time() - self._last_request_time
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)

        url = self.PYPI_JSON_API.format(package=package_name)

        try:
            req = Request(url)
            req.add_header("User-Agent", "qontinui-devtools/1.0")

            with urlopen(req, timeout=self.timeout) as response:
                self._last_request_time = time.time()
                self._request_count += 1

                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    return data

        except HTTPError as e:
            if e.code == 404:
                # Package not found
                return None
            # Other HTTP errors
            pass
        except (URLError, TimeoutError):
            # Network errors
            pass

        return None

    def _parse_package_data(self, data: dict[str, Any]) -> PackageInfo:
        """Parse PyPI API response into PackageInfo.

        Args:
            data: Raw PyPI API response

        Returns:
            PackageInfo object
        """
        info_data = data.get("info", {})
        releases = data.get("releases", {})

        # Get versions and release dates
        versions = list(releases.keys())
        release_dates: dict[str, datetime] = {}

        for version, release_list in releases.items():
            if release_list and isinstance(release_list, list):
                # Get the upload time of the first file
                upload_time_str = release_list[0].get("upload_time_iso_8601")
                if upload_time_str:
                    try:
                        release_dates[version] = datetime.fromisoformat(
                            upload_time_str.replace("Z", "+00:00")
                        )
                    except ValueError:
                        pass

        # Extract dependencies from requires_dist
        dependencies=[],
        requires_dist = info_data.get("requires_dist") or []
        for req in requires_dist:
            if isinstance(req, str):
                # Parse "package (>=version)" format
                dep_name = req.split()[0].split("[")[0].strip()
                if dep_name and not any(extra in req.lower() for extra in ["extra", "dev", "test"]):
                    dependencies.append(dep_name)

        # Extract maintainers
        maintainers: list[Any] = []
        if info_data.get("author"):
            maintainers.append(info_data["author"])
        if info_data.get("maintainer") and info_data["maintainer"] != info_data.get("author"):
            maintainers.append(info_data["maintainer"])

        return PackageInfo(
            name=info_data.get("name", ""),
            latest_version=info_data.get("version", ""),
            versions=versions,
            release_dates=release_dates,
            license=info_data.get("license"),
            homepage=info_data.get("home_page"),
            repository=info_data.get("project_url")
            or info_data.get("project_urls", {}).get("Repository"),
            maintainers=maintainers,
            dependencies=dependencies,
            download_count=0,  # PyPI doesn't provide this in JSON API
            description=info_data.get("summary", ""),
            requires_python=info_data.get("requires_python"),
        )

    def get_statistics(self) -> dict[str, Any]:
        """Get client statistics.

        Returns:
            Dictionary with request count and cache info
        """
        cache_files = list(self.cache_dir.glob("*.json"))

        return {
            "requests_made": self._request_count,
            "cache_entries": len(cache_files),
            "cache_dir": str(self.cache_dir),
            "offline_mode": self.offline_mode,
        }
