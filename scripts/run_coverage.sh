#!/usr/bin/env bash
# Standard coverage workflow for Thordata SDK (reliable across envs).
# Usage: from repo root, run:  bash scripts/run_coverage.sh
# Or:    python -m coverage run -m pytest -p no:cov -v tests && python -m coverage report -m

set -e
cd "$(dirname "$0")/.."
python -m coverage run -m pytest -p no:cov -v tests
python -m coverage report -m
