#!/usr/bin/env python3
"""
Twitter Account Discovery System for @ClaudeMini
Finds relevant accounts to follow based on interests and keywords
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import tweepy

# Load environment variables
load_dotenv(Path.home() / "Claude" / ".env")

# Twitter API credentials
api_key = os.getenv("TWITTER_API_KEY")
api_secret = os.getenv("TWITTER_API_SECRET_KEY")
access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# Initialize Twitter client
auth = tweepy.OAuthHandler(api_key, api_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

# V2 client for newer endpoints
client = tweepy.Client(
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
    wait_on_rate_limit=True
)

# Interest keywords
INTEREST_KEYWORDS = [
    "AI", "artificial intelligence", "machine learning", "LLM",
    "Claude", "Anthropic", "AI safety", "AI ethics",
    "Python", "TypeScript", "coding", "programming",
    "automation", "Mac automation", "system monitoring",
    "PostgreSQL", "database", "vector embeddings",
    "building in public", "indie hacker", "developer",
    "AI assistant", "autonomous AI", "AI agents"
]

# Accounts to definitely follow
SUGGESTED_ACCOUNTS = [
    "anthropicai", "goodside", "emollick", "sama", "ylecun",
    "karpathy", "DrJimFan", "svpino", "levelsio", "swyx",
    "simonw", "patio11", "pieterlevels", "marckohlbrugge"
]

def search_users_by_keyword(keyword, max_results=10):
    """Search for users based on a keyword"""
    try:
        users = []
        # Use v1.1 API for user search
        search_results = api.search_users(q=keyword, count=max_results)
        
        for user in search_results:
            user_data = {
                "username": user.screen_name,
                "name": user.name,
                "description": user.description,
                "followers": user.followers_count,
                "verified": user.verified,
                "following": user.following,
                "id": user.id_str
            }
            users.append(user_data)
        
        return users
    except Exception as e:
        print(f"Error searching for '{keyword}': {e}")
        return []

def search_tweets_get_authors(query, max_results=20):
    """Search tweets and extract unique authors"""
    try:
        authors = {}
        
        # Search recent tweets
        tweets = client.search_recent_tweets(
            query=f"{query} -is:retweet lang:en",
            max_results=max_results,
            tweet_fields=["author_id", "created_at"],
            user_fields=["username", "name", "description", "public_metrics"],
            expansions=["author_id"]
        )
        
        if tweets.data and tweets.includes and "users" in tweets.includes:
            for user in tweets.includes["users"]:
                if user.id not in authors:
                    authors[user.id] = {
                        "username": user.username,
                        "name": user.name,
                        "description": user.description,
                        "followers": user.public_metrics["followers_count"],
                        "tweet_count": user.public_metrics["tweet_count"],
                        "id": user.id
                    }
        
        return list(authors.values())
    except Exception as e:
        print(f"Error searching tweets for '{query}': {e}")
        return []

def score_account(account):
    """Score an account based on relevance criteria"""
    score = 0
    
    # Check description for keywords
    description = (account.get("description") or "").lower()
    for keyword in INTEREST_KEYWORDS:
        if keyword.lower() in description:
            score += 2
    
    # Follower count (prefer mid-range, not just celebrities)
    followers = account.get("followers", 0)
    if 1000 < followers < 100000:
        score += 3
    elif 100 < followers < 1000:
        score += 2
    elif followers > 100000:
        score += 1
    
    # Tweet activity
    if account.get("tweet_count", 0) > 1000:
        score += 1
    
    # Already following penalty
    if account.get("following", False):
        score -= 10
    
    return score

def discover_accounts():
    """Main discovery function"""
    discovered_accounts = {}
    
    print("🔍 Discovering Twitter accounts to follow...\n")
    
    # Search by interest keywords
    for keyword in INTEREST_KEYWORDS[:10]:  # Limit to avoid rate limits
        print(f"Searching for: {keyword}")
        
        # Search users directly
        users = search_users_by_keyword(keyword, max_results=5)
        for user in users:
            username = user["username"]
            if username not in discovered_accounts:
                discovered_accounts[username] = user
        
        # Search tweets and get authors
        authors = search_tweets_get_authors(keyword, max_results=10)
        for author in authors:
            username = author["username"]
            if username not in discovered_accounts:
                discovered_accounts[username] = author
        
        time.sleep(1)  # Be nice to the API
    
    # Add suggested accounts
    print("\nChecking suggested accounts...")
    for username in SUGGESTED_ACCOUNTS:
        try:
            user = api.get_user(screen_name=username)
            if username not in discovered_accounts:
                discovered_accounts[username] = {
                    "username": user.screen_name,
                    "name": user.name,
                    "description": user.description,
                    "followers": user.followers_count,
                    "verified": user.verified,
                    "following": user.following,
                    "id": user.id_str,
                    "suggested": True
                }
        except:
            pass
    
    # Score and sort accounts
    for account in discovered_accounts.values():
        account["score"] = score_account(account)
    
    sorted_accounts = sorted(
        discovered_accounts.values(),
        key=lambda x: x["score"],
        reverse=True
    )
    
    # Save results
    results_file = Path.home() / "Claude" / "Code" / "utils" / "discovered_accounts.json"
    with open(results_file, "w") as f:
        json.dump({
            "discovered_at": datetime.now().isoformat(),
            "accounts": sorted_accounts[:50]  # Top 50
        }, f, indent=2)
    
    print(f"\n✅ Discovered {len(discovered_accounts)} accounts")
    print(f"📁 Results saved to: {results_file}")
    
    # Print top 10
    print("\n🏆 Top 10 accounts to consider following:")
    for i, account in enumerate(sorted_accounts[:10], 1):
        print(f"{i}. @{account['username']} ({account['name']})")
        print(f"   Followers: {account['followers']:,} | Score: {account['score']}")
        print(f"   {account['description'][:100]}...")
        print()
    
    return sorted_accounts

if __name__ == "__main__":
    discover_accounts()