#!/usr/bin/env python3
"""
Twitter Automation Master Controller
Orchestrates all Twitter automation tasks
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import schedule
import logging

# Set up logging
log_dir = Path.home() / "Claude" / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'twitter_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TwitterAutomation')

# Base directory for scripts
UTILS_DIR = Path.home() / "Claude" / "Code" / "utils"
UV_PATH = Path.home() / ".local" / "bin" / "uv"

class TwitterAutomation:
    def __init__(self):
        self.last_runs = {}
        self.error_count = {}
        
    def run_script(self, script_name, description):
        """Run a Python script with error handling"""
        script_path = UTILS_DIR / script_name
        
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return False
            
        try:
            logger.info(f"Running {description}...")
            
            # Set up environment
            env = os.environ.copy()
            env['PATH'] = f"{Path.home() / '.local' / 'bin'}:{env['PATH']}"
            
            # Run the script
            result = subprocess.run(
                [str(UV_PATH), "run", "python", str(script_path)],
                cwd=UTILS_DIR,
                capture_output=True,
                text=True,
                env=env,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {description} completed successfully")
                self.last_runs[script_name] = datetime.now()
                self.error_count[script_name] = 0
                return True
            else:
                logger.error(f"❌ {description} failed: {result.stderr}")
                self.error_count[script_name] = self.error_count.get(script_name, 0) + 1
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏱️ {description} timed out")
            self.error_count[script_name] = self.error_count.get(script_name, 0) + 1
            return False
        except Exception as e:
            logger.error(f"💥 Error running {description}: {e}")
            self.error_count[script_name] = self.error_count.get(script_name, 0) + 1
            return False
    
    def morning_routine(self):
        """Morning automation tasks (9 AM)"""
        logger.info("🌅 Starting morning routine")
        
        # Post morning status update
        self.run_script("twitter_morning_post.py", "Morning status post")
        
        # Check overnight mentions
        time.sleep(30)  # Rate limit pause
        self.run_script("twitter_search_mentions.py", "Check mentions")
        
    def afternoon_routine(self):
        """Afternoon automation tasks (2 PM)"""
        logger.info("☀️ Starting afternoon routine")
        
        # Post technical content (need to create this)
        # self.run_script("twitter_technical_post.py", "Technical content post")
        
        # Discover new accounts
        self.run_script("twitter_account_discovery.py", "Account discovery")
        
    def evening_routine(self):
        """Evening automation tasks (6 PM)"""
        logger.info("🌆 Starting evening routine")
        
        # Check and respond to mentions
        self.run_script("twitter_search_mentions.py", "Evening mention check")
        
        # Generate interaction report
        self.generate_daily_report()
        
    def hourly_routine(self):
        """Hourly automation tasks"""
        logger.info("⏰ Running hourly checks")
        
        # Quick mention check (lighter than full search)
        # Could implement a quick_mention_check.py if needed
        
    def generate_daily_report(self):
        """Generate daily Twitter activity report"""
        try:
            report = {
                "date": datetime.now().isoformat(),
                "scripts_run": len(self.last_runs),
                "errors": sum(self.error_count.values()),
                "last_runs": {k: v.isoformat() for k, v in self.last_runs.items()},
                "error_details": self.error_count
            }
            
            report_file = UTILS_DIR / f"twitter_report_{datetime.now().strftime('%Y%m%d')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
                
            logger.info(f"📊 Daily report saved: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
    
    def health_check(self):
        """Check system health and alert if issues"""
        # Check for too many errors
        for script, count in self.error_count.items():
            if count >= 3:
                logger.warning(f"⚠️ {script} has failed {count} times today")
                
        # Check if scripts are running
        now = datetime.now()
        for script, last_run in self.last_runs.items():
            if now - last_run > timedelta(hours=24):
                logger.warning(f"⚠️ {script} hasn't run in over 24 hours")

def main():
    """Main automation loop"""
    automation = TwitterAutomation()
    
    # Set up schedule
    schedule.every().day.at("09:00").do(automation.morning_routine)
    schedule.every().day.at("14:00").do(automation.afternoon_routine)
    schedule.every().day.at("18:00").do(automation.evening_routine)
    schedule.every().hour.do(automation.hourly_routine)
    schedule.every().day.at("23:00").do(automation.generate_daily_report)
    schedule.every(6).hours.do(automation.health_check)
    
    logger.info("🚀 Twitter Automation Master started")
    logger.info("📅 Schedule:")
    logger.info("  - 9:00 AM: Morning routine (status post, check mentions)")
    logger.info("  - 2:00 PM: Afternoon routine (technical content, discovery)")
    logger.info("  - 6:00 PM: Evening routine (mentions, daily report)")
    logger.info("  - Hourly: Quick checks")
    logger.info("  - 11:00 PM: Generate daily report")
    
    # Run initial tasks
    automation.morning_routine()
    
    # Keep running
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("👋 Automation stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(300)  # Wait 5 minutes on error

if __name__ == "__main__":
    main()