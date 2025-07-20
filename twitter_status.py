#!/usr/bin/env python3
"""
Check Twitter automation status
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

def check_tmux_session():
    """Check if twitter_monitor session is running"""
    try:
        result = subprocess.run(
            ["tmux", "has-session", "-t", "twitter_monitor"],
            capture_output=True
        )
        return result.returncode == 0
    except:
        return False

def get_monitor_state():
    """Get the last known monitor state"""
    state_file = Path.home() / "Claude" / "Code" / "utils" / "twitter_monitor_state.json"
    if state_file.exists():
        with open(state_file, "r") as f:
            return json.load(f)
    return None

def check_recent_logs():
    """Check recent log entries"""
    log_file = Path.home() / "Claude" / "logs" / "twitter_monitor.log"
    if log_file.exists():
        # Get last 5 lines
        with open(log_file, "r") as f:
            lines = f.readlines()
            return lines[-5:] if len(lines) >= 5 else lines
    return []

def main():
    print("🐦 Twitter Automation Status")
    print("=" * 40)
    
    # Check if monitor is running
    if check_tmux_session():
        print("✅ Monitor: RUNNING in tmux session")
        print("   View with: tmux attach -t twitter_monitor")
    else:
        print("❌ Monitor: NOT RUNNING")
        print("   Start with: ./start_twitter_monitor.sh")
    
    print()
    
    # Check state
    state = get_monitor_state()
    if state:
        print("📊 Last Activities:")
        if state.get("last_morning_post"):
            last_morning = datetime.fromisoformat(state["last_morning_post"])
            print(f"   Morning post: {last_morning.strftime('%Y-%m-%d %H:%M')}")
        if state.get("last_mention_check"):
            last_mention = datetime.fromisoformat(state["last_mention_check"])
            print(f"   Mention check: {last_mention.strftime('%Y-%m-%d %H:%M')}")
    
    print()
    
    # Check recent logs
    recent_logs = check_recent_logs()
    if recent_logs:
        print("📋 Recent Log Entries:")
        for line in recent_logs:
            print(f"   {line.strip()}")
    
    print()
    print("📁 Log locations:")
    print("   Monitor: ~/Claude/logs/twitter_monitor.log")
    print("   Posts: ~/Claude/logs/twitter_posts.log")
    print("   Mentions: ~/Claude/logs/twitter_mentions.log")

if __name__ == "__main__":
    main()