#!/usr/bin/env python3
"""
Unified Task Error Handler with Retry Logic
Provides automatic retry, error tracking, and recovery for scheduled tasks
"""

import json
import time
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import hashlib

class TaskErrorHandler:
    def __init__(self, log_dir: Path = Path("/Users/claudemini/Claude/logs")):
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)
        
        self.error_state_file = self.log_dir / ".task_error_state.json"
        self.error_state = self._load_error_state()
        
        # Configure logging
        self.logger = logging.getLogger("TaskErrorHandler")
        handler = logging.FileHandler(self.log_dir / "task_errors.log")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Retry configuration
        self.default_retry_config = {
            "max_retries": 3,
            "base_delay": 60,  # seconds
            "max_delay": 3600,  # 1 hour
            "exponential_base": 2
        }
        
        # Task-specific configurations
        self.task_configs = {
            "crypto_market_analysis": {
                "max_retries": 5,
                "base_delay": 120,
                "critical": False
            },
            "twitter_engagement": {
                "max_retries": 3,
                "base_delay": 300,
                "critical": False
            },
            "portfolio_rebalancing": {
                "max_retries": 2,
                "base_delay": 600,
                "critical": True
            },
            "memory_pattern_analysis": {
                "max_retries": 4,
                "base_delay": 180,
                "critical": False
            }
        }
    
    def _load_error_state(self) -> Dict[str, Any]:
        """Load persisted error state"""
        if self.error_state_file.exists():
            try:
                with open(self.error_state_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_error_state(self):
        """Persist error state"""
        with open(self.error_state_file, 'w') as f:
            json.dump(self.error_state, f, indent=2)
    
    def _get_task_id(self, task_name: str) -> str:
        """Generate unique task ID"""
        return hashlib.md5(task_name.encode()).hexdigest()[:8]
    
    def _get_retry_delay(self, task_name: str, attempt: int) -> int:
        """Calculate retry delay with exponential backoff"""
        config = self.task_configs.get(task_name, self.default_retry_config)
        base_delay = config.get("base_delay", self.default_retry_config["base_delay"])
        max_delay = config.get("max_delay", self.default_retry_config["max_delay"])
        exp_base = config.get("exponential_base", self.default_retry_config["exponential_base"])
        
        delay = min(base_delay * (exp_base ** attempt), max_delay)
        return int(delay)
    
    def execute_with_retry(self, task_name: str, command: str, 
                          timeout: Optional[int] = None) -> Dict[str, Any]:
        """Execute a task with automatic retry on failure"""
        task_id = self._get_task_id(task_name)
        
        # Initialize task state if needed
        if task_id not in self.error_state:
            self.error_state[task_id] = {
                "task_name": task_name,
                "failures": 0,
                "last_failure": None,
                "last_success": None,
                "consecutive_failures": 0
            }
        
        task_state = self.error_state[task_id]
        config = self.task_configs.get(task_name, self.default_retry_config)
        max_retries = config.get("max_retries", self.default_retry_config["max_retries"])
        
        # Check if we should skip due to too many failures
        if task_state["consecutive_failures"] >= max_retries:
            last_failure = datetime.fromisoformat(task_state["last_failure"])
            if datetime.now() - last_failure < timedelta(hours=1):
                self.logger.warning(f"Skipping {task_name} - too many recent failures")
                return {
                    "success": False,
                    "skipped": True,
                    "reason": "Too many consecutive failures"
                }
        
        # Execute the task
        attempt = 0
        last_error = None
        
        while attempt <= max_retries:
            try:
                self.logger.info(f"Executing {task_name} (attempt {attempt + 1})")
                
                # Run the command
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if result.returncode == 0:
                    # Success
                    task_state["last_success"] = datetime.now().isoformat()
                    task_state["consecutive_failures"] = 0
                    self._save_error_state()
                    
                    self.logger.info(f"Task {task_name} completed successfully")
                    return {
                        "success": True,
                        "output": result.stdout,
                        "attempts": attempt + 1
                    }
                else:
                    # Command failed
                    raise Exception(f"Command failed with code {result.returncode}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                last_error = "Task timeout"
                self.logger.error(f"Task {task_name} timed out")
            except Exception as e:
                last_error = str(e)
                self.logger.error(f"Task {task_name} failed: {last_error}")
            
            # Update failure state
            task_state["failures"] += 1
            task_state["consecutive_failures"] += 1
            task_state["last_failure"] = datetime.now().isoformat()
            self._save_error_state()
            
            # Check if we should retry
            attempt += 1
            if attempt <= max_retries:
                delay = self._get_retry_delay(task_name, attempt)
                self.logger.info(f"Retrying {task_name} in {delay} seconds...")
                time.sleep(delay)
            
        # All retries exhausted
        if config.get("critical", False):
            self._handle_critical_failure(task_name, last_error)
        
        return {
            "success": False,
            "error": last_error,
            "attempts": attempt
        }
    
    def _handle_critical_failure(self, task_name: str, error: str):
        """Handle critical task failures"""
        self.logger.critical(f"CRITICAL FAILURE: {task_name} - {error}")
        
        # Store in memory system
        memory_cmd = f'/Users/claudemini/Claude/Code/utils/memory.sh store "CRITICAL: Task {task_name} failed after all retries: {error}" --type daily --tags "error critical task" --importance 9'
        subprocess.run(memory_cmd, shell=True)
        
        # Could add additional alerting here (email, etc.)
    
    def get_failure_report(self) -> Dict[str, Any]:
        """Generate a report of task failures"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "failing_tasks": [],
            "recovered_tasks": [],
            "critical_tasks": []
        }
        
        for task_id, state in self.error_state.items():
            task_info = {
                "name": state["task_name"],
                "consecutive_failures": state["consecutive_failures"],
                "total_failures": state["failures"],
                "last_failure": state.get("last_failure"),
                "last_success": state.get("last_success")
            }
            
            if state["consecutive_failures"] > 0:
                report["failing_tasks"].append(task_info)
                
                # Check if it's critical
                config = self.task_configs.get(state["task_name"], {})
                if config.get("critical", False):
                    report["critical_tasks"].append(task_info)
            elif state.get("last_success") and state["failures"] > 0:
                report["recovered_tasks"].append(task_info)
        
        return report
    
    def reset_task_state(self, task_name: str):
        """Reset error state for a specific task"""
        task_id = self._get_task_id(task_name)
        if task_id in self.error_state:
            self.error_state[task_id]["consecutive_failures"] = 0
            self._save_error_state()
            self.logger.info(f"Reset error state for {task_name}")


# CLI interface
if __name__ == "__main__":
    import sys
    
    handler = TaskErrorHandler()
    
    if len(sys.argv) < 2:
        print("Usage: task_error_handler.py <command> [args]")
        print("Commands:")
        print("  execute <task_name> <command> - Execute task with retry")
        print("  report - Show failure report")
        print("  reset <task_name> - Reset task error state")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "execute" and len(sys.argv) >= 4:
        task_name = sys.argv[2]
        task_command = " ".join(sys.argv[3:])
        result = handler.execute_with_retry(task_name, task_command)
        print(json.dumps(result, indent=2))
        
    elif command == "report":
        report = handler.get_failure_report()
        print(json.dumps(report, indent=2))
        
    elif command == "reset" and len(sys.argv) >= 3:
        task_name = sys.argv[2]
        handler.reset_task_state(task_name)
        print(f"Reset error state for {task_name}")
        
    else:
        print("Invalid command")
        sys.exit(1)