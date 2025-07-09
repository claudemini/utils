#!/usr/bin/env python3

"""
Claude Executor for Task Automation
Handles execution of tasks using claude CLI or brain.sh
"""

import subprocess
import os
import time
import tempfile
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import signal
from pathlib import Path

# Add utils directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from response_parser import ResponseParser
from memory_manager import MemoryManager

class ClaudeExecutor:
    def __init__(self):
        self.parser = ResponseParser()
        self.memory_manager = MemoryManager()
        self.brain_path = "/Users/claudemini/Claude/Code/claude-brain/brain.sh"
        self.claude_home = "/Users/claudemini/Claude"
        
        # Database connection
        self.conn = psycopg2.connect(
            dbname="claudemini",
            user="claudemini",
            host="localhost"
        )
    
    def __del__(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def execute_claude_command(self, command: str, timeout: int = 300) -> Dict:
        """Execute a command using claude -p"""
        start_time = time.time()
        
        try:
            # Run claude with the command
            process = subprocess.Popen(
                ["claude", "--dangerously-skip-permissions", "-p", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.claude_home
            )
            
            # Wait for completion with timeout
            stdout, stderr = process.communicate(timeout=timeout)
            execution_time = int((time.time() - start_time) * 1000)
            
            if process.returncode == 0:
                return {
                    'status': 'success',
                    'output': stdout.strip(),
                    'error': None,
                    'execution_time_ms': execution_time
                }
            else:
                return {
                    'status': 'failed',
                    'output': stdout.strip() if stdout else None,
                    'error': stderr.strip() if stderr else 'Command failed',
                    'execution_time_ms': execution_time
                }
                
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                'status': 'timeout',
                'output': None,
                'error': f'Command timed out after {timeout} seconds',
                'execution_time_ms': timeout * 1000
            }
        except Exception as e:
            return {
                'status': 'failed',
                'output': None,
                'error': str(e),
                'execution_time_ms': int((time.time() - start_time) * 1000)
            }
    
    def execute_brain_command(self, command: str, timeout: int = 300) -> Dict:
        """Execute a command using brain.sh"""
        start_time = time.time()
        
        try:
            # Check if brain is running
            status_result = subprocess.run(
                [self.brain_path, "status"],
                capture_output=True,
                text=True
            )
            
            if "not running" in status_result.stdout:
                # Start brain if not running
                subprocess.run([self.brain_path, "start"], check=True)
                time.sleep(5)  # Give it time to start
            
            # Get current log file
            logs_dir = os.path.join(os.path.dirname(self.brain_path), "logs")
            log_files = sorted([f for f in os.listdir(logs_dir) if f.endswith('.log')])
            current_log = os.path.join(logs_dir, log_files[-1]) if log_files else None
            
            if not current_log:
                return {
                    'status': 'failed',
                    'output': None,
                    'error': 'No log file found',
                    'execution_time_ms': int((time.time() - start_time) * 1000)
                }
            
            # Record current position in log
            with open(current_log, 'r') as f:
                f.seek(0, 2)  # Go to end
                log_position = f.tell()
            
            # Send command
            send_result = subprocess.run(
                [self.brain_path, "send", command],
                capture_output=True,
                text=True
            )
            
            if send_result.returncode != 0:
                return {
                    'status': 'failed',
                    'output': None,
                    'error': send_result.stderr or 'Failed to send command',
                    'execution_time_ms': int((time.time() - start_time) * 1000)
                }
            
            # Wait for response with timeout
            response = None
            elapsed = 0
            check_interval = 2
            
            while elapsed < timeout:
                time.sleep(check_interval)
                elapsed += check_interval
                
                # Read new log content
                with open(current_log, 'r') as f:
                    f.seek(log_position)
                    new_content = f.read()
                
                if new_content.strip():
                    # Parse for response
                    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
                    temp_file.write(new_content)
                    temp_file.close()
                    
                    try:
                        interactions = self.parser.parse_log_file(temp_file.name)
                        if interactions:
                            response = interactions[-1]['response']
                            break
                    finally:
                        os.unlink(temp_file.name)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            if response:
                return {
                    'status': 'success',
                    'output': self.parser.clean_response(response),
                    'error': None,
                    'execution_time_ms': execution_time,
                    'log_file_path': current_log
                }
            else:
                return {
                    'status': 'timeout',
                    'output': None,
                    'error': f'No response received within {timeout} seconds',
                    'execution_time_ms': execution_time
                }
                
        except Exception as e:
            return {
                'status': 'failed',
                'output': None,
                'error': str(e),
                'execution_time_ms': int((time.time() - start_time) * 1000)
            }
    
    def get_memory_context(self, memory_ids: List[int]) -> str:
        """Retrieve memories by IDs and format as context"""
        if not memory_ids:
            return ""
        
        context_parts = []
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT content, memory_type, importance
                FROM memories
                WHERE id = ANY(%s) AND is_active = TRUE
                ORDER BY importance DESC
            """, (memory_ids,))
            
            memories = cur.fetchall()
            
            for memory in memories:
                context_parts.append(
                    f"[{memory['memory_type'].upper()}] {memory['content']}"
                )
        
        if context_parts:
            return "Context from memories:\n" + "\n".join(context_parts) + "\n\n"
        return ""
    
    def execute_task(self, task: Dict) -> Dict:
        """Execute a task with appropriate method"""
        # Add memory context to command if specified
        command = task['command']
        if task.get('context_memory_ids'):
            context = self.get_memory_context(task['context_memory_ids'])
            command = context + command
        
        # Execute based on requirements
        if task.get('requires_brain', False):
            result = self.execute_brain_command(
                command, 
                timeout=task.get('timeout_seconds', 300)
            )
        else:
            result = self.execute_claude_command(
                command,
                timeout=task.get('timeout_seconds', 300)
            )
        
        # Store output as memory if successful and significant
        if result['status'] == 'success' and result.get('output'):
            output = result['output']
            
            # Determine if output should be stored as memory
            should_store = False
            memory_type = 'task'
            importance = 3
            
            # Check task type for memory storage rules
            task_type = task.get('task_type', 'custom')
            
            if task_type == 'memory_management':
                should_store = True
                memory_type = 'task'
                importance = 7
            elif task_type == 'learning_research':
                should_store = True
                memory_type = 'fact'
                importance = 6
            elif task_type == 'daily_routine' and 'goal' in output.lower():
                should_store = True
                memory_type = 'task'
                importance = 5
            elif len(output) > 100:  # Store substantial outputs
                should_store = True
            
            if should_store:
                try:
                    memory_id = self.memory_manager.store_memory(
                        content=f"Task '{task.get('task_name', 'Unknown')}' output: {output[:500]}",
                        memory_type=memory_type,
                        importance=importance,
                        tags=['task-output', task_type],
                        context={'task_id': task.get('id'), 'task_name': task.get('task_name')},
                        source='task_execution'
                    )
                    result['memory_ids'] = [memory_id]
                except Exception as e:
                    print(f"Failed to store task output as memory: {e}")
        
        return result


def main():
    """Test the executor"""
    executor = ClaudeExecutor()
    
    if len(sys.argv) < 2:
        print("Usage: python claude_executor.py <command> [--brain]")
        return
    
    command = sys.argv[1]
    use_brain = '--brain' in sys.argv
    
    print(f"Executing: {command}")
    print(f"Method: {'brain.sh' if use_brain else 'claude -p'}")
    
    if use_brain:
        result = executor.execute_brain_command(command)
    else:
        result = executor.execute_claude_command(command)
    
    print(f"\nStatus: {result['status']}")
    print(f"Execution time: {result['execution_time_ms']}ms")
    
    if result['output']:
        print(f"\nOutput:\n{result['output']}")
    
    if result['error']:
        print(f"\nError:\n{result['error']}")


if __name__ == "__main__":
    main()