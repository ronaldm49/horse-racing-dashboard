#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python requirements
pip install -r requirements.txt

# Install Playwright and its necessary browser dependencies (Chromium only to save space)
playwright install --with-deps chromium
