#!/usr/bin/env zsh
set -eu

# difflex / src/difflex/main.py / assets/app.png
python3 -m nuitka \
  --macos-create-app-bundle \
  --macos-app-icon="assets/app.png" \
  --macos-app-version="0.1.0" \
  --output-filename="difflex" \
  "src/difflex/main.py"
