#!/bin/bash

# Start the CRON scheduler in a tmux session

SESSION_NAME="claude_scheduler"

# Kill existing session if it exists
tmux kill-session -t $SESSION_NAME 2>/dev/null

# Create new session
tmux new-session -d -s $SESSION_NAME

# Run the scheduler
tmux send-keys -t $SESSION_NAME "cd /Users/claudemini/Claude/Code/utils" C-m
tmux send-keys -t $SESSION_NAME "/Users/claudemini/.local/bin/uv run python cron_scheduler.py" C-m

echo "CRON scheduler started in tmux session: $SESSION_NAME"
echo "To view: tmux attach -t $SESSION_NAME"
echo "To stop: tmux kill-session -t $SESSION_NAME"