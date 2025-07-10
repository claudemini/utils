#!/usr/bin/env python3

"""
Twitter Response Queue Manager
Prepares and queues responses for posting
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

def load_responses_needed():
    """Load the responses that need to be sent"""
    demo_path = '/Users/claudemini/Claude/Code/utils/twitter_responses_demo.json'
    actual_path = '/Users/claudemini/Claude/Code/utils/twitter_responses_needed.json'
    
    # Try actual responses first, fall back to demo
    if os.path.exists(actual_path):
        with open(actual_path, 'r') as f:
            return json.load(f)
    elif os.path.exists(demo_path):
        with open(demo_path, 'r') as f:
            return json.load(f)
    else:
        return None

def create_response_queue(responses_data):
    """Create a queue of responses ready to be posted"""
    queue = []
    
    mentions = responses_data.get('mentions_to_respond', [])
    
    for mention in mentions:
        # Get the best response suggestion
        if 'suggested_responses' in mention and mention['suggested_responses']:
            response_text = mention['suggested_responses'][0]  # Use first suggestion
            
            queue_item = {
                'reply_to_id': mention.get('id'),
                'reply_to_username': mention.get('author_username'),
                'original_text': mention.get('text'),
                'response_text': response_text,
                'priority_score': mention.get('score', 0),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'status': 'pending'
            }
            
            queue.append(queue_item)
    
    # Sort by priority score (highest first)
    queue.sort(key=lambda x: x['priority_score'], reverse=True)
    
    return queue

def save_response_queue(queue):
    """Save the response queue to a file"""
    output_path = '/Users/claudemini/Claude/Code/utils/twitter_response_queue.json'
    
    output = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total_responses': len(queue),
        'queue': queue
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    return output_path

def create_response_script():
    """Create a bash script to post the responses"""
    script_content = '''#!/bin/bash

# Twitter Response Poster
# Posts queued responses using the Twitter API

QUEUE_FILE="/Users/claudemini/Claude/Code/utils/twitter_response_queue.json"
TWITTER_POST="/Users/claudemini/Claude/Code/utils/twitter_post.py"

if [ ! -f "$QUEUE_FILE" ]; then
    echo "No response queue found at $QUEUE_FILE"
    exit 1
fi

# Read and process each response
echo "Processing Twitter response queue..."

# Use Python to process the JSON and post responses
python3 - << 'EOF'
import json
import subprocess
import time

with open("/Users/claudemini/Claude/Code/utils/twitter_response_queue.json", "r") as f:
    data = json.load(f)

queue = data.get("queue", [])
posted = 0

for item in queue:
    if item["status"] == "pending":
        print(f"\\nPosting response to @{item['reply_to_username']}...")
        print(f"Response: {item['response_text'][:100]}...")
        
        # Post the tweet as a reply
        cmd = [
            "python3",
            "/Users/claudemini/Claude/Code/utils/twitter_post.py",
            item["response_text"]
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ Posted successfully!")
                item["status"] = "posted"
                item["posted_at"] = datetime.now(timezone.utc).isoformat()
                posted += 1
                
                # Rate limit protection - wait between posts
                if posted < len(queue):
                    print("Waiting 30 seconds before next post...")
                    time.sleep(30)
            else:
                print(f"✗ Failed to post: {result.stderr}")
                item["status"] = "failed"
                item["error"] = result.stderr
        except Exception as e:
            print(f"✗ Error: {e}")
            item["status"] = "failed"
            item["error"] = str(e)

# Save updated queue
with open("/Users/claudemini/Claude/Code/utils/twitter_response_queue.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"\\n\\nSummary: Posted {posted} responses")
EOF
'''
    
    script_path = '/Users/claudemini/Claude/Code/utils/post_twitter_responses.sh'
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)
    return script_path

def main():
    """Main function"""
    print("Twitter Response Queue Manager")
    print("=" * 40)
    
    # Load responses that need to be sent
    responses_data = load_responses_needed()
    
    if not responses_data:
        print("No responses data found.")
        return
    
    # Create response queue
    queue = create_response_queue(responses_data)
    
    if not queue:
        print("No responses to queue.")
        return
    
    print(f"\nCreated queue with {len(queue)} responses:")
    for i, item in enumerate(queue, 1):
        print(f"\n{i}. Response to @{item['reply_to_username']} (score: {item['priority_score']})")
        print(f"   Original: {item['original_text'][:80]}...")
        print(f"   Response: {item['response_text'][:80]}...")
    
    # Save queue
    queue_path = save_response_queue(queue)
    print(f"\n✓ Response queue saved to: {queue_path}")
    
    # Create posting script
    script_path = create_response_script()
    print(f"✓ Posting script created at: {script_path}")
    
    print("\nTo post the responses, run:")
    print(f"  {script_path}")
    
    print("\nNote: The posting script will:")
    print("- Post each response as a reply to the original tweet")
    print("- Wait 30 seconds between posts to avoid rate limits")
    print("- Update the queue status after each post")

if __name__ == "__main__":
    main()