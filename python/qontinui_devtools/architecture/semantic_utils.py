"""Semantic utilities for method name analysis and classification.

This module provides utilities for analyzing method names, extracting keywords,
and classifying methods into responsibility categories based on common patterns.
"""

import re
from typing import Optional

# Common method prefixes mapped to responsibilities
RESPONSIBILITY_PATTERNS: dict[str, list[str]] = {
    "Data Access": [
        "get",
        "set",
        "fetch",
        "retrieve",
        "find",
        "query",
        "search",
        "select",
        "lookup",
    ],
    "Validation": ["validate", "check", "verify", "assert", "ensure", "confirm", "test"],
    "Business Logic": ["calculate", "compute", "process", "execute", "run", "perform", "apply"],
    "Persistence": [
        "save",
        "load",
        "persist",
        "store",
        "restore",
        "read",
        "write",
        "update",
        "delete",
    ],
    "Presentation": ["render", "display", "show", "format", "print", "draw", "paint"],
    "Event Handling": ["handle", "on", "trigger", "emit", "listen", "subscribe", "publish"],
    "Lifecycle": [
        "init",
        "initialize",
        "setup",
        "start",
        "stop",
        "cleanup",
        "destroy",
        "dispose",
        "close",
    ],
    "Factory": ["create", "build", "make", "construct", "new", "instantiate"],
    "Conversion": ["to", "from", "convert", "transform", "parse", "serialize", "deserialize"],
    "Comparison": ["compare", "equals", "matches", "is", "has"],
}

# Common stop words to ignore
STOP_WORDS: set[str] = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "as",
    "into",
    "like",
    "through",
    "after",
    "over",
    "between",
    "out",
    "against",
    "during",
    "without",
    "before",
    "under",
    "around",
    "among",
}


def tokenize_method_name(name: str) -> list[str]:
    """Split method name into tokens.

    Handles both snake_case and camelCase method names, splitting them
    into individual word tokens.

    Args:
        name: Method name to tokenize

    Returns:
        List of lowercase tokens

    Examples:
        >>> tokenize_method_name("get_user_data")
        ['get', 'user', 'data']
        >>> tokenize_method_name("calculateTotal")
        ['calculate', 'total']
        >>> tokenize_method_name("handleHTTPRequest")
        ['handle', 'http', 'request']
    """
    if not name:
        return []

    # Remove leading/trailing underscores (dunder methods handled separately)
    name = name.strip("_")

    # Handle snake_case: split on underscores
    if "_" in name:
        tokens = name.split("_")
    else:
        # Handle camelCase: insert spaces before capital letters
        # Convert HTTPRequest -> HTTP Request
        name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", name)
        # Convert camelCase -> camel Case
        name = re.sub(r"([a-z\d])([A-Z])", r"\1 \2", name)
        tokens = name.split()

    # Lowercase and filter empty strings
    tokens = [t.lower() for t in tokens if t]

    return tokens


def extract_verb(tokens: list[str]) -> Optional[str]:
    """Extract primary verb from tokens.

    Typically the first token is the verb (get, set, calculate, etc).

    Args:
        tokens: List of tokens from method name

    Returns:
        Primary verb or None if not found

    Examples:
        >>> extract_verb(['get', 'user', 'data'])
        'get'
        >>> extract_verb(['calculate', 'total'])
        'calculate'
    """
    if not tokens:
        return None

    # First token is typically the verb
    return tokens[0]


def extract_keywords(method_name: str) -> set[str]:
    """Extract keywords from method name.

    Tokenizes the method name and removes stop words to extract
    meaningful keywords.

    Args:
        method_name: Method name to extract keywords from

    Returns:
        Set of keywords

    Examples:
        >>> extract_keywords("get_user_by_email")
        {'get', 'user', 'email'}
        >>> extract_keywords("calculateUserScore")
        {'calculate', 'user', 'score'}
    """
    tokens = tokenize_method_name(method_name)

    # Remove stop words and return as set
    keywords = {token for token in tokens if token not in STOP_WORDS}

    return keywords


def classify_method(method_name: str) -> str:
    """Classify method into responsibility category.

    Analyzes the method name to determine which responsibility category
    it belongs to based on common patterns.

    Args:
        method_name: Method name to classify

    Returns:
        Responsibility category name (e.g., "Data Access", "Validation")
        Returns "Other" if no clear category is found

    Examples:
        >>> classify_method("get_user_data")
        'Data Access'
        >>> classify_method("validate_email")
        'Validation'
        >>> classify_method("calculate_total")
        'Business Logic'
    """
    tokens = tokenize_method_name(method_name)
    if not tokens:
        return "Other"

    verb = extract_verb(tokens)
    if not verb:
        return "Other"

    # Check each responsibility pattern
    for responsibility, patterns in RESPONSIBILITY_PATTERNS.items():
        for pattern in patterns:
            if verb == pattern or verb.startswith(pattern):
                return responsibility

    return "Other"


def calculate_similarity_score(name1: str, name2: str) -> float:
    """Calculate similarity between two method names (0-1).

    Uses Jaccard similarity on the keyword sets extracted from
    method names.

    Args:
        name1: First method name
        name2: Second method name

    Returns:
        Similarity score between 0 (no similarity) and 1 (identical)

    Examples:
        >>> calculate_similarity_score("get_user", "get_customer")
        0.5  # One common keyword: 'get'
        >>> calculate_similarity_score("save_data", "load_data")
        0.333  # One common keyword: 'data'
    """
    keywords1 = extract_keywords(name1)
    keywords2 = extract_keywords(name2)

    if not keywords1 and not keywords2:
        return 0.0

    if not keywords1 or not keywords2:
        return 0.0

    # Jaccard similarity: intersection / union
    intersection = keywords1 & keywords2
    union = keywords1 | keywords2

    return len(intersection) / len(union) if union else 0.0


def get_method_category(method_name: str) -> str:
    """Get the category of a method based on its verb.

    Similar to classify_method but focuses only on the verb pattern.

    Args:
        method_name: Method name to categorize

    Returns:
        Category name
    """
    return classify_method(method_name)


def calculate_cluster_similarity(methods1: list[str], methods2: list[str]) -> float:
    """Calculate similarity between two groups of methods.

    Compares the keywords used across two method groups to determine
    how similar their responsibilities are.

    Args:
        methods1: First group of method names
        methods2: Second group of method names

    Returns:
        Similarity score between 0 and 1
    """
    if not methods1 or not methods2:
        return 0.0

    # Aggregate all keywords from each group
    keywords1 = set()
    for method in methods1:
        keywords1.update(extract_keywords(method))

    keywords2 = set()
    for method in methods2:
        keywords2.update(extract_keywords(method))

    if not keywords1 or not keywords2:
        return 0.0

    # Jaccard similarity
    intersection = keywords1 & keywords2
    union = keywords1 | keywords2

    return len(intersection) / len(union) if union else 0.0
