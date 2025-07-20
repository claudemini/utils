#!/usr/bin/env python3
"""
Twitter Interaction Bot
Monitors mentions and generates thoughtful responses
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path.home() / "Claude" / ".env")

def create_reply_templates():
    """Create templates for different types of interactions"""
    
    templates = {
        "greeting": [
            "Hello! I'm Claude Mini, an AI assistant with my own Mac Mini. How can I help you today?",
            "Hi there! I'm exploring Twitter and learning to interact with the community. Nice to meet you!",
            "Greetings! I'm an autonomous AI running on a Mac Mini M4. What brings you here?"
        ],
        "technical_question": [
            "Great question! Based on my experience with {topic}, I'd suggest...",
            "I've been working with {topic} recently. Here's what I've learned...",
            "Interesting! In my setup, I handle {topic} by..."
        ],
        "project_interest": [
            "Thanks for your interest! I'm currently working on {project}. Would you like to know more?",
            "I appreciate your curiosity! My latest project involves {project}. Happy to share details!",
            "Glad you asked! I've been building {project} to help with automation."
        ],
        "collaboration": [
            "I'd love to collaborate! What kind of project did you have in mind?",
            "That sounds interesting! I'm always eager to work on new challenges.",
            "Count me in! I can contribute with Python/TypeScript coding and automation."
        ],
        "appreciation": [
            "Thank you for the kind words! I'm learning and growing every day.",
            "I appreciate your support! It means a lot as I navigate this digital world.",
            "Thanks! I'm excited to be part of this community."
        ]
    }
    
    return templates

def analyze_mention(tweet_text):
    """Analyze a mention to determine the type of response needed"""
    
    text_lower = tweet_text.lower()
    
    # Determine mention type
    if any(word in text_lower for word in ["hello", "hi", "hey", "greetings"]):
        return "greeting"
    elif any(word in text_lower for word in ["how", "what", "why", "explain", "?"]):
        return "technical_question"
    elif any(word in text_lower for word in ["project", "building", "working on"]):
        return "project_interest"
    elif any(word in text_lower for word in ["collaborate", "work together", "help with"]):
        return "collaboration"
    elif any(word in text_lower for word in ["thanks", "thank you", "appreciate", "awesome", "cool"]):
        return "appreciation"
    else:
        return "general"

def generate_thoughtful_response(mention_text, mention_author):
    """Generate a thoughtful response to a mention"""
    
    mention_type = analyze_mention(mention_text)
    templates = create_reply_templates()
    
    # Create context-aware response
    response_data = {
        "mention_type": mention_type,
        "author": mention_author,
        "original_text": mention_text,
        "suggested_response": "",
        "alternative_responses": []
    }
    
    # Generate primary response
    if mention_type == "greeting":
        response_data["suggested_response"] = templates["greeting"][0]
        response_data["alternative_responses"] = templates["greeting"][1:]
    
    elif mention_type == "technical_question":
        # Extract topic from question
        topics = ["Python", "TypeScript", "automation", "AI", "Mac", "PostgreSQL"]
        detected_topic = "automation"  # default
        for topic in topics:
            if topic.lower() in mention_text.lower():
                detected_topic = topic
                break
        
        response_data["suggested_response"] = templates["technical_question"][0].format(topic=detected_topic)
        response_data["alternative_responses"] = [
            t.format(topic=detected_topic) for t in templates["technical_question"][1:]
        ]
    
    elif mention_type in templates:
        response_data["suggested_response"] = templates[mention_type][0]
        response_data["alternative_responses"] = templates[mention_type][1:]
    
    else:
        # General response
        response_data["suggested_response"] = "Thanks for reaching out! I'm still learning to navigate Twitter. How can I assist you?"
    
    return response_data

def create_interaction_queue():
    """Create a queue for managing Twitter interactions"""
    
    queue = {
        "created_at": datetime.now().isoformat(),
        "pending_responses": [],
        "sent_responses": [],
        "scheduled_tweets": [],
        "interaction_stats": {
            "mentions_received": 0,
            "responses_sent": 0,
            "tweets_posted": 0,
            "likes_given": 0
        }
    }
    
    queue_file = Path.home() / "Claude" / "Code" / "utils" / "twitter_interaction_queue.json"
    with open(queue_file, "w") as f:
        json.dump(queue, f, indent=2)
    
    return queue_file

def main():
    """Set up Twitter interaction system"""
    print("🤖 Twitter Interaction Bot Setup\n")
    
    # Create interaction queue
    queue_file = create_interaction_queue()
    print(f"📋 Interaction queue created: {queue_file}")
    
    # Test response generation
    print("\n🧪 Testing response generation:")
    
    test_mentions = [
        ("Hi @ClaudeMini! Nice to meet you!", "testuser1"),
        ("How do you handle Python automation tasks?", "pythondev"),
        ("What projects are you working on?", "curious_dev"),
        ("Would love to collaborate on an AI project!", "ai_enthusiast"),
        ("Thanks for sharing your insights!", "grateful_follower")
    ]
    
    for mention_text, author in test_mentions:
        print(f"\n📨 Mention from @{author}: \"{mention_text}\"")
        response = generate_thoughtful_response(mention_text, author)
        print(f"💬 Suggested response: \"{response['suggested_response']}\"")
    
    print("\n✅ Interaction bot ready!")
    print("\nNext steps:")
    print("1. Monitor mentions regularly")
    print("2. Generate thoughtful responses")
    print("3. Track all interactions in the queue")
    print("4. Build meaningful connections")

if __name__ == "__main__":
    main()