#!/usr/bin/env bash
set -euo pipefail

curl -X POST "http://localhost:8000/api/process-image" \
  -F "image=@assets/sample_images/sample.jpg" \
  -F "stages=quality,background,rebuild,vision,metadata"
