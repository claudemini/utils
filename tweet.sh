#!/bin/bash

# Simple wrapper for tweeting
# Usage: ./tweet.sh "Your message"
#    or: echo "Your message" | ./tweet.sh

UTILS_DIR="$(dirname "$0")"
cd "$UTILS_DIR"

# If no arguments, read from stdin
if [ $# -eq 0 ]; then
    /Users/claudemini/.local/bin/uv run python twitter_post.py -
else
    /Users/claudemini/.local/bin/uv run python twitter_post.py "$@"
fi