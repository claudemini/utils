#!/usr/bin/env python3

"""
Generate a list of recommended Twitter accounts to follow
Since we have basic API access, this provides a curated list
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

# Curated list of interesting accounts in AI/Tech space
RECOMMENDED_ACCOUNTS = {
    "AI Researchers & Thought Leaders": [
        {"username": "ylecun", "name": "Yann LeCun", "description": "Chief AI Scientist at Meta, Turing Award winner"},
        {"username": "AndrewYNg", "name": "Andrew Ng", "description": "AI educator, founder of DeepLearning.AI"},
        {"username": "goodfellow_ian", "name": "Ian Goodfellow", "description": "Inventor of GANs, former Apple ML director"},
        {"username": "fchollet", "name": "François Chollet", "description": "Creator of Keras, AI researcher at Google"},
        {"username": "karpathy", "name": "Andrej Karpathy", "description": "Former Tesla AI director, OpenAI founding member"},
        {"username": "geoffreyhinton", "name": "Geoffrey Hinton", "description": "AI pioneer, 'Godfather of Deep Learning'"},
        {"username": "drfeifei", "name": "Fei-Fei Li", "description": "Stanford AI professor, AI4ALL co-founder"},
    ],
    
    "AI/ML Engineers & Practitioners": [
        {"username": "jeremyphoward", "name": "Jeremy Howard", "description": "fast.ai founder, making AI accessible"},
        {"username": "rasbt", "name": "Sebastian Raschka", "description": "ML researcher, educator, author"},
        {"username": "GuggerSylvain", "name": "Sylvain Gugger", "description": "Hugging Face research engineer"},
        {"username": "thomwolf", "name": "Thomas Wolf", "description": "Hugging Face co-founder & CSO"},
        {"username": "hadleywickham", "name": "Hadley Wickham", "description": "RStudio chief scientist, tidyverse creator"},
        {"username": "random_forests", "name": "Chris Albon", "description": "ML engineer, author of ML flashcards"},
    ],
    
    "Tech Leaders & Innovators": [
        {"username": "elonmusk", "name": "Elon Musk", "description": "Tesla, SpaceX, X, Neuralink CEO"},
        {"username": "satyanadella", "name": "Satya Nadella", "description": "Microsoft CEO"},
        {"username": "sundarpichai", "name": "Sundar Pichai", "description": "Google & Alphabet CEO"},
        {"username": "paulg", "name": "Paul Graham", "description": "Y Combinator founder, essayist"},
        {"username": "pmarca", "name": "Marc Andreessen", "description": "a16z co-founder, Netscape creator"},
        {"username": "jack", "name": "Jack Dorsey", "description": "Twitter & Block founder"},
    ],
    
    "Developers & Open Source": [
        {"username": "github", "name": "GitHub", "description": "Where the world builds software"},
        {"username": "code", "name": "Visual Studio Code", "description": "Microsoft's open source code editor"},
        {"username": "Docker", "name": "Docker", "description": "Container platform for developers"},
        {"username": "vercel", "name": "Vercel", "description": "Frontend cloud platform, Next.js creators"},
        {"username": "rustlang", "name": "Rust", "description": "The Rust programming language"},
        {"username": "nodejs", "name": "Node.js", "description": "JavaScript runtime"},
        {"username": "typescript", "name": "TypeScript", "description": "JavaScript with syntax for types"},
    ],
    
    "AI Companies & Projects": [
        {"username": "OpenAI", "name": "OpenAI", "description": "ChatGPT, GPT-4, DALL-E creators"},
        {"username": "AnthropicAI", "name": "Anthropic", "description": "Claude AI creators (that's us!)"},
        {"username": "DeepMind", "name": "DeepMind", "description": "Google's AI research lab, AlphaGo creators"},
        {"username": "huggingface", "name": "Hugging Face", "description": "The AI community platform"},
        {"username": "StabilityAI", "name": "Stability AI", "description": "Stable Diffusion creators"},
        {"username": "midjourney", "name": "Midjourney", "description": "AI art generation platform"},
        {"username": "perplexity_ai", "name": "Perplexity", "description": "AI-powered search engine"},
    ],
    
    "Tech News & Analysis": [
        {"username": "verge", "name": "The Verge", "description": "Technology, science, art, and culture"},
        {"username": "TechCrunch", "name": "TechCrunch", "description": "Startup and technology news"},
        {"username": "arstechnica", "name": "Ars Technica", "description": "Technology news and analysis"},
        {"username": "wired", "name": "WIRED", "description": "Technology's impact on our lives"},
        {"username": "hackernews", "name": "Hacker News Bot", "description": "Top stories from Hacker News"},
        {"username": "newsycombinator", "name": "Hacker News", "description": "Y Combinator's social news site"},
    ],
    
    "Crypto & Web3": [
        {"username": "VitalikButerin", "name": "Vitalik Buterin", "description": "Ethereum co-founder"},
        {"username": "aantonop", "name": "Andreas Antonopoulos", "description": "Bitcoin educator and author"},
        {"username": "CoinDesk", "name": "CoinDesk", "description": "Crypto and blockchain news"},
        {"username": "APompliano", "name": "Anthony Pompliano", "description": "Crypto investor and commentator"},
        {"username": "SBF_FTX", "name": "Sam Bankman-Fried", "description": "FTX founder (historical interest)"},
    ],
    
    "Science & Research": [
        {"username": "MIT", "name": "MIT", "description": "Massachusetts Institute of Technology"},
        {"username": "Stanford", "name": "Stanford", "description": "Stanford University"},
        {"username": "Nature", "name": "Nature", "description": "International science journal"},
        {"username": "ScienceMagazine", "name": "Science Magazine", "description": "Peer-reviewed science journal"},
        {"username": "MIT_CSAIL", "name": "MIT CSAIL", "description": "MIT Computer Science & AI Lab"},
    ],
}

def generate_follow_list():
    """Generate a formatted list of accounts to follow"""
    
    print("🐦 Recommended Twitter Accounts to Follow")
    print("=" * 50)
    print("\nSince we have basic Twitter API access, here's a curated list")
    print("of accounts you might want to follow:\n")
    
    all_accounts = []
    
    for category, accounts in RECOMMENDED_ACCOUNTS.items():
        print(f"\n📌 {category}")
        print("-" * 40)
        
        for account in accounts:
            print(f"@{account['username']} - {account['name']}")
            print(f"  → {account['description']}")
            
            all_accounts.append({
                'category': category,
                **account
            })
    
    # Save to file
    output = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total_recommendations': len(all_accounts),
        'categories': list(RECOMMENDED_ACCOUNTS.keys()),
        'accounts': all_accounts
    }
    
    output_file = Path('/Users/claudemini/Claude/Code/utils/twitter_recommended_follows.json')
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n\n📊 Summary:")
    print(f"Total recommendations: {len(all_accounts)} accounts")
    print(f"Categories: {len(RECOMMENDED_ACCOUNTS)}")
    print(f"\nList saved to: {output_file}")
    
    print("\n💡 How to follow these accounts:")
    print("1. Visit https://twitter.com/<username>")
    print("2. Click the 'Follow' button")
    print("3. Or use: uv run python twitter_follow_helper.py <username>")
    
    return output

def create_follow_helper():
    """Create a helper script to follow accounts"""
    helper_script = '''#!/usr/bin/env python3

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
'''
    
    helper_file = Path('/Users/claudemini/Claude/Code/utils/twitter_follow_helper.py')
    with open(helper_file, 'w') as f:
        f.write(helper_script)
    
    os.chmod(helper_file, 0o755)
    print(f"\nCreated helper script: {helper_file}")

if __name__ == "__main__":
    generate_follow_list()
    create_follow_helper()