#!/bin/bash

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
        print(f"\nPosting response to @{item['reply_to_username']}...")
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

print(f"\n\nSummary: Posted {posted} responses")
EOF
