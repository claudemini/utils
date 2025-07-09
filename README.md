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

## Memory Manager

Store and search memories using PostgreSQL with vector embeddings.

### Setup

The memory system is already initialized with core memories from CLAUDE.md.

### Usage

```bash
# Store a new memory
./memory.sh store "The user prefers dark mode interfaces" --type preference --tags ui dark-mode --importance 7

# Search memories semantically
./memory.sh search "What are my coding preferences?"

# List memories by type
./memory.sh list --type core
./memory.sh list --type preference

# Filter by tags
./memory.sh list --tags python development

# View statistics
./memory.sh stats
```

### Memory Types

- **core**: Fundamental identity and system configuration
- **fact**: Known facts and information
- **instruction**: Rules and guidelines
- **preference**: User or system preferences
- **conversation**: Past conversation context
- **task**: Task-related memories
- **relationship**: Information about people

### Features

- Semantic search using sentence-transformers (all-MiniLM-L6-v2)
- Vector similarity search with pgvector
- Importance levels (1-10)
- Tag-based categorization
- Access tracking and timestamps
- Soft delete support
