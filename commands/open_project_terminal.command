#!/bin/zsh

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

cd "$PROJECT_ROOT"

# Deactivate Conda if one was automatically activated.
if [[ -n "${CONDA_PREFIX:-}" ]] && command -v conda >/dev/null 2>&1; then
    conda deactivate 2>/dev/null || true
fi

# Prefer .venv if both exist, otherwise use venv.
if [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
elif [[ -f "$PROJECT_ROOT/venv/bin/activate" ]]; then
    source "$PROJECT_ROOT/venv/bin/activate"
else
    echo
    echo "WARNING: No virtual environment was found."
    echo "Expected either:"
    echo "  $PROJECT_ROOT/.venv"
    echo "or:"
    echo "  $PROJECT_ROOT/venv"
    echo
fi

clear

echo "Evolution Simulation Engine"
echo "==========================="
echo
echo "Project root:"
echo "$PROJECT_ROOT"
echo

if command -v python >/dev/null 2>&1; then
    echo "Python:"
    command -v python
    python --version
else
    echo "Python environment is not active."
fi

echo
echo "Ready."
echo

exec zsh -i
