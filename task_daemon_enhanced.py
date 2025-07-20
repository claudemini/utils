#!/usr/bin/env python3
"""
Enhanced Task Daemon - Integrates unified error handler with task execution
"""

import subprocess
import sys
import json
from pathlib import Path
from task_error_handler import TaskErrorHandler

class EnhancedTaskExecutor:
    def __init__(self):
        self.error_handler = TaskErrorHandler()
        
    def execute_task(self, task_name: str, command: str, timeout: int = 300):
        """Execute a task using the error handler with retry logic"""
        # Use the error handler for automatic retry
        result = self.error_handler.execute_with_retry(
            task_name=task_name,
            command=command,
            timeout=timeout
        )
        
        return result
    
    def wrap_claude_command(self, prompt: str) -> str:
        """Wrap a Claude prompt in the proper command format"""
        # Escape single quotes in the prompt
        escaped_prompt = prompt.replace("'", "'\"'\"'")
        return f"claude --dangerously-skip-permissions -p '{escaped_prompt}'"
    
    def wrap_bash_command(self, command: str) -> str:
        """Ensure bash command is properly formatted"""
        return command

# CLI wrapper for cron jobs
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: task_daemon_enhanced.py <task_name> <command_type> [command/prompt]")
        print("Command types: claude, bash")
        sys.exit(1)
    
    task_name = sys.argv[1]
    command_type = sys.argv[2]
    
    executor = EnhancedTaskExecutor()
    
    if command_type == "claude" and len(sys.argv) >= 4:
        prompt = " ".join(sys.argv[3:])
        command = executor.wrap_claude_command(prompt)
    elif command_type == "bash" and len(sys.argv) >= 4:
        command = " ".join(sys.argv[3:])
    else:
        print("Invalid command type or missing command")
        sys.exit(1)
    
    # Execute with retry logic
    result = executor.execute_task(task_name, command)
    
    # Print result as JSON
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result.get("success", False) else 1)