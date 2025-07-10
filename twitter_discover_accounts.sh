#!/bin/bash

# Account Discovery - For scheduled task
# Discovers relevant accounts to follow

cd /Users/claudemini/Claude/Code/utils

echo "Discovering relevant Twitter accounts..."
uv run python twitter_manager.py discover --topics AI automation coding "machine learning" technology innovation

echo "Account discovery complete. Results saved to twitter_discovered_accounts.json"