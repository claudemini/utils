#!/usr/bin/env python3

"""
Helper to follow a specific Twitter account
Usage: python twitter_follow_helper.py <username>
"""

import sys
import tweepy
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
env_path = Path('/Users/claudemini/Claude/.env')
load_dotenv(env_path)

def follow_account(username):
    """Follow a specific Twitter account"""
    try:
        client = tweepy.Client(
            consumer_key=os.getenv('TWITTER_API_KEY'),
            consumer_secret=os.getenv('TWITTER_API_SECRET_KEY'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        )
        
        # Note: Following requires write access
        # This is a placeholder - actual following would need:
        # user = client.get_user(username=username)
        # client.follow_user(user.data.id)
        
        print(f"To follow @{username}:")
        print(f"Visit: https://twitter.com/{username}")
        print("Click the 'Follow' button")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python twitter_follow_helper.py <username>")
        sys.exit(1)
    
    follow_account(sys.argv[1])
