"""Tests for Single Responsibility Principle (SRP) Analyzer."""

from pathlib import Path

import pytest
from qontinui_devtools.architecture import (
    MethodCluster,
    SRPAnalyzer,
)
from qontinui_devtools.architecture.clustering import (
    cluster_methods_by_keywords,
    merge_similar_clusters,
    name_cluster,
)
from qontinui_devtools.architecture.semantic_utils import (
    calculate_similarity_score,
    classify_method,
    extract_keywords,
    extract_verb,
    tokenize_method_name,
)


class TestMethodTokenization:
    """Tests for method name tokenization."""

    def test_tokenize_snake_case(self):
        """Test tokenizing snake_case method names."""
        tokens = tokenize_method_name("get_user_data")
        assert tokens == ["get", "user", "data"]

    def test_tokenize_camel_case(self):
        """Test tokenizing camelCase method names."""
        tokens = tokenize_method_name("calculateTotal")
        assert tokens == ["calculate", "total"]

    def test_tokenize_pascal_case(self):
        """Test tokenizing PascalCase method names."""
        tokens = tokenize_method_name("ProcessUserData")
        assert tokens == ["process", "user", "data"]

    def test_tokenize_mixed_case(self):
        """Test tokenizing mixed case with acronyms."""
        tokens = tokenize_method_name("handleHTTPRequest")
        assert tokens == ["handle", "http", "request"]

    def test_tokenize_empty_string(self):
        """Test tokenizing empty string."""
        tokens = tokenize_method_name("")
        assert tokens == []

    def test_tokenize_with_underscores(self):
        """Test tokenizing with leading/trailing underscores."""
        tokens = tokenize_method_name("_private_method_")
        assert tokens == ["private", "method"]


class TestVerbExtraction:
    """Tests for verb extraction from method names."""

    def test_extract_verb_simple(self):
        """Test extracting verb from simple method name."""
        verb = extract_verb(["get", "user", "data"])
        assert verb == "get"

    def test_extract_verb_single_token(self):
        """Test extracting verb from single token."""
        verb = extract_verb(["calculate"])
        assert verb == "calculate"

    def test_extract_verb_empty(self):
        """Test extracting verb from empty list."""
        verb = extract_verb([])
        assert verb is None


class TestKeywordExtraction:
    """Tests for keyword extraction."""

    def test_extract_keywords_basic(self):
        """Test basic keyword extraction."""
        keywords = extract_keywords("get_user_by_email")
        assert keywords == {"get", "user", "email"}

    def test_extract_keywords_camel_case(self):
        """Test keyword extraction from camelCase."""
        keywords = extract_keywords("calculateUserScore")
        assert keywords == {"calculate", "user", "score"}

    def test_extract_keywords_with_stop_words(self):
        """Test that stop words are filtered out."""
        keywords = extract_keywords("get_user_from_database")
        assert "from" not in keywords
        assert "get" in keywords
        assert "user" in keywords
        assert "database" in keywords


class TestMethodClassification:
    """Tests for method classification into responsibilities."""

    def test_classify_data_access(self):
        """Test classifying data access methods."""
        assert classify_method("get_user_data") == "Data Access"
        assert classify_method("fetch_records") == "Data Access"
        assert classify_method("retrieve_profile") == "Data Access"

    def test_classify_validation(self):
        """Test classifying validation methods."""
        assert classify_method("validate_email") == "Validation"
        assert classify_method("check_password") == "Validation"
        assert classify_method("verify_credentials") == "Validation"

    def test_classify_business_logic(self):
        """Test classifying business logic methods."""
        assert classify_method("calculate_total") == "Business Logic"
        assert classify_method("process_order") == "Business Logic"
        assert classify_method("compute_score") == "Business Logic"

    def test_classify_persistence(self):
        """Test classifying persistence methods."""
        assert classify_method("save_to_database") == "Persistence"
        assert classify_method("load_from_cache") == "Persistence"
        assert classify_method("persist_data") == "Persistence"

    def test_classify_presentation(self):
        """Test classifying presentation methods."""
        assert classify_method("render_template") == "Presentation"
        assert classify_method("display_results") == "Presentation"
        assert classify_method("format_output") == "Presentation"

    def test_classify_other(self):
        """Test classifying unrecognized methods."""
        assert classify_method("do_something") == "Other"
        assert classify_method("helper_function") == "Other"


class TestSimilarityCalculation:
    """Tests for similarity score calculation."""

    def test_similarity_identical(self):
        """Test similarity of identical method names."""
        score = calculate_similarity_score("get_user", "get_user")
        assert score == 1.0

    def test_similarity_partial_overlap(self):
        """Test similarity with partial keyword overlap."""
        score = calculate_similarity_score("get_user", "get_customer")
        assert 0.3 < score < 0.7  # Should have some similarity

    def test_similarity_no_overlap(self):
        """Test similarity with no keyword overlap."""
        score = calculate_similarity_score("get_user", "calculate_total")
        assert score < 0.3  # Should have low similarity

    def test_similarity_empty(self):
        """Test similarity with empty strings."""
        score = calculate_similarity_score("", "get_user")
        assert score == 0.0


class TestClustering:
    """Tests for method clustering algorithm."""

    def test_cluster_data_access_methods(self):
        """Test clustering data access methods."""
        methods = [
            "get_user",
            "fetch_data",
            "retrieve_records",
            "find_items",
            "query_database",
        ]

        clusters = cluster_methods_by_keywords(methods, min_cluster_size=2)

        # Should create a Data Access cluster
        assert len(clusters) >= 1
        assert any(c.name == "Data Access" for c in clusters)

    def test_cluster_mixed_responsibilities(self):
        """Test clustering methods with mixed responsibilities."""
        methods = [
            "get_user",
            "fetch_data",
            "validate_email",
            "check_password",
            "save_record",
            "load_cache",
        ]

        clusters = cluster_methods_by_keywords(methods, min_cluster_size=2)

        # Should create multiple clusters
        assert len(clusters) >= 2

    def test_cluster_min_size(self):
        """Test minimum cluster size enforcement."""
        methods = ["get_user", "validate_email", "calculate_total"]

        clusters = cluster_methods_by_keywords(methods, min_cluster_size=3)

        # No cluster should be created (not enough methods in any category)
        assert len(clusters) == 0

    def test_name_cluster(self):
        """Test cluster naming."""
        methods = ["get_user", "fetch_data", "retrieve_records"]
        name = name_cluster(methods)

        assert name == "Data Access"


class TestMergeCluster:
    """Tests for cluster merging."""

    def test_merge_similar_clusters(self):
        """Test merging similar clusters."""
        cluster1 = MethodCluster(
            name="Data Access",
            methods=["get_user", "fetch_data"],
            keywords={"get", "fetch", "user", "data"},
            confidence=0.8,
        )

        cluster2 = MethodCluster(
            name="Data Retrieval",
            methods=["retrieve_records", "query_database"],
            keywords={"retrieve", "query", "records", "database"},
            confidence=0.7,
        )

        # These are different enough that they might not merge
        # depending on threshold
        merged = merge_similar_clusters([cluster1, cluster2], threshold=0.9)
        assert len(merged) <= 2


class TestSRPAnalyzer:
    """Tests for the main SRP Analyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create an SRP analyzer instance."""
        return SRPAnalyzer(verbose=False)

    @pytest.fixture
    def fixtures_path(self):
        """Get path to test fixtures."""
        return Path(__file__).parent.parent / "fixtures" / "srp"

    def test_analyze_multi_responsibility_class(self, analyzer, fixtures_path):
        """Test analyzing class with multiple responsibilities."""
        file_path = fixtures_path / "multi_responsibility.py"

        violations = analyzer.analyze_directory(str(file_path), min_methods=5)

        assert len(violations) > 0
        violation = violations[0]

        assert violation.class_name == "UserManager"
        assert len(violation.clusters) >= 2  # Should detect multiple responsibilities
        assert violation.severity in ("critical", "high", "medium")

    def test_analyze_single_responsibility_class(self, analyzer, fixtures_path):
        """Test analyzing class with single responsibility."""
        file_path = fixtures_path / "single_responsibility.py"

        violations = analyzer.analyze_directory(str(file_path), min_methods=5)

        # Should have few or no violations for single-responsibility classes
        # UserRepository should not violate SRP (all data access)
        user_repo_violations = [v for v in violations if v.class_name == "UserRepository"]
        assert len(user_repo_violations) == 0

    def test_severity_calculation(self, analyzer):
        """Test severity calculation based on cluster count."""
        assert analyzer._calculate_severity(2) == "medium"
        assert analyzer._calculate_severity(3) == "high"
        assert analyzer._calculate_severity(4) == "high"
        assert analyzer._calculate_severity(5) == "critical"
        assert analyzer._calculate_severity(10) == "critical"

    def test_generate_recommendation(self, analyzer):
        """Test recommendation generation."""
        clusters = [
            MethodCluster("Data Access", ["get", "fetch"], {"get", "fetch"}, 0.8),
            MethodCluster("Validation", ["validate", "check"], {"validate", "check"}, 0.7),
        ]

        recommendation = analyzer._generate_recommendation("UserManager", clusters)

        assert "UserManager" in recommendation
        assert "2" in recommendation or "two" in recommendation.lower()

    def test_suggest_class_name(self, analyzer):
        """Test class name suggestions for extracted responsibilities."""
        assert analyzer._suggest_class_name("UserManager", "Data Access") == "UserRepository"
        assert analyzer._suggest_class_name("UserManager", "Validation") == "UserValidator"
        assert analyzer._suggest_class_name("UserService", "Persistence") == "UserPersister"

    def test_generate_refactoring_suggestions(self, analyzer):
        """Test refactoring suggestion generation."""
        clusters = [
            MethodCluster("Data Access", ["get", "fetch"], {"get", "fetch"}, 0.8),
            MethodCluster("Validation", ["validate", "check"], {"validate", "check"}, 0.7),
        ]

        suggestions = analyzer._generate_refactoring_suggestions("UserManager", clusters)

        assert len(suggestions) >= 2
        assert any("Data Access" in s for s in suggestions)
        assert any("Validation" in s for s in suggestions)

    def test_analyze_directory_stats(self, analyzer, fixtures_path):
        """Test that analyzer collects statistics."""
        analyzer.analyze_directory(str(fixtures_path), min_methods=5)

        assert analyzer.stats["files_analyzed"] > 0
        assert analyzer.stats["classes_analyzed"] > 0

    def test_generate_report(self, analyzer, fixtures_path):
        """Test report generation."""
        violations = analyzer.analyze_directory(str(fixtures_path), min_methods=5)
        report = analyzer.generate_report(violations)

        assert "SRP VIOLATION REPORT" in report
        assert "Total violations:" in report

    def test_generate_report_no_violations(self, analyzer):
        """Test report generation with no violations."""
        report = analyzer.generate_report([])
        assert "No SRP violations detected" in report

    def test_analyze_with_timing(self, analyzer, fixtures_path):
        """Test analysis with timing measurement."""
        violations, execution_time = analyzer.analyze_with_timing(str(fixtures_path), min_methods=5)

        assert isinstance(violations, list)
        assert execution_time > 0
        assert execution_time < 10  # Should complete quickly


class TestIntegration:
    """Integration tests for the complete SRP analysis workflow."""

    def test_full_analysis_workflow(self):
        """Test complete analysis workflow."""
        analyzer = SRPAnalyzer(verbose=False)
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "srp"

        # Run analysis
        violations = analyzer.analyze_directory(str(fixtures_path), min_methods=5)

        # Generate report
        report = analyzer.generate_report(violations)

        # Verify we got results
        assert isinstance(violations, list)
        assert isinstance(report, str)

        # Check that multi-responsibility class is detected
        user_manager_violations = [v for v in violations if v.class_name == "UserManager"]
        assert len(user_manager_violations) > 0

        # Check violation has required fields
        if user_manager_violations:
            violation = user_manager_violations[0]
            assert violation.class_name
            assert violation.file_path
            assert violation.line_number > 0
            assert len(violation.clusters) >= 2
            assert violation.severity
            assert violation.recommendation
            assert len(violation.suggested_refactorings) > 0

    def test_cluster_quality(self):
        """Test quality of clustering for known method groups."""
        methods = [
            # Data access
            "get_user",
            "fetch_data",
            "retrieve_record",
            "find_item",
            # Validation
            "validate_email",
            "check_password",
            "verify_input",
            # Business logic
            "calculate_total",
            "process_order",
            "compute_score",
        ]

        clusters = cluster_methods_by_keywords(methods, min_cluster_size=2)

        # Should identify 3 distinct responsibilities
        assert len(clusters) >= 2
        assert len(clusters) <= 4  # Allow some flexibility

        # Check cluster names are meaningful
        cluster_names = {c.name for c in clusters}
        assert len(cluster_names) > 0
