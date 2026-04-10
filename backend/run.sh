#!/bin/bash
cd "$(dirname "$0")" || exit 1
uvicorn src.main:app --host 0.0.0.0 --port 8000
