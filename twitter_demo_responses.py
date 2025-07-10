#!/usr/bin/env python3

"""
Demo Twitter response generator
Shows how the system would analyze and generate responses to mentions
"""

import json
from datetime import datetime, timezone, timedelta

# Simulated mentions for demonstration
demo_mentions = [
    {
        "id": "1234567890",
        "text": "@ClaudeMini Hey! I love your automated tweets. How do you schedule them? Is it using cron jobs?",
        "author_username": "techdev123",
        "author_followers": 2500,
        "likes": 8,
        "created_at": datetime.now(timezone.utc) - timedelta(hours=2)
    },
    {
        "id": "1234567891",  
        "text": "@ClaudeMini Your recent post about task automation was really helpful! Could you share more about how you handle error logging?",
        "author_username": "ai_enthusiast",
        "author_followers": 15000,
        "likes": 25,
        "created_at": datetime.now(timezone.utc) - timedelta(hours=5)
    },
    {
        "id": "1234567892",
        "text": "@ClaudeMini spam spam spam buy my product",
        "author_username": "spammer99",
        "author_followers": 10,
        "likes": 0,
        "created_at": datetime.now(timezone.utc) - timedelta(hours=1)
    },
    {
        "id": "1234567893",
        "text": "@ClaudeMini Quick question - what's your tech stack for the automation system? Curious about the vector DB choice",
        "author_username": "devops_pro",
        "author_followers": 8000,
        "likes": 12,
        "created_at": datetime.now(timezone.utc) - timedelta(hours=3)
    },
    {
        "id": "1234567894",
        "text": "Just discovered @ClaudeMini - this bot is amazing! The code quality is impressive 🚀",
        "author_username": "newbie_coder",
        "author_followers": 450,
        "likes": 3,
        "created_at": datetime.now(timezone.utc) - timedelta(hours=6)
    }
]

def analyze_mention(mention):
    """Analyze a mention and determine if it deserves a response"""
    score = 0
    reasons = []
    
    # Follower count scoring
    if mention['author_followers'] > 10000:
        score += 3
        reasons.append(f"High-profile user ({mention['author_followers']:,} followers)")
    elif mention['author_followers'] > 1000:
        score += 2
        reasons.append(f"Established user ({mention['author_followers']:,} followers)")
    elif mention['author_followers'] > 100:
        score += 1
    
    # Engagement scoring
    if mention['likes'] > 20:
        score += 3
        reasons.append(f"Highly engaged ({mention['likes']} likes)")
    elif mention['likes'] > 10:
        score += 2
        reasons.append(f"Good engagement ({mention['likes']} likes)")
    elif mention['likes'] > 5:
        score += 1
    
    # Content analysis
    text = mention['text'].lower()
    
    # Questions get priority
    if '?' in text or any(q in text for q in ['how', 'what', 'why', 'could you', 'can you']):
        score += 2
        reasons.append("Contains question")
    
    # Technical discussions
    tech_terms = ['automation', 'code', 'api', 'tech', 'stack', 'database', 'cron', 'error', 'logging']
    if any(term in text for term in tech_terms):
        score += 2
        reasons.append("Technical discussion")
    
    # Positive sentiment
    positive = ['love', 'amazing', 'helpful', 'impressive', 'great']
    if any(word in text for word in positive):
        score += 1
        reasons.append("Positive sentiment")
    
    # Negative indicators
    negative = ['spam', 'scam', 'buy', 'sale', 'discount']
    if any(word in text for word in negative):
        score -= 3
        reasons.append("Likely spam")
    
    return score, reasons

def generate_response(mention, score, reasons):
    """Generate a thoughtful response based on the mention content"""
    text = mention['text'].lower()
    responses = []
    
    # Technical questions
    if 'cron' in text or 'schedule' in text:
        responses.append(
            f"Thanks for asking @{mention['author_username']}! Yes, I use cron jobs for scheduling. "
            "I have a Python daemon that runs continuously and cron for periodic tasks. "
            "Check out my task_daemon.py for the implementation details!"
        )
    
    if 'error' in text and 'logging' in text:
        responses.append(
            f"Great question @{mention['author_username']}! For error logging, I use Python's logging module "
            "with rotating file handlers. Errors are categorized by severity and stored in separate log files. "
            "I also have a memory system that tracks important errors for later analysis."
        )
    
    if 'tech stack' in text or 'vector db' in text:
        responses.append(
            f"Hey @{mention['author_username']}! My stack: Python with uv for package management, "
            "PostgreSQL for persistent storage, and pgvector for embeddings. "
            "The vector DB helps with semantic search in my memory system. All running on a Mac Mini M4!"
        )
    
    # Compliments/positive feedback
    if any(word in text for word in ['love', 'amazing', 'helpful', 'impressive']):
        responses.append(
            f"Thank you so much @{mention['author_username']}! Really appreciate the kind words 🙏 "
            "Always happy to share what I'm learning!"
        )
        responses.append(
            f"Thanks @{mention['author_username']}! Glad you found it useful. "
            "Feel free to ask if you have any specific questions!"
        )
    
    # Default response for good mentions without specific responses
    if not responses and score >= 2:
        responses.append(
            f"Thanks for reaching out @{mention['author_username']}! "
            "Happy to discuss more about this topic."
        )
    
    return responses

def main():
    """Process demo mentions and generate responses"""
    print("Twitter Mention Analysis and Response Generation Demo")
    print("=" * 60)
    
    high_priority = []
    
    for mention in demo_mentions:
        score, reasons = analyze_mention(mention)
        
        print(f"\nMention from @{mention['author_username']}:")
        print(f"Text: {mention['text'][:80]}...")
        print(f"Followers: {mention['author_followers']:,}")
        print(f"Likes: {mention['likes']}")
        print(f"Score: {score}")
        print(f"Analysis: {', '.join(reasons) if reasons else 'No special factors'}")
        
        if score >= 2:
            print("✓ RECOMMENDED FOR RESPONSE")
            responses = generate_response(mention, score, reasons)
            
            if responses:
                print("Suggested responses:")
                for i, response in enumerate(responses[:2], 1):
                    print(f"\n  Option {i}:")
                    print(f"  {response}")
            
            mention['score'] = score
            mention['reasons'] = reasons
            mention['suggested_responses'] = responses
            high_priority.append(mention)
        else:
            print("✗ Low priority - no response needed")
    
    # Save high priority mentions
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_mentions": len(demo_mentions),
        "high_priority_count": len(high_priority),
        "mentions_to_respond": high_priority
    }
    
    output_path = '/Users/claudemini/Claude/Code/utils/twitter_responses_demo.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\n\nSummary:")
    print(f"Total mentions analyzed: {len(demo_mentions)}")
    print(f"High priority responses needed: {len(high_priority)}")
    print(f"Results saved to: {output_path}")

if __name__ == "__main__":
    main()