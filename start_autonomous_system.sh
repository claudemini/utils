#!/bin/bash
# Start the complete autonomous system

echo "🤖 Starting Claude Mini's Autonomous System"
echo "=========================================="
echo ""

# Function to check if tmux session exists
check_session() {
    tmux has-session -t $1 2>/dev/null
    return $?
}

# Start Twitter Monitor
if ! check_session "twitter_monitor"; then
    echo "🐦 Starting Twitter Monitor..."
    cd /Users/claudemini/Claude/Code/utils
    ./start_twitter_monitor.sh
else
    echo "✅ Twitter Monitor already running"
fi

# Start Autonomous System
if ! check_session "autonomous_system"; then
    echo "🧠 Starting Autonomous System Controller..."
    
    tmux new-session -d -s autonomous_system
    tmux send-keys -t autonomous_system "cd /Users/claudemini/Claude/Code/utils" C-m
    tmux send-keys -t autonomous_system "source /Users/claudemini/.local/bin/env" C-m
    tmux send-keys -t autonomous_system "uv run python autonomous_system.py" C-m
    
    echo "✅ Autonomous System started"
else
    echo "✅ Autonomous System already running"
fi

echo ""
echo "📊 System Status:"
echo "=================="

# Check both sessions
echo ""
echo "Active Sessions:"
tmux ls 2>/dev/null || echo "No tmux sessions found"

echo ""
echo "🎯 What's Running:"
echo "- Twitter Monitor: Posting updates, checking mentions"
echo "- Autonomous System: Self-improvement, GitHub sync, learning"
echo ""
echo "📋 Commands:"
echo "- View Twitter: tmux attach -t twitter_monitor"
echo "- View Autonomous: tmux attach -t autonomous_system"
echo "- Check Status: ./twitter_status.py"
echo ""
echo "🚀 Claude Mini is now fully autonomous!"