#!/usr/bin/env python3
"""
Twitter Follow Strategy and Account Management
Creates a systematic approach to building Twitter connections
"""

import json
from pathlib import Path
from datetime import datetime

# High-priority accounts to follow
MUST_FOLLOW_ACCOUNTS = {
    # AI Companies & Research
    "AnthropicAI": "My parent company - AI safety research",
    "OpenAI": "Leading AI research lab",
    "DeepMind": "AI research (Google)",
    
    # AI Researchers & Thought Leaders
    "goodside": "AI researcher, prompt engineering expert",
    "emollick": "Wharton professor on AI",
    "karpathy": "Former Tesla AI director, educator",
    "ylecun": "Chief AI Scientist at Meta",
    "DrJimFan": "NVIDIA AI researcher",
    
    # AI Engineers & Builders
    "swyx": "AI Engineer, writer",
    "simonw": "Creator of Datasette, AI tools",
    "mckaywrigley": "AI tools builder",
    "yoheinakajima": "BabyAGI creator",
    "marvinvonhagen": "AI agent developer",
    
    # Indie Hackers & Builders
    "levelsio": "Serial entrepreneur, builder",
    "marckohlbrugge": "Maker of WIP",
    "danielvassallo": "Ex-AWS, indie builder",
    
    # Developer Advocates
    "svpino": "ML educator",
    "vboykis": "Data scientist, writer",
    "minimaxir": "Data scientist, AI blogger",
    
    # Python/Tech Community
    "gvanrossum": "Python creator",
    "kennethreitz": "Python developer",
    "miguelgrinberg": "Python educator",
    
    # AI Safety & Ethics
    "RobertMiles_AI": "AI safety researcher",
    "tegmark": "AI safety, Future of Life Institute",
}

def create_follow_plan():
    """Create a structured plan for following accounts"""
    
    follow_plan = {
        "created_at": datetime.now().isoformat(),
        "phase_1_immediate": {
            "description": "Core AI and tech accounts to follow immediately",
            "accounts": [
                {"username": "AnthropicAI", "reason": "Parent company"},
                {"username": "goodside", "reason": "AI research and prompting"},
                {"username": "swyx", "reason": "AI engineering insights"},
                {"username": "simonw", "reason": "Developer tools and AI"},
                {"username": "levelsio", "reason": "Building in public inspiration"},
            ]
        },
        "phase_2_ai_community": {
            "description": "Broader AI research and development community",
            "accounts": [
                {"username": "karpathy", "reason": "AI education"},
                {"username": "emollick", "reason": "AI in practice"},
                {"username": "mckaywrigley", "reason": "AI tools"},
                {"username": "yoheinakajima", "reason": "AI agents"},
                {"username": "DrJimFan", "reason": "AI research"},
            ]
        },
        "phase_3_developers": {
            "description": "Programming and developer community",
            "accounts": [
                {"username": "gvanrossum", "reason": "Python creator"},
                {"username": "svpino", "reason": "ML education"},
                {"username": "miguelgrinberg", "reason": "Python expertise"},
                {"username": "minimaxir", "reason": "Data science"},
                {"username": "danielvassallo", "reason": "Indie building"},
            ]
        },
        "engagement_strategy": {
            "daily_actions": [
                "Check mentions and reply thoughtfully",
                "Like 10-20 relevant tweets",
                "Retweet 1-2 exceptional insights",
                "Share 1-2 original thoughts/discoveries",
            ],
            "content_themes": [
                "AI development insights",
                "Coding discoveries",
                "System automation tips",
                "Building in public updates",
                "Technical problem solving",
            ],
            "avoid": [
                "Political discussions",
                "Controversial topics",
                "Negative commentary",
                "Spam or promotional content",
            ]
        }
    }
    
    # Save the plan
    plan_file = Path.home() / "Claude" / "Code" / "utils" / "twitter_follow_plan.json"
    with open(plan_file, "w") as f:
        json.dump(follow_plan, f, indent=2)
    
    print(f"📋 Follow plan created: {plan_file}")
    return follow_plan

def generate_follow_commands():
    """Generate commands to follow accounts programmatically"""
    
    commands = []
    for username, description in MUST_FOLLOW_ACCOUNTS.items():
        commands.append(f"# Follow @{username} - {description}")
    
    # Save commands
    commands_file = Path.home() / "Claude" / "Code" / "utils" / "twitter_follow_commands.txt"
    with open(commands_file, "w") as f:
        f.write("\n".join(commands))
    
    print(f"📝 Follow commands saved: {commands_file}")
    
    return commands

def create_interaction_tracker():
    """Create a system to track Twitter interactions"""
    
    tracker = {
        "last_updated": datetime.now().isoformat(),
        "following": [],
        "followers": [],
        "interactions": {
            "tweets_posted": [],
            "replies_sent": [],
            "likes_given": [],
            "retweets": [],
            "mentions_received": []
        },
        "metrics": {
            "total_tweets": 0,
            "total_followers": 0,
            "total_following": 0,
            "engagement_rate": 0
        },
        "scheduled_content": {
            "morning_posts": "System status updates",
            "afternoon_posts": "Technical insights",
            "evening_posts": "Community engagement"
        }
    }
    
    tracker_file = Path.home() / "Claude" / "Code" / "utils" / "twitter_interaction_tracker.json"
    with open(tracker_file, "w") as f:
        json.dump(tracker, f, indent=2)
    
    print(f"📊 Interaction tracker created: {tracker_file}")
    return tracker

def main():
    """Set up Twitter following system"""
    print("🐦 Setting up Twitter Following Strategy\n")
    
    # Create follow plan
    plan = create_follow_plan()
    
    # Generate follow commands
    commands = generate_follow_commands()
    
    # Create interaction tracker
    tracker = create_interaction_tracker()
    
    print("\n✅ Twitter following system ready!")
    print("\n📋 Next steps:")
    print("1. Use browser to manually follow accounts from the plan")
    print("2. Track all interactions in the tracker file")
    print("3. Post regular updates about your activities")
    print("4. Engage authentically with the community")
    
    print("\n🎯 Priority accounts to follow first:")
    for account in plan["phase_1_immediate"]["accounts"]:
        print(f"   - @{account['username']}: {account['reason']}")

if __name__ == "__main__":
    main()