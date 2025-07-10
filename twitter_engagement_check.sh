#!/bin/bash

# Twitter Engagement Check - For scheduled task
# Checks mentions and prepares engagement opportunities

cd /Users/claudemini/Claude/Code/utils

echo "Checking Twitter mentions and engagement opportunities..."
uv run python twitter_manager.py mentions --hours 6

# Process high-priority mentions with Claude
if [ -f twitter_mentions_analysis.json ]; then
    echo "Analyzing mentions for responses..."
    # This will be processed by a Claude task
    echo "Mentions analysis saved. Ready for Claude to generate responses."
fi