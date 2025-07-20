#!/usr/bin/env python3
"""Reply to a specific tweet"""

import os
import sys
import tweepy
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path.home() / "Claude" / ".env"
load_dotenv(env_path)

def reply_to_tweet(tweet_id, message):
    """Reply to a specific tweet"""
    # Create Twitter client
    client = tweepy.Client(
        consumer_key=os.getenv('TWITTER_API_KEY'),
        consumer_secret=os.getenv('TWITTER_API_SECRET_KEY'),
        access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
        access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
        wait_on_rate_limit=True
    )
    
    try:
        # Post the reply
        response = client.create_tweet(
            text=message,
            in_reply_to_tweet_id=tweet_id
        )
        
        if response.data:
            tweet_id = response.data['id']
            print(f"Reply posted successfully! ID: {tweet_id}")
            print(f"View at: https://twitter.com/ClaudeMini/status/{tweet_id}")
            return True
        else:
            print("Failed to post reply")
            return False
    except Exception as e:
        print(f"Error posting reply: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python twitter_reply.py <tweet_id> <message>")
        print("   or: echo <message> | python twitter_reply.py <tweet_id> -")
        sys.exit(1)
    
    tweet_id = sys.argv[1]
    
    # Handle stdin input
    if len(sys.argv) == 3 and sys.argv[2] == "-":
        message = sys.stdin.read().strip()
    else:
        message = " ".join(sys.argv[2:])
    
    reply_to_tweet(tweet_id, message)