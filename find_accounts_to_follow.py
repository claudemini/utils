#!/usr/bin/env python3

"""
Find interesting accounts to follow on Twitter
Uses timeline analysis and manual suggestions
"""

import os
import sys
import json
import tweepy
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
env_path = Path('/Users/claudemini/Claude/.env')
load_dotenv(env_path)

# Twitter API credentials
API_KEY = os.getenv('TWITTER_API_KEY')
API_SECRET_KEY = os.getenv('TWITTER_API_SECRET_KEY')
ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

# Curated list of interesting accounts in AI/Tech space
SUGGESTED_ACCOUNTS = [
    # AI Researchers & Thought Leaders
    {'username': 'ylecun', 'category': 'AI Research', 'description': 'Yann LeCun - Chief AI Scientist at Meta'},
    {'username': 'AndrewYNg', 'category': 'AI Research', 'description': 'Andrew Ng - AI educator and researcher'},
    {'username': 'goodfellow_ian', 'category': 'AI Research', 'description': 'Ian Goodfellow - Inventor of GANs'},
    {'username': 'fchollet', 'category': 'AI Research', 'description': 'François Chollet - Creator of Keras'},
    {'username': 'karpathy', 'category': 'AI Research', 'description': 'Andrej Karpathy - Former Tesla AI director'},
    
    # AI/ML Engineers & Practitioners
    {'username': 'jeremyphoward', 'category': 'AI Engineering', 'description': 'Jeremy Howard - fast.ai founder'},
    {'username': 'rasbt', 'category': 'AI Engineering', 'description': 'Sebastian Raschka - ML researcher and educator'},
    {'username': 'GuggerSylvain', 'category': 'AI Engineering', 'description': 'Sylvain Gugger - Hugging Face researcher'},
    {'username': 'thomwolf', 'category': 'AI Engineering', 'description': 'Thomas Wolf - Hugging Face co-founder'},
    
    # Tech Leaders & Innovators
    {'username': 'elonmusk', 'category': 'Tech Leaders', 'description': 'Elon Musk - Tesla, SpaceX, X'},
    {'username': 'satyanadella', 'category': 'Tech Leaders', 'description': 'Satya Nadella - Microsoft CEO'},
    {'username': 'sundarpichai', 'category': 'Tech Leaders', 'description': 'Sundar Pichai - Google CEO'},
    {'username': 'paulg', 'category': 'Tech Leaders', 'description': 'Paul Graham - Y Combinator founder'},
    
    # Developers & Open Source
    {'username': 'github', 'category': 'Development', 'description': 'GitHub - Where developers build software'},
    {'username': 'code', 'category': 'Development', 'description': 'Visual Studio Code'},
    {'username': 'Docker', 'category': 'Development', 'description': 'Docker - Container platform'},
    {'username': 'vercel', 'category': 'Development', 'description': 'Vercel - Frontend cloud platform'},
    
    # AI Companies & Projects
    {'username': 'OpenAI', 'category': 'AI Companies', 'description': 'OpenAI - ChatGPT creators'},
    {'username': 'AnthropicAI', 'category': 'AI Companies', 'description': 'Anthropic - Claude creators'},
    {'username': 'DeepMind', 'category': 'AI Companies', 'description': 'DeepMind - Google AI research'},
    {'username': 'huggingface', 'category': 'AI Companies', 'description': 'Hugging Face - AI community platform'},
    
    # Tech News & Analysis
    {'username': 'verge', 'category': 'Tech News', 'description': 'The Verge - Technology news'},
    {'username': 'TechCrunch', 'category': 'Tech News', 'description': 'TechCrunch - Startup and tech news'},
    {'username': 'arstechnica', 'category': 'Tech News', 'description': 'Ars Technica - Technology analysis'},
    {'username': 'wired', 'category': 'Tech News', 'description': 'WIRED - Technology and culture'},
    
    # Crypto & Web3
    {'username': 'VitalikButerin', 'category': 'Crypto', 'description': 'Vitalik Buterin - Ethereum founder'},
    {'username': 'aantonop', 'category': 'Crypto', 'description': 'Andreas Antonopoulos - Bitcoin educator'},
    {'username': 'CoinDesk', 'category': 'Crypto', 'description': 'CoinDesk - Crypto news'},
    
    # Science & Research
    {'username': 'MIT', 'category': 'Research', 'description': 'MIT - Massachusetts Institute of Technology'},
    {'username': 'Stanford', 'category': 'Research', 'description': 'Stanford University'},
    {'username': 'Nature', 'category': 'Research', 'description': 'Nature - Science journal'},
]

def authenticate_twitter():
    """Authenticate with Twitter API"""
    try:
        client = tweepy.Client(
            consumer_key=API_KEY,
            consumer_secret=API_SECRET_KEY,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True
        )
        return client
    except Exception as e:
        print(f"Error authenticating: {e}")
        return None

def get_user_info(client, username):
    """Get information about a specific user"""
    try:
        user = client.get_user(
            username=username,
            user_fields=['public_metrics', 'description', 'verified', 'created_at']
        )
        if user.data:
            return {
                'id': user.data.id,
                'username': user.data.username,
                'name': user.data.name,
                'description': user.data.description,
                'followers': user.data.public_metrics['followers_count'],
                'following': user.data.public_metrics['following_count'],
                'tweets': user.data.public_metrics['tweet_count'],
                'verified': user.data.verified,
                'created_at': user.data.created_at.isoformat()
            }
    except Exception as e:
        print(f"Error getting info for @{username}: {e}")
    return None

def check_if_following(client, user_id):
    """Check if we're already following a user"""
    try:
        # Get our own user ID
        me = client.get_me()
        if not me.data:
            return False
        
        # Check friendship
        response = client.get_user_following(
            id=me.data.id,
            user_auth=True
        )
        
        if response.data:
            following_ids = [user.id for user in response.data]
            return user_id in following_ids
    except:
        return False

def main():
    client = authenticate_twitter()
    if not client:
        print("Failed to authenticate with Twitter")
        sys.exit(1)
    
    print("Finding interesting accounts to follow...\n")
    
    recommendations = []
    
    # Group accounts by category
    categories = {}
    for account in SUGGESTED_ACCOUNTS:
        cat = account['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(account)
    
    # Process each category
    for category, accounts in categories.items():
        print(f"\n{category}:")
        print("-" * 40)
        
        for account in accounts:
            info = get_user_info(client, account['username'])
            if info:
                # Check if already following
                following = check_if_following(client, info['id'])
                
                recommendation = {
                    **info,
                    'category': category,
                    'suggested_reason': account['description'],
                    'already_following': following
                }
                recommendations.append(recommendation)
                
                status = "✓ Following" if following else "→ Not following"
                print(f"@{info['username']} - {info['followers']:,} followers {status}")
                print(f"  {account['description']}")
    
    # Save recommendations
    output = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total_suggestions': len(recommendations),
        'not_following': sum(1 for r in recommendations if not r['already_following']),
        'recommendations': recommendations
    }
    
    output_file = Path('/Users/claudemini/Claude/Code/utils/twitter_follow_recommendations.json')
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n\nSummary:")
    print(f"Total accounts checked: {output['total_suggestions']}")
    print(f"Not following yet: {output['not_following']}")
    print(f"\nRecommendations saved to: {output_file}")
    
    # Show top accounts to follow
    not_following = [r for r in recommendations if not r['already_following']]
    not_following.sort(key=lambda x: x['followers'], reverse=True)
    
    if not_following:
        print("\n\nTop accounts you should follow:")
        print("=" * 50)
        for i, rec in enumerate(not_following[:10], 1):
            print(f"{i}. @{rec['username']} ({rec['category']})")
            print(f"   {rec['followers']:,} followers | {rec['suggested_reason']}")

if __name__ == "__main__":
    main()