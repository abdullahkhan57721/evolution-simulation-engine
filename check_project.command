#!/bin/zsh

set -u

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT" || exit 1

clear
printf '%s\n' "Evolution Simulation Engine — Project Check"
printf '%s\n' "==========================================="
printf '\nProject root:\n%s\n\n' "$PROJECT_ROOT"

./scripts/check_all
exit_code=$?

printf '\n===========================================\n'
if [[ $exit_code -eq 0 ]]; then
    printf '%s\n' "PROJECT CHECK PASSED"
else
    printf '%s\n' "PROJECT CHECK FAILED (exit $exit_code)"
fi
printf '%s\n' "==========================================="
printf '\nPress Enter to close this window...'
read -r
exit "$exit_code"
