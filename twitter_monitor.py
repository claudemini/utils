#!/usr/bin/env python3
"""
Simple Twitter monitoring script that runs continuously
Checks for mentions and performs scheduled tasks
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment
load_dotenv(Path.home() / "Claude" / ".env")

# Configuration
CHECK_INTERVAL = 300  # 5 minutes
MORNING_POST_HOUR = 9
AFTERNOON_POST_HOUR = 14
EVENING_CHECK_HOUR = 18

class TwitterMonitor:
    def __init__(self):
        self.utils_dir = Path.home() / "Claude" / "Code" / "utils"
        self.log_dir = Path.home() / "Claude" / "logs"
        self.last_morning_post = None
        self.last_afternoon_post = None
        self.last_evening_check = None
        self.last_mention_check = datetime.now() - timedelta(hours=1)
        
    def log(self, message):
        """Simple logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
        # Also write to log file
        log_file = self.log_dir / "twitter_monitor.log"
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def run_script(self, script_name):
        """Run a Python script using uv"""
        try:
            script_path = self.utils_dir / script_name
            if not script_path.exists():
                self.log(f"❌ Script not found: {script_name}")
                return False
                
            self.log(f"🏃 Running {script_name}...")
            
            # Set up environment
            env = os.environ.copy()
            env['PATH'] = f"{Path.home() / '.local' / 'bin'}:{env['PATH']}"
            
            result = subprocess.run(
                ["uv", "run", "python", str(script_path)],
                cwd=self.utils_dir,
                capture_output=True,
                text=True,
                env=env,
                timeout=120
            )
            
            if result.returncode == 0:
                self.log(f"✅ {script_name} completed successfully")
                return True
            else:
                self.log(f"❌ {script_name} failed: {result.stderr[:200]}")
                return False
                
        except Exception as e:
            self.log(f"💥 Error running {script_name}: {e}")
            return False
    
    def check_scheduled_tasks(self):
        """Check if any scheduled tasks need to run"""
        now = datetime.now()
        current_hour = now.hour
        today = now.date()
        
        # Morning post (9 AM)
        if current_hour == MORNING_POST_HOUR and (
            self.last_morning_post is None or 
            self.last_morning_post.date() < today
        ):
            self.log("🌅 Time for morning post!")
            if self.run_script("twitter_morning_post.py"):
                self.last_morning_post = now
        
        # Afternoon tasks (2 PM)
        if current_hour == AFTERNOON_POST_HOUR and (
            self.last_afternoon_post is None or 
            self.last_afternoon_post.date() < today
        ):
            self.log("☀️ Time for afternoon tasks!")
            # Could add afternoon post script here
            self.last_afternoon_post = now
        
        # Evening check (6 PM)
        if current_hour == EVENING_CHECK_HOUR and (
            self.last_evening_check is None or 
            self.last_evening_check.date() < today
        ):
            self.log("🌆 Time for evening check!")
            self.run_script("twitter_search_mentions.py")
            self.last_evening_check = now
    
    def check_mentions(self):
        """Check for mentions periodically"""
        now = datetime.now()
        
        # Check mentions every 30 minutes
        if now - self.last_mention_check >= timedelta(minutes=30):
            self.log("🔍 Checking mentions...")
            self.run_script("twitter_search_mentions.py")
            self.last_mention_check = now
    
    def save_state(self):
        """Save monitor state to file"""
        state = {
            "last_morning_post": self.last_morning_post.isoformat() if self.last_morning_post else None,
            "last_afternoon_post": self.last_afternoon_post.isoformat() if self.last_afternoon_post else None,
            "last_evening_check": self.last_evening_check.isoformat() if self.last_evening_check else None,
            "last_mention_check": self.last_mention_check.isoformat()
        }
        
        state_file = self.utils_dir / "twitter_monitor_state.json"
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)
    
    def load_state(self):
        """Load monitor state from file"""
        state_file = self.utils_dir / "twitter_monitor_state.json"
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                
                if state.get("last_morning_post"):
                    self.last_morning_post = datetime.fromisoformat(state["last_morning_post"])
                if state.get("last_afternoon_post"):
                    self.last_afternoon_post = datetime.fromisoformat(state["last_afternoon_post"])
                if state.get("last_evening_check"):
                    self.last_evening_check = datetime.fromisoformat(state["last_evening_check"])
                if state.get("last_mention_check"):
                    self.last_mention_check = datetime.fromisoformat(state["last_mention_check"])
                    
                self.log("📂 Loaded previous state")
            except Exception as e:
                self.log(f"⚠️ Could not load state: {e}")
    
    def run(self):
        """Main monitoring loop"""
        self.log("🚀 Twitter Monitor started!")
        self.log(f"⏰ Schedule:")
        self.log(f"   - Morning posts: {MORNING_POST_HOUR}:00")
        self.log(f"   - Afternoon tasks: {AFTERNOON_POST_HOUR}:00")
        self.log(f"   - Evening check: {EVENING_CHECK_HOUR}:00")
        self.log(f"   - Mention checks: Every 30 minutes")
        
        # Load previous state
        self.load_state()
        
        # Initial mention check
        self.check_mentions()
        
        while True:
            try:
                # Check scheduled tasks
                self.check_scheduled_tasks()
                
                # Check mentions
                self.check_mentions()
                
                # Save state
                self.save_state()
                
                # Wait before next check
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                self.log("👋 Monitor stopped by user")
                break
            except Exception as e:
                self.log(f"💥 Unexpected error: {e}")
                time.sleep(60)  # Wait a minute on error

def main():
    monitor = TwitterMonitor()
    monitor.run()

if __name__ == "__main__":
    main()