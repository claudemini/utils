#!/bin/bash

# Content Curation - For scheduled task
# Finds high-quality content to potentially share

cd /Users/claudemini/Claude/Code/utils

echo "Curating high-quality content from timeline..."
uv run python twitter_manager.py curate --hours 48

echo "Content curation complete. Results saved to twitter_curated_content.json"