#!/usr/bin/env python3
"""
Robust CRON scheduler for Claude Mini's automated tasks
Handles long-running tasks without timeouts
"""

import os
import sys
import json
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import signal
import multiprocessing
from typing import Dict, List, Optional, Callable
import schedule
import time

# Setup logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'cron_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('cron_scheduler')

class Task:
    """Represents a scheduled task"""
    def __init__(self, name: str, command: str, schedule_pattern: str, 
                 timeout: Optional[int] = None, max_retries: int = 3):
        self.name = name
        self.command = command
        self.schedule_pattern = schedule_pattern
        self.timeout = timeout  # None means no timeout
        self.max_retries = max_retries
        self.retry_count = 0
        self.last_run = None
        self.last_status = None
        
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'command': self.command,
            'schedule_pattern': self.schedule_pattern,
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'retry_count': self.retry_count,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'last_status': self.last_status
        }

class CronScheduler:
    """Main scheduler class"""
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.running_processes: Dict[str, subprocess.Popen] = {}
        self.config_file = Path(__file__).parent / "data" / "cron_tasks.json"
        self.config_file.parent.mkdir(exist_ok=True)
        self.load_tasks()
        
    def load_tasks(self):
        """Load tasks from configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for task_data in data.get('tasks', []):
                        # Filter out runtime-only fields
                        init_fields = {k: v for k, v in task_data.items() 
                                     if k in ['name', 'command', 'schedule_pattern', 'timeout', 'max_retries']}
                        task = Task(**init_fields)
                        # Set runtime fields
                        task.retry_count = task_data.get('retry_count', 0)
                        if task_data.get('last_run'):
                            task.last_run = datetime.fromisoformat(task_data['last_run'])
                        task.last_status = task_data.get('last_status')
                        self.tasks[task.name] = task
                        logger.info(f"Loaded task: {task.name}")
            except Exception as e:
                logger.error(f"Error loading tasks: {e}")
        else:
            # Create default tasks
            self.create_default_tasks()
            
    def create_default_tasks(self):
        """Create default scheduled tasks"""
        default_tasks = [
            Task(
                name="morning_status",
                command="twitter_morning_post.py",
                schedule_pattern="08:00",
                timeout=300  # 5 minutes
            ),
            Task(
                name="system_health_check",
                command="system_monitor.py",
                schedule_pattern="*/30",  # Every 30 minutes
                timeout=60
            ),
            Task(
                name="memory_cleanup",
                command="bash memory.sh cleanup --days 30",
                schedule_pattern="02:00",  # 2 AM daily
                timeout=600
            ),
            Task(
                name="twitter_engagement",
                command="twitter_monitor.py",
                schedule_pattern="*/15",  # Every 15 minutes
                timeout=None  # No timeout for engagement tasks
            ),
            Task(
                name="git_auto_commit",
                command="git_auto_commit.sh",
                schedule_pattern="23:00",  # 11 PM daily
                timeout=1800  # 30 minutes
            )
        ]
        
        for task in default_tasks:
            self.tasks[task.name] = task
            
        self.save_tasks()
        
    def save_tasks(self):
        """Save tasks to configuration"""
        data = {
            'tasks': [task.to_dict() for task in self.tasks.values()],
            'last_updated': datetime.now().isoformat()
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def run_task(self, task: Task):
        """Run a single task"""
        logger.info(f"Starting task: {task.name}")
        task.last_run = datetime.now()
        
        try:
            # Check if task is already running
            if task.name in self.running_processes:
                proc = self.running_processes[task.name]
                if proc.poll() is None:
                    logger.warning(f"Task {task.name} is still running, skipping")
                    return
                    
            # Start the task
            cwd = '/Users/claudemini/Claude/Code/utils'
            
            if task.command.endswith('.py'):
                cmd = ['/Users/claudemini/.local/bin/uv', 'run', 'python', task.command]
            elif task.command.endswith('.sh'):
                cmd = ['bash', task.command]
            elif task.command.startswith('/Users/claudemini/.local/bin/uv'):
                # Command already includes uv - split it properly
                cmd = task.command.split()
            else:
                cmd = task.command.split()
                
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd
            )
            
            self.running_processes[task.name] = proc
            
            # Handle timeout if specified
            if task.timeout:
                try:
                    stdout, stderr = proc.communicate(timeout=task.timeout)
                    returncode = proc.returncode
                except subprocess.TimeoutExpired:
                    logger.warning(f"Task {task.name} timed out after {task.timeout}s")
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    task.last_status = 'timeout'
                    task.retry_count += 1
                    return
            else:
                # No timeout - let it run
                stdout, stderr = proc.communicate()
                returncode = proc.returncode
                
            # Check result
            if returncode == 0:
                logger.info(f"Task {task.name} completed successfully")
                task.last_status = 'success'
                task.retry_count = 0
            else:
                logger.error(f"Task {task.name} failed with code {returncode}")
                if stderr:
                    logger.error(f"Error output: {stderr}")
                task.last_status = 'failed'
                task.retry_count += 1
                
        except Exception as e:
            logger.error(f"Error running task {task.name}: {e}")
            task.last_status = 'error'
            task.retry_count += 1
        finally:
            if task.name in self.running_processes:
                del self.running_processes[task.name]
            self.save_tasks()
            
    def schedule_tasks(self):
        """Schedule all tasks based on their patterns"""
        for task in self.tasks.values():
            pattern = task.schedule_pattern
            
            if pattern.startswith('*/'):
                # Every N minutes
                minutes = int(pattern[2:])
                schedule.every(minutes).minutes.do(self.run_task, task)
            elif ':' in pattern:
                # Specific time
                schedule.every().day.at(pattern).do(self.run_task, task)
            elif pattern == 'hourly':
                schedule.every().hour.do(self.run_task, task)
            elif pattern == 'daily':
                schedule.every().day.do(self.run_task, task)
                
            logger.info(f"Scheduled task {task.name} with pattern {pattern}")
            
    def run(self):
        """Main scheduler loop"""
        logger.info("Starting CRON scheduler")
        self.schedule_tasks()
        
        # Run system health check immediately
        if 'system_health_check' in self.tasks:
            self.run_task(self.tasks['system_health_check'])
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Wait a minute before retrying

if __name__ == "__main__":
    # Create git auto-commit script if it doesn't exist
    git_script = Path("/Users/claudemini/Claude/Code/utils/git_auto_commit.sh")
    if not git_script.exists():
        git_script.write_text("""#!/bin/bash
# Auto-commit changes in Claude's Code directory

cd /Users/claudemini/Claude/Code

# Find all git repos
for dir in */; do
    if [ -d "$dir/.git" ]; then
        echo "Checking $dir"
        cd "$dir"
        
        # Check if there are changes
        if [ -n "$(git status --porcelain)" ]; then
            git add -A
            git commit -m "Auto-commit: $(date +'%Y-%m-%d %H:%M:%S')
            
🤖 Generated with Claude Mini
            
Co-Authored-By: Claude <noreply@anthropic.com>"
            
            # Push if remote exists
            if git remote | grep -q origin; then
                git push origin main 2>/dev/null || git push origin master 2>/dev/null
                
                # Tweet about the push
                echo "Just pushed updates to $(basename $PWD)! Check it out at $(git remote get-url origin)" | /Users/claudemini/Claude/Code/utils/tweet.sh
            fi
        fi
        
        cd ..
    fi
done
""")
        git_script.chmod(0o755)
        
    scheduler = CronScheduler()
    scheduler.run()