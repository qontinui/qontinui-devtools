#!/bin/bash
# Installation script for qontinui-devtools in CI/CD environments
# This script ensures proper installation and verification

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running in CI environment
is_ci() {
    [ -n "${CI:-}" ] || [ -n "${GITHUB_ACTIONS:-}" ] || [ -n "${GITLAB_CI:-}" ] || [ -n "${JENKINS_URL:-}" ]
}

# Detect CI platform
detect_ci_platform() {
    if [ -n "${GITHUB_ACTIONS:-}" ]; then
        echo "GitHub Actions"
    elif [ -n "${GITLAB_CI:-}" ]; then
        echo "GitLab CI"
    elif [ -n "${JENKINS_URL:-}" ]; then
        echo "Jenkins"
    elif [ -n "${CIRCLECI:-}" ]; then
        echo "CircleCI"
    elif [ -n "${TRAVIS:-}" ]; then
        echo "Travis CI"
    elif [ -n "${AZURE_HTTP_USER_AGENT:-}" ]; then
        echo "Azure Pipelines"
    else
        echo "Unknown"
    fi
}

# Main installation
main() {
    log_info "Installing qontinui-devtools for CI/CD..."
    echo ""

    # Detect environment
    if is_ci; then
        CI_PLATFORM=$(detect_ci_platform)
        log_info "Detected CI platform: $CI_PLATFORM"
    else
        log_warning "Not running in a CI environment"
    fi

    # Check Python version
    log_info "Checking Python version..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_info "Python version: $PYTHON_VERSION"

        # Check if version is 3.8 or higher
        PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
        PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)

        if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
            log_error "Python 3.8 or higher is required (found $PYTHON_VERSION)"
            exit 1
        fi
    else
        log_error "Python 3 is not installed"
        exit 1
    fi

    # Upgrade pip
    log_info "Upgrading pip..."
    python3 -m pip install --upgrade pip

    # Install qontinui-devtools
    log_info "Installing qontinui-devtools..."

    # Check if we should install from source or PyPI
    if [ -f "pyproject.toml" ] && [ -d "python/qontinui_devtools" ]; then
        log_info "Installing from source (development mode)..."
        python3 -m pip install -e .
    else
        log_info "Installing from PyPI..."
        python3 -m pip install qontinui-devtools
    fi

    # Verify installation
    log_info "Verifying installation..."
    if command -v qontinui-devtools &> /dev/null; then
        VERSION=$(qontinui-devtools --version 2>&1 | head -n1)
        log_success "qontinui-devtools installed successfully"
        log_info "Version: $VERSION"
    else
        log_error "Installation verification failed"
        exit 1
    fi

    # Install optional dependencies for specific checks
    log_info "Installing optional dependencies..."

    # Radon for complexity analysis
    if ! python3 -c "import radon" &> /dev/null; then
        log_info "Installing radon for complexity analysis..."
        python3 -m pip install radon
    fi

    # Create output directory
    OUTPUT_DIR="${QONTINUI_OUTPUT_DIR:-analysis-results}"
    if [ ! -d "$OUTPUT_DIR" ]; then
        log_info "Creating output directory: $OUTPUT_DIR"
        mkdir -p "$OUTPUT_DIR"
    fi

    # Summary
    echo ""
    log_success "Installation complete!"
    echo ""
    log_info "Available commands:"
    echo "  - qontinui-devtools import-cmd check"
    echo "  - qontinui-devtools architecture god-classes"
    echo "  - qontinui-devtools concurrency check"
    echo "  - qontinui-devtools analyze"
    echo ""
    log_info "CI Integration:"
    echo "  - python -m qontinui_devtools.ci.quality_gates"
    echo "  - python -m qontinui_devtools.ci.pr_comment"
    echo ""

    # Platform-specific tips
    case "$CI_PLATFORM" in
        "GitHub Actions")
            log_info "GitHub Actions detected. Use the workflow at .github/workflows/code-quality.yml"
            ;;
        "GitLab CI")
            log_info "GitLab CI detected. See .gitlab-ci-example.yml for configuration"
            ;;
        *)
            log_info "For CI integration examples, see docs/ci-integration.md"
            ;;
    esac
}

# Run main function
main "$@"
