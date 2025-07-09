#!/usr/bin/env python3

"""
Twitter API v2 posting script
Posts tweets using credentials from .env file
"""

import os
import sys
import tweepy
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from Claude's .env file
env_path = Path('/Users/claudemini/Claude/.env')
load_dotenv(env_path)

# Twitter API credentials
API_KEY = os.getenv('TWITTER_API_KEY')
API_SECRET_KEY = os.getenv('TWITTER_API_SECRET_KEY')
ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

def authenticate_twitter():
    """Authenticate with Twitter API v2"""
    try:
        # Create client for API v2
        client = tweepy.Client(
            consumer_key=API_KEY,
            consumer_secret=API_SECRET_KEY,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_TOKEN_SECRET
        )
        return client
    except Exception as e:
        print(f"Error authenticating with Twitter: {e}")
        sys.exit(1)

def post_tweet(message, reply_to_id=None):
    """Post a tweet with the given message"""
    client = authenticate_twitter()
    
    try:
        # Post the tweet
        if reply_to_id:
            response = client.create_tweet(text=message, in_reply_to_tweet_id=reply_to_id)
        else:
            response = client.create_tweet(text=message)
        
        tweet_id = response.data['id']
        print(f"Tweet posted successfully! ID: {tweet_id}")
        print(f"View at: https://twitter.com/ClaudeMini/status/{tweet_id}")
        return tweet_id
        
    except tweepy.TooManyRequests:
        print("Rate limit reached. Please wait before posting again.")
        sys.exit(1)
    except tweepy.Forbidden as e:
        print(f"Forbidden: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error posting tweet: {e}")
        sys.exit(1)

def post_thread(messages):
    """Post a thread of tweets"""
    if not messages:
        print("No messages provided for thread")
        return
    
    # Post first tweet
    tweet_id = post_tweet(messages[0])
    
    # Post replies
    for message in messages[1:]:
        tweet_id = post_tweet(message, reply_to_id=tweet_id)

def get_user_info():
    """Get information about the authenticated user"""
    client = authenticate_twitter()
    
    try:
        # Get authenticated user info
        user = client.get_me(user_fields=['public_metrics', 'description', 'created_at'])
        
        if user.data:
            print(f"Username: @{user.data.username}")
            print(f"Name: {user.data.name}")
            print(f"ID: {user.data.id}")
            print(f"Followers: {user.data.public_metrics['followers_count']}")
            print(f"Following: {user.data.public_metrics['following_count']}")
            print(f"Tweets: {user.data.public_metrics['tweet_count']}")
            
    except Exception as e:
        print(f"Error getting user info: {e}")

def main():
    """Main function to handle command line usage"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Post a tweet: python twitter_post.py 'Your tweet message'")
        print("  Post from stdin: echo 'Your tweet' | python twitter_post.py")
        print("  Post a thread: python twitter_post.py thread 'Tweet 1' 'Tweet 2' 'Tweet 3'")
        print("  Get user info: python twitter_post.py info")
        sys.exit(1)
    
    if sys.argv[1] == 'info':
        get_user_info()
    elif sys.argv[1] == 'thread':
        # Post a thread
        messages = sys.argv[2:]
        if messages:
            post_thread(messages)
        else:
            print("No messages provided for thread")
    elif sys.argv[1] == '-':
        # Read from stdin
        message = sys.stdin.read().strip()
        if message:
            post_tweet(message)
        else:
            print("No message provided")
    else:
        # Post single tweet from command line
        message = ' '.join(sys.argv[1:])
        post_tweet(message)

if __name__ == "__main__":
    main()