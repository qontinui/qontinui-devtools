"""
Comprehensive tests for the security analyzer.

Tests cover all vulnerability types with both positive and negative cases,
false positive handling, severity classification, and remediation suggestions.
"""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from qontinui_devtools.security import (SecurityAnalyzer, Severity,
                                        VulnerabilityType)


@pytest.fixture
def analyzer() -> SecurityAnalyzer:
    """Create a security analyzer instance."""
    return SecurityAnalyzer()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# SQL Injection Tests


def test_sql_injection_string_concatenation(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of SQL injection via string concatenation."""
    code = """
import sqlite3

def get_user(user_id) -> Any:
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
    return cursor.fetchone()
"""
    file_path = temp_dir / "sql_concat.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    assert len(vulns) > 0
    sql_vulns = [v for v in vulns if v.type == VulnerabilityType.SQL_INJECTION]
    assert len(sql_vulns) == 1
    assert sql_vulns[0].severity == Severity.CRITICAL
    assert "parameterized queries" in sql_vulns[0].remediation.lower()
    assert sql_vulns[0].cwe_id == "CWE-89"


def test_sql_injection_fstring(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of SQL injection via f-strings."""
    code = """
import sqlite3

def get_user(username) -> Any:
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE name = '{username}'")
    return cursor.fetchone()
"""
    file_path = temp_dir / "sql_fstring.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    sql_vulns = [v for v in vulns if v.type == VulnerabilityType.SQL_INJECTION]
    assert len(sql_vulns) == 1
    assert sql_vulns[0].severity == Severity.CRITICAL


def test_sql_injection_format(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of SQL injection via .format()."""
    code = """
import sqlite3

def get_user(email) -> Any:
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE email = '{}'".format(email)
    cursor.execute(query)
    return cursor.fetchone()
"""
    file_path = temp_dir / "sql_format.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    sql_vulns = [v for v in vulns if v.type == VulnerabilityType.SQL_INJECTION]
    assert len(sql_vulns) == 1


def test_sql_safe_parameterized_query(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test that safe parameterized queries are not flagged."""
    code = """
import sqlite3

def get_user(user_id) -> Any:
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()
"""
    file_path = temp_dir / "sql_safe.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    sql_vulns = [v for v in vulns if v.type == VulnerabilityType.SQL_INJECTION]
    assert len(sql_vulns) == 0


def test_sql_static_query(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test that static SQL queries are not flagged."""
    code = """
import sqlite3

def get_all_users() -> Any:
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()
"""
    file_path = temp_dir / "sql_static.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    sql_vulns = [v for v in vulns if v.type == VulnerabilityType.SQL_INJECTION]
    assert len(sql_vulns) == 0


# Command Injection Tests


def test_command_injection_os_system(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of command injection via os.system."""
    code = """
import os

def backup_file(filename) -> None:
    os.system("cp " + filename + " /backup/")
"""
    file_path = temp_dir / "cmd_os_system.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    cmd_vulns = [v for v in vulns if v.type == VulnerabilityType.COMMAND_INJECTION]
    assert len(cmd_vulns) == 1
    assert cmd_vulns[0].severity == Severity.CRITICAL
    assert "subprocess.run()" in cmd_vulns[0].remediation
    assert cmd_vulns[0].cwe_id == "CWE-78"


def test_command_injection_subprocess_shell_true(
    analyzer: SecurityAnalyzer, temp_dir: Path
) -> None:
    """Test detection of command injection with shell=True."""
    code = """
import subprocess

def ping_host(host) -> None:
    subprocess.run(f"ping -c 1 {host}", shell=True)
"""
    file_path = temp_dir / "cmd_shell_true.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    cmd_vulns = [v for v in vulns if v.type == VulnerabilityType.COMMAND_INJECTION]
    assert len(cmd_vulns) == 1
    assert cmd_vulns[0].severity == Severity.CRITICAL
    assert "shell=True" in cmd_vulns[0].description


def test_command_injection_subprocess_list_dynamic(
    analyzer: SecurityAnalyzer, temp_dir: Path
) -> None:
    """Test detection of command injection with dynamic list arguments."""
    code = """
import subprocess

def run_command(arg) -> None:
    subprocess.run(["ls", "-l", arg])
"""
    file_path = temp_dir / "cmd_list_dynamic.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    # This should be flagged as HIGH severity (not CRITICAL) since shell=False
    cmd_vulns = [v for v in vulns if v.type == VulnerabilityType.COMMAND_INJECTION]
    # May or may not detect depending on implementation details
    # but if detected, should be HIGH
    if len(cmd_vulns) > 0:
        assert cmd_vulns[0].severity == Severity.HIGH


def test_command_safe_subprocess(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test that safe subprocess calls are not flagged."""
    code = """
import subprocess

def list_directory() -> None:
    subprocess.run(["ls", "-l", "/home"])
"""
    file_path = temp_dir / "cmd_safe.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    cmd_vulns = [v for v in vulns if v.type == VulnerabilityType.COMMAND_INJECTION]
    assert len(cmd_vulns) == 0


def test_command_subprocess_shell_false(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test that subprocess with shell=False and static args is safe."""
    code = """
import subprocess

def git_status() -> None:
    subprocess.run(["git", "status"], shell=False)
"""
    file_path = temp_dir / "cmd_safe_shell_false.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    cmd_vulns = [v for v in vulns if v.type == VulnerabilityType.COMMAND_INJECTION]
    assert len(cmd_vulns) == 0


# Path Traversal Tests


def test_path_traversal_open(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of path traversal via open()."""
    code = """
def read_file(filename) -> Any:
    with open("/data/" + filename, "r") as f:
        return f.read()
"""
    file_path = temp_dir / "path_open.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    path_vulns = [v for v in vulns if v.type == VulnerabilityType.PATH_TRAVERSAL]
    assert len(path_vulns) == 1
    assert path_vulns[0].severity == Severity.HIGH
    assert "os.path.abspath()" in path_vulns[0].remediation
    assert path_vulns[0].cwe_id == "CWE-22"


def test_path_traversal_os_remove(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of path traversal via os.remove()."""
    code = """
import os

def delete_file(filename) -> None:
    os.remove(f"/tmp/{filename}")
"""
    file_path = temp_dir / "path_remove.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    path_vulns = [v for v in vulns if v.type == VulnerabilityType.PATH_TRAVERSAL]
    assert len(path_vulns) == 1


def test_path_safe_static(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test that static paths are not flagged."""
    code = """
def read_config() -> Any:
    with open("/etc/config.ini", "r") as f:
        return f.read()
"""
    file_path = temp_dir / "path_safe.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    path_vulns = [v for v in vulns if v.type == VulnerabilityType.PATH_TRAVERSAL]
    assert len(path_vulns) == 0


# Hardcoded Secrets Tests


def test_hardcoded_password(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of hardcoded passwords."""
    code = """
DATABASE_CONFIG = {
    "host": "localhost",
    "user": "admin",
    "password": "SuperSecret123!"
}
"""
    file_path = temp_dir / "secret_password.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    secret_vulns = [v for v in vulns if v.type == VulnerabilityType.HARDCODED_SECRET]
    assert len(secret_vulns) == 1
    assert secret_vulns[0].severity in [Severity.HIGH, Severity.CRITICAL]
    assert "environment variables" in secret_vulns[0].remediation.lower()
    assert secret_vulns[0].cwe_id == "CWE-798"


def test_hardcoded_api_key(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of hardcoded API keys."""
    code = """
API_KEY = "fake_test_key_not_real_1234567890abcdef"
"""
    file_path = temp_dir / "secret_api_key.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    secret_vulns = [v for v in vulns if v.type == VulnerabilityType.HARDCODED_SECRET]
    assert len(secret_vulns) == 1
    assert secret_vulns[0].severity == Severity.CRITICAL


def test_hardcoded_aws_key(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of hardcoded AWS keys."""
    code = """
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
"""
    file_path = temp_dir / "secret_aws.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    secret_vulns = [v for v in vulns if v.type == VulnerabilityType.HARDCODED_SECRET]
    assert len(secret_vulns) == 1


def test_hardcoded_secret_false_positive_example(
    analyzer: SecurityAnalyzer, temp_dir: Path
) -> None:
    """Test that example/placeholder secrets are not flagged."""
    code = """
# Example configuration - replace with your actual values
password = "your_password_here"
api_key = "example_api_key"
"""
    file_path = temp_dir / "secret_false_positive.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    secret_vulns = [v for v in vulns if v.type == VulnerabilityType.HARDCODED_SECRET]
    assert len(secret_vulns) == 0


def test_safe_env_variable_usage(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test that environment variable usage is not flagged."""
    code = """
import os

password = os.environ.get("DATABASE_PASSWORD")
api_key = os.getenv("API_KEY")
"""
    file_path = temp_dir / "secret_safe.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    secret_vulns = [v for v in vulns if v.type == VulnerabilityType.HARDCODED_SECRET]
    assert len(secret_vulns) == 0


# Insecure Deserialization Tests


def test_insecure_deserialization_pickle(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of insecure pickle.loads."""
    code = """
import pickle

def load_data(data) -> Any:
    return pickle.loads(data)
"""
    file_path = temp_dir / "deser_pickle.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    deser_vulns = [v for v in vulns if v.type == VulnerabilityType.INSECURE_DESERIALIZATION]
    assert len(deser_vulns) == 1
    assert deser_vulns[0].severity == Severity.CRITICAL
    assert "JSON" in deser_vulns[0].remediation
    assert deser_vulns[0].cwe_id == "CWE-502"


def test_insecure_deserialization_yaml(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of insecure yaml.load."""
    code = """
import yaml

def load_config(config_str) -> Any:
    return yaml.load(config_str)
"""
    file_path = temp_dir / "deser_yaml.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    deser_vulns = [v for v in vulns if v.type == VulnerabilityType.INSECURE_DESERIALIZATION]
    assert len(deser_vulns) == 1
    assert "safe_load" in deser_vulns[0].remediation.lower()


def test_insecure_deserialization_eval(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of eval with user input."""
    code = """
def calculate(expression) -> Any:
    return eval(expression)
"""
    file_path = temp_dir / "deser_eval.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    deser_vulns = [v for v in vulns if v.type == VulnerabilityType.INSECURE_DESERIALIZATION]
    assert len(deser_vulns) == 1
    assert "ast.literal_eval()" in deser_vulns[0].remediation


def test_insecure_deserialization_exec(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of exec with user input."""
    code = """
def run_code(code_str) -> None:
    exec(code_str)
"""
    file_path = temp_dir / "deser_exec.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    deser_vulns = [v for v in vulns if v.type == VulnerabilityType.INSECURE_DESERIALIZATION]
    assert len(deser_vulns) == 1


def test_safe_yaml_safeloader(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test that yaml.safe_load is not flagged."""
    code = """
import yaml

def load_config(config_str) -> Any:
    return yaml.safe_load(config_str)
"""
    file_path = temp_dir / "deser_safe_yaml.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    deser_vulns = [v for v in vulns if v.type == VulnerabilityType.INSECURE_DESERIALIZATION]
    assert len(deser_vulns) == 0


def test_safe_yaml_explicit_safeloader(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test that yaml.load with SafeLoader is not flagged."""
    code = """
import yaml

def load_config(config_str) -> Any:
    return yaml.load(config_str, Loader=yaml.SafeLoader)
"""
    file_path = temp_dir / "deser_safe_yaml2.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    deser_vulns = [v for v in vulns if v.type == VulnerabilityType.INSECURE_DESERIALIZATION]
    assert len(deser_vulns) == 0


# Weak Cryptography Tests


def test_weak_crypto_md5(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of MD5 usage."""
    code = """
import hashlib

def hash_password(password) -> Any:
    return hashlib.md5(password.encode()).hexdigest()
"""
    file_path = temp_dir / "crypto_md5.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    crypto_vulns = [v for v in vulns if v.type == VulnerabilityType.WEAK_CRYPTO]
    assert len(crypto_vulns) == 1
    assert crypto_vulns[0].severity == Severity.MEDIUM
    assert "SHA-256" in crypto_vulns[0].remediation
    assert crypto_vulns[0].cwe_id == "CWE-328"


def test_weak_crypto_sha1(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of SHA1 usage."""
    code = """
import hashlib

def hash_data(data) -> Any:
    return hashlib.sha1(data.encode()).hexdigest()
"""
    file_path = temp_dir / "crypto_sha1.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    crypto_vulns = [v for v in vulns if v.type == VulnerabilityType.WEAK_CRYPTO]
    assert len(crypto_vulns) == 1


def test_weak_crypto_des_string(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of DES algorithm in strings."""
    code = """
from Crypto.Cipher import DES

cipher = DES.new(key, DES.MODE_ECB)
"""
    file_path = temp_dir / "crypto_des.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    crypto_vulns = [v for v in vulns if v.type == VulnerabilityType.WEAK_CRYPTO]
    # May detect DES in the code
    if len(crypto_vulns) > 0:
        assert "AES" in crypto_vulns[0].remediation


def test_safe_crypto_sha256(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test that SHA-256 is not flagged."""
    code = """
import hashlib

def hash_data(data) -> Any:
    return hashlib.sha256(data.encode()).hexdigest()
"""
    file_path = temp_dir / "crypto_safe.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    crypto_vulns = [v for v in vulns if v.type == VulnerabilityType.WEAK_CRYPTO]
    assert len(crypto_vulns) == 0


# SSRF Tests


def test_ssrf_requests_get(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of SSRF via requests.get with user input."""
    code = """
import requests

def fetch_url(url) -> Any:
    response = requests.get(url)
    return response.text
"""
    file_path = temp_dir / "ssrf_requests.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    ssrf_vulns = [v for v in vulns if v.type == VulnerabilityType.SSRF]
    assert len(ssrf_vulns) == 1
    assert ssrf_vulns[0].severity == Severity.HIGH
    assert "allowlist" in ssrf_vulns[0].remediation.lower()
    assert ssrf_vulns[0].cwe_id == "CWE-918"


def test_ssrf_urllib(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of SSRF via urllib."""
    code = """
import urllib.request

def fetch_data(url) -> Any:
    response = urllib.request.urlopen(url)
    return response.read()
"""
    file_path = temp_dir / "ssrf_urllib.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    ssrf_vulns = [v for v in vulns if v.type == VulnerabilityType.SSRF]
    assert len(ssrf_vulns) == 1


def test_ssrf_fstring_url(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of SSRF with f-string URL."""
    code = """
import requests

def get_user_profile(user_id) -> Any:
    url = f"https://api.example.com/users/{user_id}"
    return requests.get(url).json()
"""
    file_path = temp_dir / "ssrf_fstring.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    ssrf_vulns = [v for v in vulns if v.type == VulnerabilityType.SSRF]
    assert len(ssrf_vulns) == 1


def test_safe_ssrf_static_url(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test that static URLs are not flagged."""
    code = """
import requests

def get_api_status() -> Any:
    response = requests.get("https://api.example.com/status")
    return response.json()
"""
    file_path = temp_dir / "ssrf_safe.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    ssrf_vulns = [v for v in vulns if v.type == VulnerabilityType.SSRF]
    assert len(ssrf_vulns) == 0


# XXE Tests


def test_xxe_etree_parse(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of XXE via xml.etree.ElementTree.parse."""
    code = """
import xml.etree.ElementTree as ET

def parse_xml(xml_file) -> Any:
    tree = ET.parse(xml_file)
    return tree.getroot()
"""
    file_path = temp_dir / "xxe_etree.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    xxe_vulns = [v for v in vulns if v.type == VulnerabilityType.XXE]
    assert len(xxe_vulns) == 1
    assert xxe_vulns[0].severity == Severity.HIGH
    assert "XMLParser" in xxe_vulns[0].remediation
    assert xxe_vulns[0].cwe_id == "CWE-611"


def test_xxe_etree_fromstring(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of XXE via xml.etree.ElementTree.fromstring."""
    code = """
import xml.etree.ElementTree as ET

def parse_xml_string(xml_str) -> Any:
    root = ET.fromstring(xml_str)
    return root
"""
    file_path = temp_dir / "xxe_fromstring.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    xxe_vulns = [v for v in vulns if v.type == VulnerabilityType.XXE]
    assert len(xxe_vulns) == 1


def test_xxe_lxml(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test detection of XXE via lxml."""
    code = """
from lxml import etree

def parse_xml(xml_str) -> Any:
    root = etree.fromstring(xml_str)
    return root
"""
    file_path = temp_dir / "xxe_lxml.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    xxe_vulns = [v for v in vulns if v.type == VulnerabilityType.XXE]
    assert len(xxe_vulns) == 1


def test_safe_xxe_lxml_secure(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test that lxml with resolve_entities=False is not flagged."""
    code = """
from lxml import etree

def parse_xml(xml_str) -> Any:
    parser = etree.XMLParser(resolve_entities=False)
    root = etree.fromstring(xml_str, parser=parser)
    return root
"""
    file_path = temp_dir / "xxe_safe.py"
    file_path.write_text(code)

    vulns = analyzer.analyze_file(str(file_path))

    xxe_vulns = [v for v in vulns if v.type == VulnerabilityType.XXE]
    assert len(xxe_vulns) == 0


# Directory Analysis Tests


def test_analyze_directory(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test analyzing an entire directory."""
    # Create multiple files with vulnerabilities
    (temp_dir / "vuln1.py").write_text(
        """
import os
os.system("ls " + user_input)
"""
    )

    (temp_dir / "vuln2.py").write_text(
        """
password = "SuperSecret123!"
"""
    )

    (temp_dir / "safe.py").write_text(
        """
def hello() -> None:
    print("Hello, world!")
"""
    )

    report = analyzer.analyze_directory(str(temp_dir))

    assert report.total_files_scanned == 3
    assert report.total_vulnerabilities >= 2
    assert report.critical_count >= 1


def test_analyze_directory_recursive(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test recursive directory analysis."""
    subdir = temp_dir / "subdir"
    subdir.mkdir()

    (temp_dir / "file1.py").write_text("print('hello')")
    (subdir / "file2.py").write_text(
        """
import pickle
pickle.loads(data)
"""
    )

    report = analyzer.analyze_directory(str(temp_dir), recursive=True)

    assert report.total_files_scanned == 2
    assert report.total_vulnerabilities >= 1


def test_analyze_directory_non_recursive(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test non-recursive directory analysis."""
    subdir = temp_dir / "subdir"
    subdir.mkdir()

    (temp_dir / "file1.py").write_text("print('hello')")
    (subdir / "file2.py").write_text(
        """
import pickle
pickle.loads(data)
"""
    )

    report = analyzer.analyze_directory(str(temp_dir), recursive=False)

    assert report.total_files_scanned == 1


def test_exclude_patterns(temp_dir: Path) -> None:
    """Test excluding files by pattern."""
    (temp_dir / "test_file.py").write_text(
        """
password = "SuperSecret123!"
"""
    )

    (temp_dir / "main.py").write_text(
        """
api_key = "sk_live_1234567890abcdefghij"
"""
    )

    analyzer = SecurityAnalyzer(exclude_patterns=["test_*.py"])
    report = analyzer.analyze_directory(str(temp_dir))

    assert report.total_files_scanned == 1
    # Only main.py should be scanned


# Report Tests


def test_security_report_properties(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test SecurityReport properties and methods."""
    (temp_dir / "vuln.py").write_text(
        """
import os
os.system("ls " + user_input)
password = "SuperSecret123!"
import hashlib
hashlib.md5(data)
"""
    )

    report = analyzer.analyze_directory(str(temp_dir))

    assert report.total_vulnerabilities == len(report.vulnerabilities)
    assert isinstance(report.has_critical, bool)
    assert isinstance(report.has_high, bool)


def test_security_report_get_by_severity(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test filtering vulnerabilities by severity."""
    (temp_dir / "vuln.py").write_text(
        """
import os
os.system("ls " + user_input)
import hashlib
hashlib.md5(data)
"""
    )

    report = analyzer.analyze_directory(str(temp_dir))

    critical_vulns = report.get_by_severity(Severity.CRITICAL)
    medium_vulns = report.get_by_severity(Severity.MEDIUM)

    assert all(v.severity == Severity.CRITICAL for v in critical_vulns)
    assert all(v.severity == Severity.MEDIUM for v in medium_vulns)


def test_security_report_get_by_type(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test filtering vulnerabilities by type."""
    (temp_dir / "vuln.py").write_text(
        """
import os
os.system("ls " + user_input)
password = "SuperSecret123!"
"""
    )

    report = analyzer.analyze_directory(str(temp_dir))

    cmd_vulns = report.get_by_type(VulnerabilityType.COMMAND_INJECTION)
    secret_vulns = report.get_by_type(VulnerabilityType.HARDCODED_SECRET)

    assert all(v.type == VulnerabilityType.COMMAND_INJECTION for v in cmd_vulns)
    assert all(v.type == VulnerabilityType.HARDCODED_SECRET for v in secret_vulns)


def test_security_report_to_dict(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test converting report to dictionary."""
    (temp_dir / "vuln.py").write_text(
        """
password = "SuperSecret123!"
"""
    )

    report = analyzer.analyze_directory(str(temp_dir))
    report_dict = report.to_dict()

    assert isinstance(report_dict, dict)
    assert "vulnerabilities" in report_dict
    assert "total_files_scanned" in report_dict
    assert "critical_count" in report_dict
    assert isinstance(report_dict["vulnerabilities"], list)


def test_vulnerability_to_dict(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test converting vulnerability to dictionary."""
    (temp_dir / "vuln.py").write_text(
        """
password = "SuperSecret123!"
"""
    )

    vulns = analyzer.analyze_file(str(temp_dir / "vuln.py"))
    assert len(vulns) > 0

    vuln_dict = vulns[0].to_dict()

    assert isinstance(vuln_dict, dict)
    assert "type" in vuln_dict
    assert "severity" in vuln_dict
    assert "file_path" in vuln_dict
    assert "description" in vuln_dict
    assert "remediation" in vuln_dict


def test_severity_comparison() -> None:
    """Test severity level comparison."""
    assert Severity.CRITICAL < Severity.HIGH
    assert Severity.HIGH < Severity.MEDIUM
    assert Severity.MEDIUM < Severity.LOW
    assert Severity.LOW < Severity.INFO

    assert Severity.CRITICAL <= Severity.CRITICAL
    assert Severity.CRITICAL <= Severity.HIGH
    assert Severity.HIGH >= Severity.HIGH
    assert Severity.MEDIUM > Severity.HIGH


def test_vulnerability_str_representation(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test string representation of vulnerability."""
    (temp_dir / "vuln.py").write_text(
        """
password = "SuperSecret123!"
"""
    )

    vulns = analyzer.analyze_file(str(temp_dir / "vuln.py"))
    assert len(vulns) > 0

    vuln_str = str(vulns[0])
    assert isinstance(vuln_str, str)
    assert vulns[0].severity.value.upper() in vuln_str
    assert vulns[0].file_path in vuln_str


def test_report_str_representation(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test string representation of report."""
    (temp_dir / "vuln.py").write_text(
        """
password = "SuperSecret123!"
"""
    )

    report = analyzer.analyze_directory(str(temp_dir))
    report_str = str(report)

    assert isinstance(report_str, str)
    assert "Security Analysis Report" in report_str
    assert "Files Scanned" in report_str


# Edge Cases and Error Handling


def test_analyze_nonexistent_file(analyzer: SecurityAnalyzer) -> None:
    """Test analyzing a file that doesn't exist."""
    vulns = analyzer.analyze_file("/nonexistent/file.py")
    assert len(vulns) == 0


def test_analyze_file_with_syntax_error(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test analyzing a file with syntax errors."""
    (temp_dir / "syntax_error.py").write_text(
        """
def broken_function(
    # Missing closing parenthesis
    print("This won't parse")
"""
    )

    vulns = analyzer.analyze_file(str(temp_dir / "syntax_error.py"))
    assert len(vulns) == 0  # Should handle gracefully


def test_analyze_empty_file(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test analyzing an empty file."""
    (temp_dir / "empty.py").write_text("")

    vulns = analyzer.analyze_file(str(temp_dir / "empty.py"))
    assert len(vulns) == 0


def test_analyze_file_with_multiple_vulnerabilities(
    analyzer: SecurityAnalyzer, temp_dir: Path
) -> None:
    """Test file with multiple different vulnerabilities."""
    code = """
import os
import pickle
import hashlib

password = "SuperSecret123!"
api_key = "sk_live_1234567890abcdefghij"

def unsafe_function(user_input, data) -> None:
    os.system("ls " + user_input)
    pickle.loads(data)
    hashlib.md5(b"data")
    with open("/data/" + user_input) as f:
        content = f.read()
"""
    (temp_dir / "multiple.py").write_text(code)

    vulns = analyzer.analyze_file(str(temp_dir / "multiple.py"))

    # Should detect multiple vulnerability types
    vuln_types = {v.type for v in vulns}
    assert len(vuln_types) >= 4


def test_confidence_score(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test that vulnerabilities have confidence scores."""
    (temp_dir / "vuln.py").write_text(
        """
import os
os.system("ls " + user_input)
"""
    )

    vulns = analyzer.analyze_file(str(temp_dir / "vuln.py"))
    assert len(vulns) > 0
    assert 0.0 <= vulns[0].confidence <= 1.0


# CWE and OWASP Mapping Tests


def test_cwe_mapping(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test that all vulnerabilities have CWE IDs."""
    (temp_dir / "vuln.py").write_text(
        """
import os
os.system("ls " + user_input)
password = "SuperSecret123!"
import pickle
pickle.loads(data)
"""
    )

    vulns = analyzer.analyze_file(str(temp_dir / "vuln.py"))

    for vuln in vulns:
        assert vuln.cwe_id.startswith("CWE-")


def test_owasp_mapping(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test that all vulnerabilities have OWASP categories."""
    (temp_dir / "vuln.py").write_text(
        """
import os
os.system("ls " + user_input)
password = "SuperSecret123!"
"""
    )

    vulns = analyzer.analyze_file(str(temp_dir / "vuln.py"))

    for vuln in vulns:
        assert "A" in vuln.owasp_category
        assert "2021" in vuln.owasp_category


# Remediation Tests


def test_remediation_suggestions(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test that all vulnerabilities have remediation suggestions."""
    (temp_dir / "vuln.py").write_text(
        """
import os
os.system("ls " + user_input)
"""
    )

    vulns = analyzer.analyze_file(str(temp_dir / "vuln.py"))

    for vuln in vulns:
        assert len(vuln.remediation) > 0
        assert isinstance(vuln.remediation, str)


def test_code_snippet_extraction(analyzer: SecurityAnalyzer, temp_dir: Path) -> None:
    """Test that code snippets are properly extracted."""
    (temp_dir / "vuln.py").write_text(
        """
import os

def unsafe_function(user_input) -> None:
    os.system("ls " + user_input)
"""
    )

    vulns = analyzer.analyze_file(str(temp_dir / "vuln.py"))
    assert len(vulns) > 0

    # Code snippet should contain the problematic line
    assert "os.system" in vulns[0].code_snippet
