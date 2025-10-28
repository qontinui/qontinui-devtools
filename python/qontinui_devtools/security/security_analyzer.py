"""
Comprehensive security analyzer for Python code.

This module provides static analysis capabilities to detect common security
vulnerabilities including SQL injection, command injection, path traversal,
hardcoded secrets, insecure deserialization, weak cryptography, SSRF, and XXE.
"""

import ast
import os
import re
import time
from pathlib import Path
from typing import Optional

from .models import Severity, SecurityReport, Vulnerability, VulnerabilityType


class SecurityAnalyzer:
    """
    Static security analyzer for Python code.

    Uses AST parsing to detect common security vulnerabilities with
    low false positive rates and actionable remediation guidance.
    """

    # Patterns for detecting hardcoded secrets
    SECRET_PATTERNS = {
        'password': re.compile(
            r'(?i)(password|passwd|pwd)["\']?\s*[:=]\s*["\']([^"\']{8,})["\']'
        ),
        'api_key': re.compile(
            r'(?i)(api[_-]?key|apikey|api[_-]?secret)["\']?\s*[:=]\s*["\']([^"\']{16,})["\']'
        ),
        'token': re.compile(
            r'(?i)(access[_-]?token|auth[_-]?token|bearer[_-]?token)["\']?\s*[:=]\s*["\']([^"\']{16,})["\']'
        ),
        'secret_key': re.compile(
            r'(?i)(secret[_-]?key|private[_-]?key)["\']?\s*[:=]\s*["\']([^"\']{16,})["\']'
        ),
        'aws_key': re.compile(
            r'(AKIA[0-9A-Z]{16})'
        ),
        'generic_secret': re.compile(
            r'(?i)(credentials?|auth)["\']?\s*[:=]\s*["\']([^"\']{16,})["\']'
        )
    }

    # Common SQL operations that might be vulnerable
    SQL_OPERATIONS = {
        'execute', 'executemany', 'raw', 'query', 'select',
        'insert', 'update', 'delete', 'cursor'
    }

    # Dangerous functions for command injection
    DANGEROUS_EXEC_FUNCS = {
        'os.system', 'os.popen', 'os.exec', 'os.execl', 'os.execle',
        'os.execlp', 'os.execlpe', 'os.execv', 'os.execve', 'os.execvp',
        'os.execvpe', 'subprocess.call', 'subprocess.run', 'subprocess.Popen',
        'subprocess.check_call', 'subprocess.check_output'
    }

    # Insecure deserialization functions
    DESERIALIZATION_FUNCS = {
        'pickle.loads', 'pickle.load', 'yaml.load',
        'eval', 'exec', 'compile', '__import__'
    }

    # Weak cryptographic algorithms
    WEAK_CRYPTO = {
        'md5': ('MD5', 'CWE-328'),
        'sha1': ('SHA1', 'CWE-328'),
        'des': ('DES', 'CWE-327'),
        'rc4': ('RC4', 'CWE-327'),
        'blowfish': ('Blowfish', 'CWE-327')
    }

    # File operations that could lead to path traversal
    FILE_OPERATIONS = {
        'open', 'os.open', 'pathlib.Path', 'os.path.join',
        'os.remove', 'os.unlink', 'os.rmdir', 'shutil.rmtree'
    }

    # Network functions that could lead to SSRF
    NETWORK_FUNCS = {
        'requests.get', 'requests.post', 'requests.put', 'requests.delete',
        'urllib.request.urlopen', 'urllib.request.Request',
        'httpx.get', 'httpx.post', 'aiohttp.request'
    }

    # XML parsing functions vulnerable to XXE
    XML_PARSERS = {
        'xml.etree.ElementTree.parse', 'xml.etree.ElementTree.fromstring',
        'xml.etree.ElementTree.XMLParser', 'xml.dom.minidom.parse',
        'xml.dom.minidom.parseString', 'lxml.etree.parse',
        'lxml.etree.fromstring', 'lxml.etree.XMLParser'
    }

    def __init__(self, exclude_patterns: Optional[list[str]] = None):
        """
        Initialize the security analyzer.

        Args:
            exclude_patterns: List of glob patterns to exclude from analysis
        """
        self.exclude_patterns = exclude_patterns or []
        self.vulnerabilities: list[Vulnerability] = []
        self.current_file = ""
        self.current_source_lines: list[str] = []

    def analyze_file(self, file_path: str) -> list[Vulnerability]:
        """
        Analyze a single Python file for security vulnerabilities.

        Args:
            file_path: Path to the Python file

        Returns:
            List of detected vulnerabilities
        """
        self.vulnerabilities = []
        self.current_file = file_path

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
                self.current_source_lines = source.splitlines()

            # Parse AST
            tree = ast.parse(source, filename=file_path)

            # Run all detectors
            self._detect_sql_injection(tree)
            self._detect_command_injection(tree)
            self._detect_path_traversal(tree)
            self._detect_hardcoded_secrets(source)
            self._detect_insecure_deserialization(tree)
            self._detect_weak_crypto(tree)
            self._detect_ssrf(tree)
            self._detect_xxe(tree)

            return self.vulnerabilities

        except SyntaxError:
            # Skip files with syntax errors
            return []
        except Exception:
            # Skip files that can't be parsed
            return []

    def analyze_directory(
        self,
        directory: str,
        recursive: bool = True
    ) -> SecurityReport:
        """
        Analyze all Python files in a directory.

        Args:
            directory: Path to directory
            recursive: Whether to analyze subdirectories

        Returns:
            SecurityReport with all detected vulnerabilities
        """
        start_time = time.time()
        all_vulnerabilities: list[Vulnerability] = []
        files_scanned = 0
        errors: list[str] = []

        directory_path = Path(directory)

        # Find all Python files
        if recursive:
            python_files = list(directory_path.rglob("*.py"))
        else:
            python_files = list(directory_path.glob("*.py"))

        # Filter out excluded patterns
        python_files = [
            f for f in python_files
            if not self._is_excluded(str(f))
        ]

        # Analyze each file
        for file_path in python_files:
            try:
                vulns = self.analyze_file(str(file_path))
                all_vulnerabilities.extend(vulns)
                files_scanned += 1
            except Exception as e:
                errors.append(f"{file_path}: {str(e)}")

        # Count vulnerabilities by severity
        severity_counts = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 0,
            Severity.MEDIUM: 0,
            Severity.LOW: 0,
            Severity.INFO: 0
        }

        for vuln in all_vulnerabilities:
            severity_counts[vuln.severity] += 1

        scan_duration = time.time() - start_time

        return SecurityReport(
            vulnerabilities=all_vulnerabilities,
            total_files_scanned=files_scanned,
            critical_count=severity_counts[Severity.CRITICAL],
            high_count=severity_counts[Severity.HIGH],
            medium_count=severity_counts[Severity.MEDIUM],
            low_count=severity_counts[Severity.LOW],
            info_count=severity_counts[Severity.INFO],
            scan_duration=scan_duration,
            errors=errors
        )

    def _is_excluded(self, file_path: str) -> bool:
        """Check if file matches any exclude pattern."""
        path = Path(file_path)
        for pattern in self.exclude_patterns:
            if path.match(pattern):
                return True
        return False

    def _get_code_snippet(self, lineno: int, context: int = 2) -> str:
        """Get code snippet with context lines."""
        start = max(0, lineno - context - 1)
        end = min(len(self.current_source_lines), lineno + context)
        lines = self.current_source_lines[start:end]
        return '\n'.join(lines)

    def _detect_sql_injection(self, tree: ast.AST) -> None:
        """Detect SQL injection vulnerabilities."""
        for node in ast.walk(tree):
            # Check for string concatenation in SQL operations
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)

                if any(sql_op in func_name.lower() for sql_op in self.SQL_OPERATIONS):
                    # Check if SQL query uses string concatenation or f-strings
                    for arg in node.args:
                        if self._is_dynamic_string(arg):
                            self._add_vulnerability(
                                VulnerabilityType.SQL_INJECTION,
                                Severity.CRITICAL,
                                node.lineno,
                                "SQL query uses string concatenation or f-strings, "
                                "potentially vulnerable to SQL injection",
                                "Use parameterized queries with placeholders (?, %s, or :param) "
                                "instead of string concatenation. Example: "
                                "cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
                                "CWE-89",
                                "A03:2021 - Injection"
                            )

            # Also check for dynamic SQL query assignments
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if 'query' in target.id.lower() or 'sql' in target.id.lower():
                            if self._is_dynamic_string(node.value):
                                self._add_vulnerability(
                                    VulnerabilityType.SQL_INJECTION,
                                    Severity.CRITICAL,
                                    node.lineno,
                                    "SQL query uses string concatenation or f-strings, "
                                    "potentially vulnerable to SQL injection",
                                    "Use parameterized queries with placeholders (?, %s, or :param) "
                                    "instead of string concatenation. Example: "
                                    "cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
                                    "CWE-89",
                                    "A03:2021 - Injection"
                                )

    def _detect_command_injection(self, tree: ast.AST) -> None:
        """Detect command injection vulnerabilities."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)

                # Check for dangerous exec functions
                if func_name in self.DANGEROUS_EXEC_FUNCS:
                    # Check for shell=True in subprocess calls
                    if 'subprocess' in func_name:
                        has_shell_true = any(
                            isinstance(kw, ast.keyword) and
                            kw.arg == 'shell' and
                            isinstance(kw.value, ast.Constant) and
                            kw.value.value is True
                            for kw in node.keywords
                        )

                        if has_shell_true:
                            # Check if command uses dynamic strings
                            if node.args and self._is_dynamic_string(node.args[0]):
                                self._add_vulnerability(
                                    VulnerabilityType.COMMAND_INJECTION,
                                    Severity.CRITICAL,
                                    node.lineno,
                                    f"{func_name} with shell=True and dynamic input "
                                    "is vulnerable to command injection",
                                    "Avoid shell=True. Use list arguments instead: "
                                    "subprocess.run(['cmd', arg1, arg2]). "
                                    "If shell is required, use shlex.quote() to escape input.",
                                    "CWE-78",
                                    "A03:2021 - Injection"
                                )
                        else:
                            # shell=False but check for dynamic strings in list
                            if node.args and self._contains_dynamic_elements(node.args[0]):
                                self._add_vulnerability(
                                    VulnerabilityType.COMMAND_INJECTION,
                                    Severity.HIGH,
                                    node.lineno,
                                    f"{func_name} uses dynamic command arguments",
                                    "Validate and sanitize all user input before using in commands. "
                                    "Use allowlists for acceptable values.",
                                    "CWE-78",
                                    "A03:2021 - Injection"
                                )

                    # os.system is always dangerous with dynamic input
                    elif func_name == 'os.system':
                        if node.args and self._is_dynamic_string(node.args[0]):
                            self._add_vulnerability(
                                VulnerabilityType.COMMAND_INJECTION,
                                Severity.CRITICAL,
                                node.lineno,
                                "os.system() with dynamic input is vulnerable to command injection",
                                "Replace os.system() with subprocess.run() using list arguments. "
                                "Never concatenate user input into shell commands.",
                                "CWE-78",
                                "A03:2021 - Injection"
                            )

    def _detect_path_traversal(self, tree: ast.AST) -> None:
        """Detect path traversal vulnerabilities."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)

                # Check file operations
                if any(file_op in func_name for file_op in self.FILE_OPERATIONS):
                    # Check if path uses dynamic/user input
                    if node.args and self._is_dynamic_string(node.args[0]):
                        # Check if there's path validation
                        has_validation = self._has_path_validation(node)

                        if not has_validation:
                            self._add_vulnerability(
                                VulnerabilityType.PATH_TRAVERSAL,
                                Severity.HIGH,
                                node.lineno,
                                f"{func_name} with unsanitized user input can lead to "
                                "path traversal attacks",
                                "Validate file paths using os.path.abspath() and ensure they "
                                "stay within expected directory. Use os.path.commonpath() to "
                                "check if path is within allowed directory. "
                                "Example: if not path.startswith(safe_dir): raise ValueError()",
                                "CWE-22",
                                "A01:2021 - Broken Access Control"
                            )

    def _detect_hardcoded_secrets(self, source: str) -> None:
        """Detect hardcoded secrets in source code."""
        for secret_type, pattern in self.SECRET_PATTERNS.items():
            for match in pattern.finditer(source):
                # Calculate line number
                lineno = source[:match.start()].count('\n') + 1

                # Skip common false positives (except AWS keys which have specific format)
                matched_text = match.group(0)
                if secret_type != 'aws_key' and self._is_false_positive_secret(matched_text):
                    continue

                severity = Severity.CRITICAL
                if secret_type in ['api_key', 'token', 'aws_key']:
                    severity = Severity.CRITICAL
                elif secret_type == 'password':
                    severity = Severity.HIGH
                else:
                    severity = Severity.MEDIUM

                self._add_vulnerability(
                    VulnerabilityType.HARDCODED_SECRET,
                    severity,
                    lineno,
                    f"Hardcoded {secret_type.replace('_', ' ')} detected in source code",
                    "Store secrets in environment variables or secure secret management "
                    "systems (e.g., AWS Secrets Manager, HashiCorp Vault, Azure Key Vault). "
                    "Use python-decouple or similar libraries to load secrets from .env files. "
                    "Never commit secrets to version control.",
                    "CWE-798",
                    "A07:2021 - Identification and Authentication Failures"
                )

    def _detect_insecure_deserialization(self, tree: ast.AST) -> None:
        """Detect insecure deserialization vulnerabilities."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)

                if func_name in self.DESERIALIZATION_FUNCS:
                    severity = Severity.CRITICAL
                    description = ""
                    remediation = ""

                    if 'pickle' in func_name:
                        description = (
                            "pickle.loads/load with untrusted data can execute "
                            "arbitrary code during deserialization"
                        )
                        remediation = (
                            "Avoid pickle for untrusted data. Use JSON or other safe "
                            "serialization formats. If pickle is necessary, implement "
                            "HMAC signature verification to ensure data integrity."
                        )
                    elif 'yaml.load' in func_name and not self._uses_safe_loader(node):
                        description = (
                            "yaml.load() without SafeLoader can execute arbitrary code"
                        )
                        remediation = (
                            "Use yaml.safe_load() instead of yaml.load(), or specify "
                            "Loader=yaml.SafeLoader explicitly."
                        )
                    elif func_name in ['eval', 'exec']:
                        description = (
                            f"{func_name}() with user input can execute arbitrary code"
                        )
                        remediation = (
                            f"Avoid {func_name}() with user input. Use ast.literal_eval() "
                            "for safe evaluation of Python literals, or implement proper "
                            "parsing/validation logic."
                        )
                    elif func_name == 'compile':
                        description = "compile() with user input can create malicious code objects"
                        remediation = "Avoid compile() with user input. Use safe alternatives."
                    else:
                        continue

                    self._add_vulnerability(
                        VulnerabilityType.INSECURE_DESERIALIZATION,
                        severity,
                        node.lineno,
                        description,
                        remediation,
                        "CWE-502",
                        "A08:2021 - Software and Data Integrity Failures"
                    )

    def _detect_weak_crypto(self, tree: ast.AST) -> None:
        """Detect weak cryptographic algorithms."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func).lower()

                # Check for weak hash algorithms
                for weak_algo, (algo_name, cwe) in self.WEAK_CRYPTO.items():
                    if weak_algo in func_name and 'hashlib' in func_name:
                        self._add_vulnerability(
                            VulnerabilityType.WEAK_CRYPTO,
                            Severity.MEDIUM,
                            node.lineno,
                            f"Use of weak cryptographic algorithm: {algo_name}",
                            f"Replace {algo_name} with SHA-256 or SHA-3 for hashing. "
                            "For password hashing, use bcrypt, scrypt, or Argon2. "
                            "Example: hashlib.sha256() or from passlib.hash import bcrypt",
                            cwe,
                            "A02:2021 - Cryptographic Failures"
                        )

            # Check for algorithm specification in strings
            elif isinstance(node, ast.Constant):
                if isinstance(node.value, str):
                    value_lower = node.value.lower()
                    for weak_algo, (algo_name, cwe) in self.WEAK_CRYPTO.items():
                        if weak_algo == value_lower:
                            self._add_vulnerability(
                                VulnerabilityType.WEAK_CRYPTO,
                                Severity.MEDIUM,
                                node.lineno,
                                f"Weak cryptographic algorithm specified: {algo_name}",
                                f"Replace {algo_name} with stronger alternatives like "
                                "AES-256-GCM for encryption or SHA-256 for hashing.",
                                cwe,
                                "A02:2021 - Cryptographic Failures"
                            )

    def _detect_ssrf(self, tree: ast.AST) -> None:
        """Detect Server-Side Request Forgery vulnerabilities."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)

                if any(net_func in func_name for net_func in self.NETWORK_FUNCS):
                    # Check if URL is dynamic or from variable
                    if node.args:
                        url_arg = node.args[0]
                        if self._is_dynamic_string(url_arg) or isinstance(url_arg, ast.Name):
                            self._add_vulnerability(
                                VulnerabilityType.SSRF,
                                Severity.HIGH,
                                node.lineno,
                                f"{func_name} with user-controlled URL can lead to SSRF attacks",
                                "Validate and sanitize URLs. Use an allowlist of permitted domains. "
                                "Parse URLs and verify scheme, host, and port. Block private IP ranges "
                                "(127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16). "
                                "Example: if urlparse(url).hostname not in ALLOWED_HOSTS: raise ValueError()",
                                "CWE-918",
                                "A10:2021 - Server-Side Request Forgery"
                            )

    def _detect_xxe(self, tree: ast.AST) -> None:
        """Detect XML External Entity vulnerabilities."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)

                # Check each XML parser pattern
                for xml_parser in self.XML_PARSERS:
                    parts = xml_parser.split('.')
                    if len(parts) >= 2 and parts[-1] in func_name:
                        # Check if secure processing is enabled
                        has_secure_processing = self._has_secure_xml_processing(node)

                        if not has_secure_processing:
                            severity = Severity.HIGH

                            self._add_vulnerability(
                                VulnerabilityType.XXE,
                                severity,
                                node.lineno,
                                f"{func_name} without secure processing is vulnerable to XXE attacks",
                                "Disable external entity processing. For xml.etree.ElementTree, use: "
                                "parser = ET.XMLParser(); parser.entity = {}. "
                                "For lxml, use: parser = etree.XMLParser(resolve_entities=False). "
                                "Use defusedxml library for safer XML parsing.",
                                "CWE-611",
                                "A05:2021 - Security Misconfiguration"
                            )
                            break  # Only report once per call

    def _get_func_name(self, node: ast.AST) -> str:
        """Extract full function name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_name = self._get_func_name(node.value)
            return f"{value_name}.{node.attr}"
        return ""

    def _is_dynamic_string(self, node: ast.AST) -> bool:
        """Check if a node represents a dynamic string (f-string, concatenation, format)."""
        if isinstance(node, ast.JoinedStr):
            # f-string
            return True
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
            # String concatenation or % formatting
            # Check if either side involves a name (variable)
            if self._contains_name(node.left) or self._contains_name(node.right):
                return True
        elif isinstance(node, ast.Call):
            # Check for .format() calls
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == 'format':
                    return True
        return False

    def _contains_name(self, node: ast.AST) -> bool:
        """Check if a node contains a Name node (variable reference)."""
        if isinstance(node, ast.Name):
            return True
        elif isinstance(node, ast.BinOp):
            return self._contains_name(node.left) or self._contains_name(node.right)
        elif isinstance(node, ast.Call):
            return True
        return False

    def _contains_dynamic_elements(self, node: ast.AST) -> bool:
        """Check if a list or other container has dynamic elements."""
        if isinstance(node, (ast.List, ast.Tuple)):
            return any(self._is_dynamic_string(elem) for elem in node.elts)
        return False

    def _has_path_validation(self, node: ast.Call) -> bool:
        """Check if there's path validation nearby (heuristic)."""
        # This is a simple heuristic - in real implementation,
        # would need more sophisticated control flow analysis
        return False

    def _uses_safe_loader(self, node: ast.Call) -> bool:
        """Check if yaml.load uses SafeLoader."""
        for kw in node.keywords:
            if kw.arg == 'Loader':
                loader_name = self._get_func_name(kw.value)
                if 'SafeLoader' in loader_name or 'safe' in loader_name.lower():
                    return True
        return False

    def _has_secure_xml_processing(self, node: ast.Call) -> bool:
        """Check if XML parsing uses secure settings."""
        # Check if a parser keyword argument is provided
        # (assume it might be configured securely)
        for kw in node.keywords:
            if kw.arg == 'parser':
                # If a parser is explicitly provided, assume it might be secure
                # (full data flow analysis would be needed for certainty)
                return True
            if kw.arg in ['resolve_entities', 'no_network']:
                if isinstance(kw.value, ast.Constant) and kw.value.value is False:
                    return True
        return False

    def _is_false_positive_secret(self, text: str) -> bool:
        """Filter common false positives for secret detection."""
        false_positives = [
            'example', 'sample', 'test', 'dummy', 'placeholder',
            'your_', 'my_', '<', '>', '{', '}', 'xxx', '***',
            'changeme', 'change_me', 'replace', 'todo', 'fixme'
        ]
        text_lower = text.lower()
        return any(fp in text_lower for fp in false_positives)

    def _add_vulnerability(
        self,
        vuln_type: VulnerabilityType,
        severity: Severity,
        lineno: int,
        description: str,
        remediation: str,
        cwe_id: str,
        owasp_category: str,
        confidence: float = 1.0
    ) -> None:
        """Add a vulnerability to the current analysis."""
        vulnerability = Vulnerability(
            type=vuln_type,
            severity=severity,
            file_path=self.current_file,
            line_number=lineno,
            code_snippet=self._get_code_snippet(lineno),
            description=description,
            remediation=remediation,
            cwe_id=cwe_id,
            owasp_category=owasp_category,
            confidence=confidence
        )
        self.vulnerabilities.append(vulnerability)
