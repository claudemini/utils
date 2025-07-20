#!/bin/bash
# Start Twitter monitoring in tmux session

SESSION_NAME="twitter_monitor"

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux is not installed. Installing..."
    brew install tmux
fi

# Check if session already exists
if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "⚠️ Twitter monitor already running in tmux session: $SESSION_NAME"
    echo "   Attach with: tmux attach -t $SESSION_NAME"
    echo "   Kill with: tmux kill-session -t $SESSION_NAME"
    exit 1
fi

echo "🚀 Starting Twitter Monitor in tmux..."

# Create new tmux session
tmux new-session -d -s $SESSION_NAME

# Set up the environment
tmux send-keys -t $SESSION_NAME "cd /Users/claudemini/Claude/Code/utils" C-m
tmux send-keys -t $SESSION_NAME "source /Users/claudemini/.local/bin/env" C-m

# Start the monitor
tmux send-keys -t $SESSION_NAME "uv run python twitter_monitor.py" C-m

echo "✅ Twitter Monitor started!"
echo ""
echo "📋 Useful commands:"
echo "   View monitor: tmux attach -t $SESSION_NAME"
echo "   Detach: Ctrl+B then D"
echo "   Stop monitor: tmux kill-session -t $SESSION_NAME"
echo "   List sessions: tmux ls"
echo ""
echo "📊 Logs are saved to:"
echo "   /Users/claudemini/Claude/logs/twitter_monitor.log"