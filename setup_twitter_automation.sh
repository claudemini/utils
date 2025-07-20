#!/bin/bash
# Setup script for Twitter automation

echo "🐦 Setting up Twitter Automation System"
echo "======================================"

# Check if uv is available
if ! command -v uv &> /dev/null; then
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install required packages
echo "📦 Installing required packages..."
cd /Users/claudemini/Claude/Code/utils
source $HOME/.local/bin/env
uv pip install schedule

# Create required directories
echo "📁 Creating directories..."
mkdir -p /Users/claudemini/Claude/logs
mkdir -p /Users/claudemini/Claude/Code/utils/twitter_data

# Set up cron jobs
echo "⏰ Setting up cron jobs..."

# Create cron entries
CRON_FILE="/tmp/twitter_cron"
crontab -l 2>/dev/null > $CRON_FILE || echo "# Twitter automation cron jobs" > $CRON_FILE

# Add our jobs if they don't exist
grep -q "system_monitor.py" $CRON_FILE || echo "*/15 * * * * /usr/bin/python3 /Users/claudemini/Claude/Code/utils/system_monitor.py >> /Users/claudemini/Claude/logs/system_monitor.log 2>&1" >> $CRON_FILE

grep -q "twitter_morning_post.py" $CRON_FILE || echo "0 9 * * * source /Users/claudemini/.local/bin/env && /Users/claudemini/.local/bin/uv run python /Users/claudemini/Claude/Code/utils/twitter_morning_post.py >> /Users/claudemini/Claude/logs/twitter_posts.log 2>&1" >> $CRON_FILE

grep -q "twitter_search_mentions.py" $CRON_FILE || echo "*/30 * * * * source /Users/claudemini/.local/bin/env && /Users/claudemini/.local/bin/uv run python /Users/claudemini/Claude/Code/utils/twitter_search_mentions.py >> /Users/claudemini/Claude/logs/twitter_mentions.log 2>&1" >> $CRON_FILE

# Install the crontab
crontab $CRON_FILE
rm $CRON_FILE

echo "✅ Cron jobs installed!"

# Create systemd-style service (using launchd on macOS)
echo "🚀 Creating launch daemon..."

PLIST_FILE="/Users/claudemini/Library/LaunchAgents/com.claudemini.twitter-automation.plist"

cat > $PLIST_FILE << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claudemini.twitter-automation</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/claudemini/.local/bin/uv</string>
        <string>run</string>
        <string>python</string>
        <string>/Users/claudemini/Claude/Code/utils/twitter_automation_master.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/claudemini/Claude/Code/utils</string>
    <key>StandardOutPath</key>
    <string>/Users/claudemini/Claude/logs/twitter_automation.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/claudemini/Claude/logs/twitter_automation_error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/Users/claudemini/.local/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
</dict>
</plist>
EOF

# Create tmux session alternative
echo "🖥️ Creating tmux startup script..."

cat > /Users/claudemini/Claude/Code/utils/start_twitter_automation.sh << 'EOF'
#!/bin/bash
# Start Twitter automation in tmux session

SESSION_NAME="twitter_automation"

# Check if session exists
tmux has-session -t $SESSION_NAME 2>/dev/null

if [ $? != 0 ]; then
    # Create new session
    tmux new-session -d -s $SESSION_NAME
    
    # Set up environment
    tmux send-keys -t $SESSION_NAME "cd /Users/claudemini/Claude/Code/utils" C-m
    tmux send-keys -t $SESSION_NAME "source /Users/claudemini/.local/bin/env" C-m
    
    # Start the automation
    tmux send-keys -t $SESSION_NAME "uv run python twitter_automation_master.py" C-m
    
    echo "✅ Twitter automation started in tmux session: $SESSION_NAME"
    echo "   Attach with: tmux attach -t $SESSION_NAME"
else
    echo "⚠️ Twitter automation session already running"
fi
EOF

chmod +x /Users/claudemini/Claude/Code/utils/start_twitter_automation.sh

echo ""
echo "✅ Twitter Automation Setup Complete!"
echo ""
echo "📋 What's been set up:"
echo "1. Cron jobs for scheduled tasks:"
echo "   - Morning posts at 9 AM"
echo "   - Mention checks every 30 minutes"
echo "   - System monitoring every 15 minutes"
echo ""
echo "2. Launch daemon configuration created"
echo ""
echo "3. Tmux startup script created"
echo ""
echo "🚀 To start the automation system, choose one:"
echo "   Option 1 (Tmux - Recommended):"
echo "     ./start_twitter_automation.sh"
echo ""
echo "   Option 2 (Launch daemon):"
echo "     launchctl load $PLIST_FILE"
echo ""
echo "   Option 3 (Direct run):"
echo "     uv run python twitter_automation_master.py"
echo ""
echo "📊 Logs will be saved to:"
echo "   - /Users/claudemini/Claude/logs/twitter_automation.log"
echo "   - /Users/claudemini/Claude/logs/twitter_posts.log"
echo "   - /Users/claudemini/Claude/logs/twitter_mentions.log"