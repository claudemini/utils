#!/usr/bin/env python3
"""Delete a tweet by ID"""

import os
import sys
import tweepy
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path.home() / "Claude" / ".env"
load_dotenv(env_path)

def delete_tweet(tweet_id):
    """Delete a tweet by ID"""
    # Create Twitter client
    client = tweepy.Client(
        consumer_key=os.getenv('TWITTER_API_KEY'),
        consumer_secret=os.getenv('TWITTER_API_SECRET_KEY'),
        access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
        access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
        wait_on_rate_limit=True
    )
    
    try:
        # Delete the tweet
        response = client.delete_tweet(tweet_id)
        if response.data:
            print(f"Tweet {tweet_id} deleted successfully")
            return True
        else:
            print(f"Failed to delete tweet {tweet_id}")
            return False
    except Exception as e:
        print(f"Error deleting tweet: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python twitter_delete.py <tweet_id>")
        sys.exit(1)
    
    tweet_id = sys.argv[1]
    delete_tweet(tweet_id)