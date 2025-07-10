#!/usr/bin/env python3

"""
Twitter API v2 mentions and interactions fetcher
Retrieves recent mentions and interactions for analysis
"""

import os
import tweepy
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import json

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
        # Try bearer token first (if available)
        bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        
        if bearer_token:
            # Use bearer token for read operations
            client = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=API_KEY,
                consumer_secret=API_SECRET_KEY,
                access_token=ACCESS_TOKEN,
                access_token_secret=ACCESS_TOKEN_SECRET,
                wait_on_rate_limit=True
            )
        else:
            # Fall back to OAuth 1.0a
            client = tweepy.Client(
                consumer_key=API_KEY,
                consumer_secret=API_SECRET_KEY,
                access_token=ACCESS_TOKEN,
                access_token_secret=ACCESS_TOKEN_SECRET,
                wait_on_rate_limit=True
            )
        return client
    except Exception as e:
        print(f"Error authenticating with Twitter: {e}")
        return None

def get_mentions(client, hours=24):
    """Get recent mentions within specified hours"""
    try:
        # Get authenticated user ID
        me = client.get_me()
        if not me.data:
            print("Could not get user information")
            return []
        
        user_id = me.data.id
        
        # Calculate time range
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Get mentions
        mentions = client.get_users_mentions(
            id=user_id,
            start_time=start_time.isoformat() + "Z",
            tweet_fields=['created_at', 'author_id', 'conversation_id', 'in_reply_to_user_id', 'referenced_tweets'],
            user_fields=['username', 'name', 'verified', 'public_metrics'],
            expansions=['author_id', 'referenced_tweets.id']
        )
        
        return mentions
    except Exception as e:
        print(f"Error getting mentions: {e}")
        return None

def get_user_tweets(client, hours=24):
    """Get user's recent tweets to check for interactions"""
    try:
        # Get authenticated user ID
        me = client.get_me()
        if not me.data:
            print("Could not get user information")
            return []
        
        user_id = me.data.id
        
        # Calculate time range
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Get user's tweets
        tweets = client.get_users_tweets(
            id=user_id,
            start_time=start_time.isoformat() + "Z",
            tweet_fields=['created_at', 'public_metrics', 'conversation_id'],
            max_results=20
        )
        
        return tweets
    except Exception as e:
        print(f"Error getting user tweets: {e}")
        return None

def analyze_interactions(client, hours=24):
    """Analyze recent mentions and interactions"""
    mentions = get_mentions(client, hours)
    user_tweets = get_user_tweets(client, hours)
    
    interactions = []
    
    # Process mentions
    if mentions and mentions.data:
        for mention in mentions.data:
            interaction = {
                'type': 'mention',
                'id': mention.id,
                'text': mention.text,
                'author_id': mention.author_id,
                'created_at': mention.created_at,
                'url': f"https://twitter.com/i/web/status/{mention.id}"
            }
            
            # Get author info if available
            if hasattr(mentions, 'includes') and 'users' in mentions.includes:
                for user in mentions.includes['users']:
                    if user.id == mention.author_id:
                        interaction['author_username'] = user.username
                        interaction['author_name'] = user.name
                        interaction['author_followers'] = user.public_metrics.get('followers_count', 0)
                        break
            
            interactions.append(interaction)
    
    # Check engagement on user's tweets
    if user_tweets and user_tweets.data:
        for tweet in user_tweets.data:
            if hasattr(tweet, 'public_metrics'):
                metrics = tweet.public_metrics
                if metrics.get('reply_count', 0) > 0 or metrics.get('like_count', 0) > 5:
                    interaction = {
                        'type': 'engagement',
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': tweet.created_at,
                        'replies': metrics.get('reply_count', 0),
                        'likes': metrics.get('like_count', 0),
                        'retweets': metrics.get('retweet_count', 0),
                        'url': f"https://twitter.com/ClaudeMini/status/{tweet.id}"
                    }
                    interactions.append(interaction)
    
    return interactions

def save_interactions(interactions):
    """Save interactions to a JSON file"""
    output_path = '/Users/claudemini/Claude/Code/utils/twitter_interactions.json'
    with open(output_path, 'w') as f:
        json.dump(interactions, f, indent=2, default=str)
    print(f"Saved {len(interactions)} interactions to {output_path}")

def main():
    """Main function"""
    client = authenticate_twitter()
    if not client:
        return
    
    print("Fetching recent Twitter interactions...")
    interactions = analyze_interactions(client, hours=48)
    
    if interactions:
        print(f"\nFound {len(interactions)} interactions:")
        for i, interaction in enumerate(interactions):
            print(f"\n{i+1}. {interaction['type'].upper()}")
            print(f"   Created: {interaction['created_at']}")
            if 'author_username' in interaction:
                print(f"   From: @{interaction['author_username']} ({interaction['author_followers']} followers)")
            print(f"   Text: {interaction['text'][:100]}...")
            print(f"   URL: {interaction['url']}")
            if interaction['type'] == 'engagement':
                print(f"   Engagement: {interaction['replies']} replies, {interaction['likes']} likes, {interaction['retweets']} RTs")
        
        save_interactions(interactions)
    else:
        print("No interactions found in the specified time period.")

if __name__ == "__main__":
    main()