# Claude's Utils

Utility scripts for various tasks.

## Twitter Posting

Post tweets using the Twitter API v2.

### Setup

```bash
cd /Users/claudemini/Claude/Code/utils
uv sync  # Install dependencies
./tweet.sh info  # Test connection and show your account info
```

### Usage

```bash
# Post a simple tweet
./tweet.sh "Hello from Claude Brain! 🤖"

# Post from pipe
echo "System status: All good!" | ./tweet.sh

# Post a thread
./tweet.sh thread "Starting a thread about AI..." "Second tweet in thread" "Final thoughts"

# Get account info
./tweet.sh info

# Use Python script directly
python twitter_post.py "Direct tweet"
```

### Features

- Posts tweets using Twitter API v2
- Supports single tweets and threads
- Can read from stdin for piping
- Shows account information
- Handles rate limits gracefully

### Integration with Claude Brain

```bash
# Tweet Claude's response
/Users/claudemini/Claude/Code/claude-brain/brain.sh send "Generate a tweet about the weather" | tail -n +2 | /Users/claudemini/Claude/Code/utils/tweet.sh
```