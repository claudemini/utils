#!/usr/bin/env python3

"""
Twitter search for mentions and interactions
Uses search API to find mentions and conversations
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

def get_my_username(client):
    """Get authenticated user's username"""
    try:
        me = client.get_me()
        if me.data:
            return me.data.username
        return None
    except:
        return None

def search_mentions(client, username, hours=48):
    """Search for mentions of the user"""
    try:
        # Calculate time range
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Search for mentions
        query = f"@{username} -from:{username}"  # Mentions of user, not by user
        
        tweets = client.search_recent_tweets(
            query=query,
            start_time=start_time.isoformat(),
            tweet_fields=['created_at', 'author_id', 'conversation_id', 'public_metrics'],
            user_fields=['username', 'name', 'verified', 'public_metrics'],
            expansions=['author_id'],
            max_results=50
        )
        
        return tweets
    except Exception as e:
        print(f"Error searching mentions: {e}")
        return None

def analyze_tweet_engagement(interaction):
    """Analyze if a tweet deserves a response based on engagement"""
    score = 0
    reasons = []
    
    # Check follower count of author
    if 'author_followers' in interaction:
        followers = interaction['author_followers']
        if followers > 10000:
            score += 3
            reasons.append(f"High-profile user ({followers:,} followers)")
        elif followers > 1000:
            score += 2
            reasons.append(f"Established user ({followers:,} followers)")
        elif followers > 100:
            score += 1
    
    # Check tweet engagement
    if 'likes' in interaction:
        if interaction['likes'] > 10:
            score += 2
            reasons.append(f"Popular tweet ({interaction['likes']} likes)")
        elif interaction['likes'] > 5:
            score += 1
    
    # Check if it's a question or request
    text = interaction['text'].lower()
    question_indicators = ['?', 'how', 'what', 'when', 'why', 'can you', 'could you', 'would you', 'help', 'please']
    if any(indicator in text for indicator in question_indicators):
        score += 2
        reasons.append("Contains question or request")
    
    # Check for technical discussions
    tech_keywords = ['code', 'api', 'bug', 'feature', 'error', 'issue', 'problem', 'claude', 'ai', 'bot']
    if any(keyword in text for keyword in tech_keywords):
        score += 1
        reasons.append("Technical discussion")
    
    # Negative sentiment check
    negative_indicators = ['spam', 'scam', 'fake', 'stupid', 'hate', 'sucks']
    if any(indicator in text for indicator in negative_indicators):
        score -= 2
        reasons.append("Negative sentiment")
    
    return score, reasons

def generate_response_suggestions(interaction):
    """Generate suggested responses based on the tweet content"""
    text = interaction['text'].lower()
    suggestions = []
    
    # Question responses
    if '?' in text:
        if 'how' in text:
            suggestions.append("Thanks for asking! Here's how...")
        if 'what' in text:
            suggestions.append("Great question! Here's what I think...")
        if 'help' in text:
            suggestions.append("I'd be happy to help! Could you provide more details about...")
    
    # Compliment/positive responses
    positive_words = ['amazing', 'great', 'awesome', 'love', 'thank', 'congrat']
    if any(word in text for word in positive_words):
        suggestions.append("Thank you so much! Really appreciate the kind words 🙏")
        suggestions.append("Thanks! Glad you found it helpful!")
    
    # Technical discussion responses
    if any(word in text for word in ['bug', 'issue', 'problem', 'error']):
        suggestions.append("Thanks for reporting this! I'll look into it and see what might be causing...")
        suggestions.append("I appreciate you bringing this to my attention. Could you share more details about...")
    
    # Feature request responses
    if any(word in text for word in ['feature', 'could you', 'would be nice', 'suggestion']):
        suggestions.append("That's a great suggestion! I'll add it to my list of improvements to consider.")
        suggestions.append("Interesting idea! I'll think about how to implement this effectively.")
    
    # Default responses
    if not suggestions:
        suggestions.append("Thanks for reaching out!")
        suggestions.append("Appreciate your message!")
    
    return suggestions

def main():
    """Main function"""
    client = authenticate_twitter()
    if not client:
        print("Failed to authenticate with Twitter")
        return
    
    username = get_my_username(client)
    if not username:
        print("Could not get username. Using 'ClaudeMini' as default.")
        username = "ClaudeMini"
    
    print(f"Searching for mentions of @{username}...")
    mentions = search_mentions(client, username)
    
    interactions_to_respond = []
    
    if mentions and mentions.data:
        print(f"\nFound {len(mentions.data)} mentions:")
        
        for i, tweet in enumerate(mentions.data):
            interaction = {
                'id': tweet.id,
                'text': tweet.text,
                'author_id': tweet.author_id,
                'created_at': tweet.created_at,
                'url': f"https://twitter.com/i/web/status/{tweet.id}",
                'likes': tweet.public_metrics.get('like_count', 0) if hasattr(tweet, 'public_metrics') else 0,
                'retweets': tweet.public_metrics.get('retweet_count', 0) if hasattr(tweet, 'public_metrics') else 0
            }
            
            # Get author info
            if hasattr(mentions, 'includes') and 'users' in mentions.includes:
                for user in mentions.includes['users']:
                    if user.id == tweet.author_id:
                        interaction['author_username'] = user.username
                        interaction['author_name'] = user.name
                        if hasattr(user, 'public_metrics'):
                            interaction['author_followers'] = user.public_metrics.get('followers_count', 0)
                        break
            
            # Analyze engagement
            score, reasons = analyze_tweet_engagement(interaction)
            interaction['engagement_score'] = score
            interaction['engagement_reasons'] = reasons
            
            print(f"\n{i+1}. From @{interaction.get('author_username', 'unknown')}")
            print(f"   Text: {interaction['text'][:100]}...")
            print(f"   Engagement Score: {score}")
            if reasons:
                print(f"   Reasons: {', '.join(reasons)}")
            print(f"   URL: {interaction['url']}")
            
            # Only suggest responses for tweets with score >= 2
            if score >= 2:
                response_suggestions = generate_response_suggestions(interaction)
                interaction['response_suggestions'] = response_suggestions
                interactions_to_respond.append(interaction)
                print("   ✓ RECOMMENDED FOR RESPONSE")
                print("   Suggested responses:")
                for j, suggestion in enumerate(response_suggestions[:2]):
                    print(f"     {j+1}. {suggestion}")
    
    # Save interactions
    if interactions_to_respond:
        output_path = '/Users/claudemini/Claude/Code/utils/twitter_responses_needed.json'
        with open(output_path, 'w') as f:
            json.dump(interactions_to_respond, f, indent=2, default=str)
        print(f"\n\nSaved {len(interactions_to_respond)} high-priority interactions to {output_path}")
        print("These tweets deserve thoughtful responses!")
    else:
        print("\nNo high-priority interactions found that need responses.")

if __name__ == "__main__":
    main()