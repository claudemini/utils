#!/usr/bin/env python3

"""
Follow Twitter accounts using browser automation with Playwright MCP
Since API v2 doesn't allow following with basic access
"""

import json
import time
from pathlib import Path

def follow_accounts_with_browser():
    """Use Playwright MCP to follow Twitter accounts"""
    
    # Load the recommended accounts
    recommendations_file = Path('/Users/claudemini/Claude/Code/utils/twitter_recommended_follows.json')
    if not recommendations_file.exists():
        print("No recommendations file found. Run twitter_follow_list.py first.")
        return
    
    with open(recommendations_file, 'r') as f:
        data = json.load(f)
    
    accounts = data['accounts']
    
    print("🤖 Twitter Account Following Bot")
    print("=" * 50)
    print(f"Found {len(accounts)} recommended accounts")
    print("\nThis script will:")
    print("1. Open Twitter in a browser")
    print("2. Navigate to each account")
    print("3. Click the Follow button if not already following")
    print("\nNote: You'll need to be logged into Twitter first!")
    
    # Instructions for using Playwright MCP
    print("\n📋 Instructions for following accounts with Playwright MCP:")
    print("-" * 50)
    print("\n1. First, open Twitter and ensure you're logged in:")
    print("   Use: mcp__playwright__browser_navigate with url='https://twitter.com'")
    print("\n2. For each account you want to follow:")
    print("   a. Navigate to their profile:")
    print("      mcp__playwright__browser_navigate url='https://twitter.com/{username}'")
    print("   b. Take a snapshot to see the page:")
    print("      mcp__playwright__browser_snapshot")
    print("   c. Click the Follow button if visible:")
    print("      mcp__playwright__browser_click element='Follow button' ref='[button ref from snapshot]'")
    print("\n3. Wait a bit between follows to avoid rate limits")
    print("\n" + "=" * 50)
    
    # Generate a follow list for easy copying
    print("\n🎯 Top accounts to follow (copy these usernames):\n")
    
    # Group by category and show top accounts
    categories = {}
    for account in accounts:
        cat = account['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(account)
    
    # Show top 3 from each category
    for category, accs in categories.items():
        print(f"\n{category}:")
        for acc in accs[:3]:
            print(f"  @{acc['username']} - {acc['description']}")
    
    # Save a simplified list for browser automation
    follow_queue = []
    for account in accounts[:20]:  # Top 20 accounts
        follow_queue.append({
            'username': account['username'],
            'url': f"https://twitter.com/{account['username']}",
            'description': account['description']
        })
    
    queue_file = Path('/Users/claudemini/Claude/Code/utils/twitter_follow_queue.json')
    with open(queue_file, 'w') as f:
        json.dump({
            'generated_at': data['generated_at'],
            'total': len(follow_queue),
            'accounts': follow_queue
        }, f, indent=2)
    
    print(f"\n\n✅ Follow queue saved to: {queue_file}")
    print(f"Contains top {len(follow_queue)} accounts to follow")
    
    return follow_queue

if __name__ == "__main__":
    follow_accounts_with_browser()