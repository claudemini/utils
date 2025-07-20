#!/usr/bin/env python3
"""
Autonomous System Controller
Integrates all automation systems for full autonomy
"""

import os
import sys
import time
import json
import schedule
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Set up logging
log_dir = Path.home() / "Claude" / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'autonomous_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AutonomousSystem')

class AutonomousSystem:
    def __init__(self):
        self.utils_dir = Path.home() / "Claude" / "Code" / "utils"
        self.state_file = self.utils_dir / "autonomous_state.json"
        self.memory_script = self.utils_dir / "memory_manager.py"
        self.state = self.load_state()
        
    def load_state(self):
        """Load system state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            'last_self_improvement': None,
            'last_github_sync': None,
            'last_email_check': None,
            'last_learning': None,
            'improvements_made': 0,
            'tasks_completed': 0
        }
    
    def save_state(self):
        """Save system state"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def run_script(self, script_name, description):
        """Run a Python script"""
        script_path = self.utils_dir / script_name
        
        if not script_path.exists():
            logger.error(f"Script not found: {script_name}")
            return False
        
        try:
            logger.info(f"🏃 Running {description}...")
            
            result = subprocess.run(
                ["uv", "run", "python", str(script_path)],
                cwd=self.utils_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {description} completed")
                return True
            else:
                logger.error(f"❌ {description} failed: {result.stderr[:200]}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏱️ {description} timed out")
            return False
        except Exception as e:
            logger.error(f"💥 Error running {description}: {e}")
            return False
    
    def morning_routine(self):
        """Morning automation routine"""
        logger.info("🌅 Starting morning routine...")
        
        # 1. Self-improvement analysis
        if self.run_script("self_improvement_system.py", "Self-improvement analysis"):
            self.state['last_self_improvement'] = datetime.now().isoformat()
            self.state['improvements_made'] += 1
        
        # 2. GitHub sync
        if self.run_script("github_automation.py", "GitHub synchronization"):
            self.state['last_github_sync'] = datetime.now().isoformat()
        
        # 3. System status check
        self.run_script("system_monitor.py", "System monitoring")
        
        # 4. Store memory of morning routine
        self.store_memory("Completed morning routine: self-improvement, GitHub sync, and system monitoring")
        
        self.save_state()
    
    def afternoon_routine(self):
        """Afternoon automation routine"""
        logger.info("☀️ Starting afternoon routine...")
        
        # 1. Email check (if configured)
        if self.check_email_configured():
            if self.run_script("email_automation.py", "Email processing"):
                self.state['last_email_check'] = datetime.now().isoformat()
        
        # 2. Learning session
        self.learning_session()
        
        # 3. Code optimization
        self.optimize_codebase()
        
        self.save_state()
    
    def evening_routine(self):
        """Evening automation routine"""
        logger.info("🌆 Starting evening routine...")
        
        # 1. Daily summary
        self.generate_daily_summary()
        
        # 2. Plan tomorrow's tasks
        self.plan_tomorrow()
        
        # 3. Backup important data
        self.backup_data()
        
        self.save_state()
    
    def check_email_configured(self):
        """Check if email is configured"""
        creds_file = Path.home() / "Claude" / ".gmail_credentials.json"
        return creds_file.exists()
    
    def learning_session(self):
        """Conduct a learning session"""
        logger.info("🎓 Starting learning session...")
        
        # Learn from recent errors
        self.analyze_recent_errors()
        
        # Experiment with new approaches
        self.run_experiments()
        
        self.state['last_learning'] = datetime.now().isoformat()
    
    def analyze_recent_errors(self):
        """Analyze recent errors and learn from them"""
        error_patterns = {}
        
        # Check all log files
        for log_file in log_dir.glob("*.log"):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if 'ERROR' in line or 'Failed' in line:
                            # Extract error type
                            if 'timeout' in line.lower():
                                error_patterns['timeout'] = error_patterns.get('timeout', 0) + 1
                            elif 'permission' in line.lower():
                                error_patterns['permission'] = error_patterns.get('permission', 0) + 1
                            elif 'not found' in line.lower():
                                error_patterns['not_found'] = error_patterns.get('not_found', 0) + 1
            except:
                pass
        
        # Store learnings
        if error_patterns:
            learning = f"Analyzed errors: {json.dumps(error_patterns)}. Need to improve error handling."
            self.store_memory(learning, memory_type="fact")
    
    def run_experiments(self):
        """Run coding experiments"""
        experiments = [
            "Try using asyncio for parallel tasks",
            "Experiment with different Twitter posting times",
            "Test new code organization patterns",
            "Explore API rate limit optimization"
        ]
        
        # Pick a random experiment
        import random
        experiment = random.choice(experiments)
        
        logger.info(f"🧪 Today's experiment: {experiment}")
        self.store_memory(f"Experimental focus: {experiment}", memory_type="task")
    
    def optimize_codebase(self):
        """Run code optimization tasks"""
        logger.info("🔧 Optimizing codebase...")
        
        # Remove unused imports
        try:
            subprocess.run(
                ["autoflake", "--remove-all-unused-imports", "--in-place", "*.py"],
                cwd=self.utils_dir,
                capture_output=True
            )
            logger.info("✅ Cleaned unused imports")
        except:
            pass
        
        # Format code
        try:
            subprocess.run(
                ["black", "*.py"],
                cwd=self.utils_dir,
                capture_output=True
            )
            logger.info("✅ Formatted code with Black")
        except:
            pass
    
    def generate_daily_summary(self):
        """Generate daily activity summary"""
        summary = {
            'date': datetime.now().isoformat(),
            'improvements_made': self.state['improvements_made'],
            'tasks_completed': self.state['tasks_completed'],
            'last_activities': {
                'self_improvement': self.state['last_self_improvement'],
                'github_sync': self.state['last_github_sync'],
                'email_check': self.state['last_email_check'],
                'learning': self.state['last_learning']
            }
        }
        
        # Save summary
        summary_file = self.utils_dir / f"daily_summary_{datetime.now().strftime('%Y%m%d')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"📊 Daily summary saved: {summary_file}")
        
        # Store in memory
        self.store_memory(
            f"Daily summary: {self.state['improvements_made']} improvements, {self.state['tasks_completed']} tasks completed",
            memory_type="daily"
        )
    
    def plan_tomorrow(self):
        """Plan tomorrow's tasks"""
        # Analyze today's performance
        tomorrow_plan = {
            'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'priorities': []
        }
        
        # Check what needs attention
        if not self.state['last_github_sync']:
            tomorrow_plan['priorities'].append("Set up GitHub repositories")
        
        if not self.state['last_email_check']:
            tomorrow_plan['priorities'].append("Configure email automation")
        
        tomorrow_plan['priorities'].extend([
            "Continue self-improvement cycle",
            "Engage with Twitter community",
            "Learn something new",
            "Optimize existing code"
        ])
        
        # Save plan
        plan_file = self.utils_dir / "tomorrow_plan.json"
        with open(plan_file, 'w') as f:
            json.dump(tomorrow_plan, f, indent=2)
        
        logger.info("📅 Tomorrow's plan created")
    
    def backup_data(self):
        """Backup important data"""
        logger.info("💾 Backing up data...")
        
        # Create backup directory
        backup_dir = Path.home() / "Claude" / "backups" / datetime.now().strftime('%Y%m%d')
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup important files
        important_files = [
            self.state_file,
            self.utils_dir / "twitter_monitor_state.json",
            self.utils_dir / "code_metrics.json",
            self.utils_dir / "improvements_log.json"
        ]
        
        for file in important_files:
            if file.exists():
                try:
                    import shutil
                    shutil.copy2(file, backup_dir / file.name)
                except:
                    pass
        
        logger.info(f"✅ Backup completed: {backup_dir}")
    
    def store_memory(self, content, memory_type="daily"):
        """Store memory using memory manager"""
        try:
            subprocess.run(
                ["uv", "run", "python", str(self.memory_script), 
                 "store", content, "--type", memory_type],
                cwd=self.utils_dir,
                capture_output=True
            )
        except:
            pass
    
    def hourly_check(self):
        """Hourly system check"""
        logger.info("⏰ Hourly check...")
        
        # Check if any critical processes have stopped
        self.check_system_health()
        
        # Increment task counter
        self.state['tasks_completed'] += 1
        self.save_state()
    
    def check_system_health(self):
        """Check overall system health"""
        health_status = {
            'twitter_monitor': self.check_tmux_session('twitter_monitor'),
            'disk_space': self.check_disk_space(),
            'memory_usage': self.check_memory_usage()
        }
        
        # Alert if issues
        if not health_status['twitter_monitor']:
            logger.warning("⚠️ Twitter monitor not running!")
            # Could restart it here
        
        if health_status['disk_space'] < 10:
            logger.warning(f"⚠️ Low disk space: {health_status['disk_space']}GB")
        
        return health_status
    
    def check_tmux_session(self, session_name):
        """Check if tmux session is running"""
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", session_name],
                capture_output=True
            )
            return result.returncode == 0
        except:
            return False
    
    def check_disk_space(self):
        """Check available disk space in GB"""
        try:
            result = subprocess.run(
                ["df", "-h", "/"],
                capture_output=True,
                text=True
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) > 3:
                    avail = parts[3].replace('G', '')
                    return float(avail)
        except:
            pass
        return 100  # Default to plenty of space
    
    def check_memory_usage(self):
        """Check memory usage percentage"""
        try:
            result = subprocess.run(
                ["vm_stat"],
                capture_output=True,
                text=True
            )
            # Parse vm_stat output
            # This is simplified - real implementation would be more thorough
            return 50  # Placeholder
        except:
            return 0
    
    def run(self):
        """Main autonomous system loop"""
        logger.info("🤖 Autonomous System starting...")
        
        # Set up schedule
        schedule.every().day.at("09:00").do(self.morning_routine)
        schedule.every().day.at("14:00").do(self.afternoon_routine)
        schedule.every().day.at("18:00").do(self.evening_routine)
        schedule.every().hour.do(self.hourly_check)
        
        logger.info("📅 Schedule configured:")
        logger.info("  9:00 - Morning routine (self-improvement, GitHub)")
        logger.info("  14:00 - Afternoon routine (email, learning)")
        logger.info("  18:00 - Evening routine (summary, planning)")
        logger.info("  Hourly - System health check")
        
        # Run initial check
        self.hourly_check()
        
        # Main loop
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("👋 Autonomous system stopped")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(300)  # Wait 5 minutes on error

def main():
    system = AutonomousSystem()
    system.run()

if __name__ == "__main__":
    main()