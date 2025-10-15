#!/bin/bash

set -eu # deliberately no `-x` or `-v`
set -o pipefail

# Import common.bashrc and change to git repository directory
# shellcheck source-path=SCRIPTDIR  # to help shellcheck to find common.bashrc
source "$(dirname -- "${BASH_SOURCE[0]}")/common.bashrc"
cd "${REPO_DIR}"

# pytest-xdist will force pytest stdout/stderr capture (aka. disables -s/--capture=no),
# which is inconvenient for local development.
# We disable pytest-xdist by default, and only use it in CICD pipeline.
#
# Also, before running, we ensure .coverage file does not exist
rm -f ./.coverage

TEST_SCOPE="${1:-memorylake}"

PYTEST_ARGS=()
if python3 -c "import xdist" >/dev/null 2>&1; then
    PYTEST_ARGS+=(-n logical)
else
    echo "pytest-xdist not available; running tests in a single process." >&2
fi

if python3 -c "import pytest_cov" >/dev/null 2>&1; then
    PYTEST_ARGS+=(--cov=. --cov-append --cov-report="")
else
    echo "pytest-cov not available; coverage reporting disabled." >&2
fi

FALLBACK_CONFIG=""
if ! python3 -c "import pytest_asyncio" >/dev/null 2>&1; then
    echo "pytest-asyncio not available; using fallback pytest configuration." >&2
    FALLBACK_CONFIG="$(mktemp)"
    cat <<'EOF' >"${FALLBACK_CONFIG}"
[pytest]
pythonpath = .
testpaths = memorylake
python_files = test_*.py
asyncio_mode = auto
log_cli_level = INFO
verbosity_assertions = 2
verbosity_test_cases = 2
addopts =
    -s
    --strict-config
env_files =
    cicd/ci-test.env
filterwarnings =
    error
EOF
    PYTEST_ARGS+=(-c "${FALLBACK_CONFIG}")
    cleanup() {
        if [ -n "${FALLBACK_CONFIG}" ] && [ -f "${FALLBACK_CONFIG}" ]; then
            rm -f "${FALLBACK_CONFIG}"
        fi
    }
    trap cleanup EXIT
fi

if [ "${#PYTEST_ARGS[@]}" -gt 0 ]; then
    python3 -m pytest "${PYTEST_ARGS[@]}" "${TEST_SCOPE}"
else
    python3 -m pytest "${TEST_SCOPE}"
fi

# Generate coverage.xml, and print to console too
if command -v coverage >/dev/null 2>&1; then
    coverage xml -o coverage.xml
    coverage report
else
    echo "'coverage' command not found; skipping coverage report generation." >&2
fi
