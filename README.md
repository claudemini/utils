# Claude's Utils

Utility scripts for various tasks.

## Task Scheduler

Automated task scheduling system integrated with claude-brain for autonomous activities.

### Setup

```bash
# Initialize database tables
./scheduler.sh init

# The scheduler runs automatically via cron every 5 minutes
# To run manually:
./scheduler.sh run
```

### Usage

```bash
# View active tasks
./scheduler.sh list

# Check recent task executions
./scheduler.sh status

# Run scheduler manually
./scheduler.sh run
```

### Task Categories

- **Daily Routines**: Morning/evening reflections, goal setting, journaling
- **Memory Management**: Pattern analysis, consolidation, learning sessions
- **Social Media**: Scheduled tweets, engagement monitoring
- **Financial Monitoring**: Market analysis, portfolio reviews
- **System Monitoring**: Resource checks, security scans
- **Personality Development**: Trait analysis, goal reviews, skill planning

### Features

- PostgreSQL-based task queue with scheduling
- Integration with claude-brain for context-aware tasks
- Automatic memory storage for significant outputs
- Cron and interval-based scheduling
- Priority-based execution
- Retry logic for failed tasks
- Response parsing from tmux logs

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