#!/bin/bash
# Twitter posting schedule script
# Run this script to execute scheduled Twitter posts

source /Users/claudemini/.local/bin/env

echo "Twitter Posting Schedule"
echo "======================="
echo "Morning post (9 AM): System status update"
echo "Afternoon post (2 PM): Technical content"
echo "Evening check (6 PM): Mention monitoring"
echo ""

# Check current time
HOUR=$(date +%H)

if [ $HOUR -eq 9 ]; then
    echo "Running morning post..."
    cd /Users/claudemini/Claude/Code/utils
    uv run python twitter_morning_post.py
elif [ $HOUR -eq 14 ]; then
    echo "Running afternoon technical post..."
    # TODO: Add afternoon post script
elif [ $HOUR -eq 18 ]; then
    echo "Checking mentions..."
    cd /Users/claudemini/Claude/Code/utils
    uv run python twitter_search_mentions.py
else
    echo "No scheduled posts at this hour."
fi