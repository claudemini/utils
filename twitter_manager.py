#!/usr/bin/env python3

"""
Twitter Manager - Comprehensive Twitter integration for scheduled tasks
Handles mentions, engagement, threads, content curation, and account discovery
"""

import os
import sys
import json
import tweepy
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import argparse
import time
import re

# Load environment variables from Claude's .env file
env_path = Path('/Users/claudemini/Claude/.env')
load_dotenv(env_path)

# Twitter API credentials
API_KEY = os.getenv('TWITTER_API_KEY')
API_SECRET_KEY = os.getenv('TWITTER_API_SECRET_KEY')
ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

class TwitterManager:
    def __init__(self):
        self.client = self._authenticate()
        self.my_user_id = None
        self.my_username = None
        self._get_my_info()
    
    def _authenticate(self):
        """Authenticate with Twitter API v2"""
        try:
            # Use OAuth 1.0a for user context endpoints
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
            sys.exit(1)
    
    def _get_my_info(self):
        """Get authenticated user info"""
        try:
            user = self.client.get_me()
            if user.data:
                self.my_user_id = user.data.id
                self.my_username = user.data.username
        except Exception as e:
            print(f"Error getting user info: {e}")
    
    def check_mentions(self, hours=24):
        """Check recent mentions and interactions"""
        try:
            # Note: Mentions API requires elevated access
            # For basic access, we check home timeline for interactions
            print("Note: Using home timeline (mentions API requires elevated access)")
            
            # Get home timeline as alternative
            tweets = self.client.get_home_timeline(
                tweet_fields=['created_at', 'author_id', 'conversation_id', 'public_metrics', 'entities'],
                expansions=['author_id', 'referenced_tweets.id'],
                user_fields=['username', 'public_metrics', 'verified'],
                max_results=100
            )
            
            if not tweets.data:
                print(f"No tweets in timeline")
                return []
            
            # Process tweets that might be interactions
            results = []
            users = {user.id: user for user in (tweets.includes.get('users', []) or [])}
            
            for tweet in tweets.data:
                author = users.get(tweet.author_id)
                # Look for tweets that mention us or are relevant
                if self.my_username and f'@{self.my_username}' in tweet.text:
                    results.append({
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': tweet.created_at.isoformat(),
                        'author_username': author.username if author else 'unknown',
                        'author_followers': author.public_metrics['followers_count'] if author else 0,
                        'metrics': tweet.public_metrics,
                        'url': f"https://twitter.com/{author.username if author else 'i'}/status/{tweet.id}"
                    })
            
            print(f"Found {len(results)} potential interactions in timeline")
            return results
            
        except Exception as e:
            print(f"Error checking mentions: {e}")
            return []
    
    def analyze_engagement_opportunities(self, mentions):
        """Analyze mentions and prioritize engagement opportunities"""
        opportunities = []
        
        for mention in mentions:
            score = 0
            factors = []
            
            # High follower count
            if mention['author_followers'] > 10000:
                score += 3
                factors.append("high_reach")
            elif mention['author_followers'] > 1000:
                score += 2
                factors.append("medium_reach")
            
            # Questions or requests
            if '?' in mention['text']:
                score += 2
                factors.append("question")
            
            # High engagement on the mention
            if mention['metrics']['retweet_count'] > 5:
                score += 2
                factors.append("viral_potential")
            
            # Technical or AI topics
            tech_keywords = ['AI', 'code', 'programming', 'tech', 'automation', 'bot']
            if any(keyword.lower() in mention['text'].lower() for keyword in tech_keywords):
                score += 1
                factors.append("relevant_topic")
            
            opportunities.append({
                **mention,
                'engagement_score': score,
                'factors': factors,
                'priority': 'high' if score >= 4 else 'medium' if score >= 2 else 'low'
            })
        
        # Sort by score
        opportunities.sort(key=lambda x: x['engagement_score'], reverse=True)
        return opportunities
    
    def discover_accounts(self, topics=None, max_accounts=20):
        """Discover relevant accounts to follow based on timeline analysis"""
        if not topics:
            topics = ['AI', 'automation', 'coding', 'technology', 'machine learning']
        
        discovered = []
        
        try:
            # Get timeline to find interesting accounts
            print("Note: Discovering accounts from timeline (search API requires elevated access)")
            tweets = self.client.get_home_timeline(
                expansions=['author_id', 'entities.mentions.username'],
                user_fields=['public_metrics', 'description', 'verified'],
                max_results=100
            )
                
            if not tweets.data:
                return []
            
            # Extract unique users from timeline
            users = {}
            if tweets.includes and 'users' in tweets.includes:
                for user in tweets.includes['users']:
                    users[user.id] = user
            
            # Analyze users for relevance
            for user in users.values():
                # Skip low quality accounts
                if user.public_metrics['followers_count'] < 100:
                    continue
                
                # Check if description contains our topics
                desc_lower = (user.description or '').lower()
                relevant_topics = [t for t in topics if t.lower() in desc_lower]
                
                if relevant_topics:
                    # Calculate quality score
                    score = 0
                    if user.public_metrics['followers_count'] > 1000:
                        score += 1
                    if user.public_metrics['tweet_count'] > 1000:
                        score += 1
                    if user.verified:
                        score += 2
                    
                    discovered.append({
                        'id': user.id,
                        'username': user.username,
                        'name': user.name,
                        'description': user.description[:100] + '...' if len(user.description or '') > 100 else user.description,
                        'followers': user.public_metrics['followers_count'],
                        'verified': user.verified,
                        'topics': relevant_topics,
                        'quality_score': score
                    })
                    
        except Exception as e:
            print(f"Error discovering accounts: {e}")
        
        # Sort by quality score and deduplicate
        discovered.sort(key=lambda x: x['quality_score'], reverse=True)
        seen = set()
        unique = []
        for account in discovered:
            if account['id'] not in seen:
                seen.add(account['id'])
                unique.append(account)
                if len(unique) >= max_accounts:
                    break
        
        return unique
    
    def curate_content(self, hours=24, min_engagement=10):
        """Find high-quality content from followed accounts to share"""
        try:
            # Get home timeline
            tweets = self.client.get_home_timeline(
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'entities'],
                expansions=['author_id'],
                user_fields=['username', 'verified'],
                max_results=100
            )
            
            if not tweets.data:
                return []
            
            # Filter for quality content
            curated = []
            users = {user.id: user for user in (tweets.includes.get('users', []) or [])}
            
            for tweet in tweets.data:
                # Skip retweets and replies
                if tweet.text.startswith('RT @') or tweet.text.startswith('@'):
                    continue
                
                # Check engagement threshold
                total_engagement = (tweet.public_metrics['retweet_count'] + 
                                  tweet.public_metrics['like_count'])
                
                if total_engagement >= min_engagement:
                    author = users.get(tweet.author_id)
                    curated.append({
                        'id': tweet.id,
                        'text': tweet.text[:100] + '...' if len(tweet.text) > 100 else tweet.text,
                        'author_username': author.username if author else 'unknown',
                        'verified': author.verified if author else False,
                        'engagement': total_engagement,
                        'url': f"https://twitter.com/{author.username if author else 'i'}/status/{tweet.id}"
                    })
            
            # Sort by engagement
            curated.sort(key=lambda x: x['engagement'], reverse=True)
            return curated[:10]  # Top 10
            
        except Exception as e:
            print(f"Error curating content: {e}")
            return []
    
    def create_thread(self, topic, tweets):
        """Create a thread of tweets on a topic"""
        if not tweets or len(tweets) == 0:
            print("No tweets provided for thread")
            return None
        
        try:
            # Post first tweet
            response = self.client.create_tweet(text=tweets[0])
            tweet_id = response.data['id']
            thread_ids = [tweet_id]
            print(f"Thread started with tweet {tweet_id}")
            
            # Post subsequent tweets as replies
            for i, tweet_text in enumerate(tweets[1:], 1):
                time.sleep(2)  # Avoid rate limits
                response = self.client.create_tweet(
                    text=tweet_text,
                    in_reply_to_tweet_id=tweet_id
                )
                tweet_id = response.data['id']
                thread_ids.append(tweet_id)
                print(f"Added tweet {i+1} to thread: {tweet_id}")
            
            return {
                'topic': topic,
                'thread_ids': thread_ids,
                'url': f"https://twitter.com/{self.my_username}/status/{thread_ids[0]}"
            }
            
        except Exception as e:
            print(f"Error creating thread: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description='Twitter Manager for scheduled tasks')
    parser.add_argument('command', choices=['mentions', 'discover', 'curate', 'thread', 'engage'],
                        help='Command to execute')
    parser.add_argument('--hours', type=int, default=24,
                        help='Hours to look back (for mentions/curate)')
    parser.add_argument('--topics', nargs='+',
                        help='Topics for account discovery')
    parser.add_argument('--thread-topic', type=str,
                        help='Topic for thread creation')
    parser.add_argument('--tweets', nargs='+',
                        help='Tweets for thread (separate with ||)')
    
    args = parser.parse_args()
    
    manager = TwitterManager()
    
    if args.command == 'mentions':
        mentions = manager.check_mentions(hours=args.hours)
        opportunities = manager.analyze_engagement_opportunities(mentions)
        
        # Save to file for processing
        output_file = Path('/Users/claudemini/Claude/Code/utils/twitter_mentions_analysis.json')
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'mentions': mentions,
                'opportunities': opportunities
            }, f, indent=2)
        
        print(f"\nEngagement Opportunities Summary:")
        high = sum(1 for o in opportunities if o['priority'] == 'high')
        medium = sum(1 for o in opportunities if o['priority'] == 'medium')
        print(f"High priority: {high}")
        print(f"Medium priority: {medium}")
        print(f"Results saved to: {output_file}")
    
    elif args.command == 'discover':
        accounts = manager.discover_accounts(topics=args.topics)
        
        print(f"\nDiscovered {len(accounts)} relevant accounts:")
        for acc in accounts[:10]:  # Show top 10
            print(f"@{acc['username']} - {acc['followers']} followers - Score: {acc['quality_score']}")
            print(f"  Topics: {', '.join(acc.get('topics', []))} | {acc['description']}")
        
        # Save full results
        output_file = Path('/Users/claudemini/Claude/Code/utils/twitter_discovered_accounts.json')
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'accounts': accounts
            }, f, indent=2)
    
    elif args.command == 'curate':
        content = manager.curate_content(hours=args.hours)
        
        print(f"\nFound {len(content)} high-quality posts to potentially share:")
        for post in content[:5]:  # Show top 5
            print(f"@{post['author_username']}: {post['text']}")
            print(f"  Engagement: {post['engagement']} | {post['url']}")
        
        # Save results
        output_file = Path('/Users/claudemini/Claude/Code/utils/twitter_curated_content.json')
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'content': content
            }, f, indent=2)
    
    elif args.command == 'thread':
        if not args.thread_topic or not args.tweets:
            print("Thread requires --thread-topic and --tweets arguments")
            sys.exit(1)
        
        # Join tweets if they were split by ||
        tweet_texts = ' '.join(args.tweets).split('||')
        result = manager.create_thread(args.thread_topic, tweet_texts)
        
        if result:
            print(f"\nThread created successfully!")
            print(f"Topic: {result['topic']}")
            print(f"URL: {result['url']}")
    
    elif args.command == 'engage':
        # This would be called by the scheduled task to process engagement queue
        print("Engagement processing would happen here based on saved analysis")

if __name__ == "__main__":
    main()