#!/bin/zsh

set -e

PROJECT_ROOT="${0:A:h}"
PROJECT_NAME="${PROJECT_ROOT:t}"
OUTPUT_DIR="$HOME/Downloads"
OUTPUT_FILE="$OUTPUT_DIR/${PROJECT_NAME}-review.zip"

mkdir -p "$OUTPUT_DIR"
rm -f "$OUTPUT_FILE"

cd "$PROJECT_ROOT"

zip -r -q "$OUTPUT_FILE" . \
    -x '.git/*' \
       '.venv/*' \
       'venv/*' \
       '__pycache__/*' \
       '*/__pycache__/*' \
       '.DS_Store' \
       '*/.DS_Store' \
       '.pytest_cache/*' \
       '.ruff_cache/*' \
       '.mypy_cache/*' \
       'site/*' \
       'outputs/*' \
       'scratch/*' \
       'archived/*' \
       '*.egg-info/*' \
       'src/*.egg-info/*' \
       '*.sublime-workspace' \
       '*.pyc'

printf '\nCreated review ZIP:\n%s\n\n' "$OUTPUT_FILE"

open -R "$OUTPUT_FILE"
