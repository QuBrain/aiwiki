#!/bin/sh
set -e

if [ -n "$AIWIKI_RUN_AGENT_LOOP" ]; then
    exec python run_agent_loop.py
else
    exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
fi
