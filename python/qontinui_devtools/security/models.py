"""
Security models for vulnerability tracking and reporting.

This module defines the data structures used to represent security
vulnerabilities, their severity levels, and comprehensive security reports.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class VulnerabilityType(Enum):
    """Types of security vulnerabilities that can be detected."""

    SQL_INJECTION = "sql_injection"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    HARDCODED_SECRET = "hardcoded_secret"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    WEAK_CRYPTO = "weak_cryptography"
    SSRF = "server_side_request_forgery"
    XXE = "xml_external_entity"


class Severity(Enum):
    """Severity levels for security vulnerabilities."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    def __lt__(self, other):
        """Allow severity comparison for sorting."""
        if not isinstance(other, Severity):
            return NotImplemented
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }
        return severity_order[self] < severity_order[other]

    def __le__(self, other):
        """Allow severity comparison for filtering."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self == other or self < other

    def __gt__(self, other):
        """Allow severity comparison for sorting."""
        if not isinstance(other, Severity):
            return NotImplemented
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }
        return severity_order[self] > severity_order[other]

    def __ge__(self, other):
        """Allow severity comparison for filtering."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self == other or self > other


@dataclass
class Vulnerability:
    """
    Represents a security vulnerability detected in code.

    Attributes:
        type: The type of vulnerability
        severity: Severity level
        file_path: Path to the file containing the vulnerability
        line_number: Line number where the vulnerability was found
        code_snippet: The problematic code
        description: Human-readable description of the issue
        remediation: Actionable steps to fix the vulnerability
        cwe_id: Common Weakness Enumeration identifier
        owasp_category: OWASP Top 10 category
        column_offset: Optional column offset in the line
        end_line_number: Optional end line for multi-line vulnerabilities
        confidence: Confidence level of the detection (0.0-1.0)
    """

    type: VulnerabilityType
    severity: Severity
    file_path: str
    line_number: int
    code_snippet: str
    description: str
    remediation: str
    cwe_id: str
    owasp_category: str
    column_offset: Optional[int] = None
    end_line_number: Optional[int] = None
    confidence: float = 1.0

    def to_dict(self) -> dict:
        """Convert vulnerability to dictionary format."""
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "description": self.description,
            "remediation": self.remediation,
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category,
            "column_offset": self.column_offset,
            "end_line_number": self.end_line_number,
            "confidence": self.confidence,
        }

    def __str__(self) -> str:
        """String representation of vulnerability."""
        return (
            f"{self.severity.value.upper()}: {self.description}\n"
            f"  File: {self.file_path}:{self.line_number}\n"
            f"  Type: {self.type.value}\n"
            f"  CWE: {self.cwe_id}\n"
            f"  OWASP: {self.owasp_category}"
        )


@dataclass
class SecurityReport:
    """
    Comprehensive security analysis report.

    Attributes:
        vulnerabilities: List of detected vulnerabilities
        total_files_scanned: Number of files analyzed
        critical_count: Number of critical vulnerabilities
        high_count: Number of high severity vulnerabilities
        medium_count: Number of medium severity vulnerabilities
        low_count: Number of low severity vulnerabilities
        info_count: Number of informational findings
        scan_duration: Time taken for the scan in seconds
        errors: List of files that couldn't be analyzed
    """

    vulnerabilities: list[Vulnerability] = field(default_factory=list)
    total_files_scanned: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    scan_duration: float = 0.0
    errors: list[str] = field(default_factory=list)

    @property
    def total_vulnerabilities(self) -> int:
        """Total number of vulnerabilities found."""
        return len(self.vulnerabilities)

    @property
    def has_critical(self) -> bool:
        """Check if report contains critical vulnerabilities."""
        return self.critical_count > 0

    @property
    def has_high(self) -> bool:
        """Check if report contains high severity vulnerabilities."""
        return self.high_count > 0

    def get_by_severity(self, severity: Severity) -> list[Vulnerability]:
        """Get all vulnerabilities of a specific severity."""
        return [v for v in self.vulnerabilities if v.severity == severity]

    def get_by_type(self, vuln_type: VulnerabilityType) -> list[Vulnerability]:
        """Get all vulnerabilities of a specific type."""
        return [v for v in self.vulnerabilities if v.type == vuln_type]

    def to_dict(self) -> dict:
        """Convert report to dictionary format."""
        return {
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "total_files_scanned": self.total_files_scanned,
            "total_vulnerabilities": self.total_vulnerabilities,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "info_count": self.info_count,
            "scan_duration": self.scan_duration,
            "errors": self.errors,
        }

    def __str__(self) -> str:
        """String representation of security report."""
        lines = [
            "Security Analysis Report",
            "=" * 50,
            f"Files Scanned: {self.total_files_scanned}",
            f"Total Vulnerabilities: {self.total_vulnerabilities}",
            f"Scan Duration: {self.scan_duration:.2f}s",
            "",
            "Severity Breakdown:",
            f"  Critical: {self.critical_count}",
            f"  High: {self.high_count}",
            f"  Medium: {self.medium_count}",
            f"  Low: {self.low_count}",
            f"  Info: {self.info_count}",
        ]

        if self.errors:
            lines.extend(["", f"Errors: {len(self.errors)} files could not be analyzed"])

        return "\n".join(lines)
