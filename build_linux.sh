#!/usr/bin/env bash
set -euo pipefail

# difflex / src/difflex/main.py / assets/app.png
python3 -m nuitka \
  --onefile \
  --linux-onefile-icon="assets/app.png" \
  --output-filename="difflex" \
  "src/difflex/main.py"
