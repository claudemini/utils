#!/usr/bin/env python3
"""
Claude Task Daemon - A persistent task scheduler with full context
Runs as a continuous loop checking and executing scheduled tasks
"""

import asyncio
import os
import sys
import time
import signal
import logging
from datetime import datetime, timezone
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
import subprocess
import json
from task_error_handler import TaskErrorHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/task_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('task_daemon')

class TaskDaemon:
    def __init__(self):
        self.running = True
        self.tick_interval = 60  # Check every 60 seconds
        self.claude_md_path = Path("/Users/claudemini/Claude/CLAUDE.md")
        self.env_path = Path("/Users/claudemini/Claude/.env")
        self.context = {}
        self.db_conn = None
        self.retry_attempts = {}  # Track retry attempts per task
        self.max_retries = 3
        self.retry_delays = [60, 300, 900]  # 1 min, 5 min, 15 min
        self.error_handler = TaskErrorHandler()  # Initialize error handler
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
    def handle_shutdown(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    def load_context(self):
        """Load CLAUDE.md and environment context"""
        try:
            # Load CLAUDE.md
            if self.claude_md_path.exists():
                with open(self.claude_md_path, 'r') as f:
                    self.context['claude_md'] = f.read()
                logger.info("Loaded CLAUDE.md context")
            
            # Load environment variables
            if self.env_path.exists():
                with open(self.env_path, 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
                logger.info("Loaded environment variables")
                
            # Set up PATH to include necessary binaries
            os.environ['PATH'] = f"/Users/claudemini/.local/bin:{os.environ.get('PATH', '')}"
            
        except Exception as e:
            logger.error(f"Error loading context: {e}")
            
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.db_conn = psycopg2.connect(
                dbname="claudemini",
                user="claudemini",
                host="localhost"
            )
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
            
    def get_pending_tasks(self):
        """Get tasks that need to be executed"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM scheduled_tasks 
                    WHERE is_active = TRUE 
                    AND next_run_at <= NOW() 
                    ORDER BY priority DESC, next_run_at ASC
                    LIMIT 5
                """)
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []
            
    def execute_task(self, task):
        """Execute a single task with full context"""
        execution_id = None
        start_time = datetime.now(timezone.utc)
        
        try:
            # Update last run time (don't change status in scheduled_tasks)
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE scheduled_tasks 
                    SET last_run_at = NOW() 
                    WHERE id = %s
                """, (task['id'],))
                
                # Create execution record
                cur.execute("""
                    INSERT INTO task_executions (task_id, status)
                    VALUES (%s, 'running')
                    RETURNING id
                """, (task['id'],))
                execution_id = cur.fetchone()[0]
                self.db_conn.commit()
                
            logger.info(f"Executing task: {task['task_name']} (ID: {task['id']})")
            
            # Build command with full context
            if task['task_type'] == 'claude_task':
                # Use claude with full permissions and context
                cmd = [
                    'claude',
                    '--dangerously-skip-permissions',
                    '-p',
                    task['prompt'] or ''
                ]
            else:
                # Use command directly
                cmd = task['command'] or 'echo "No command specified"'
                
            # Execute with timeout
            timeout = task.get('timeout_seconds', 300)  # 5 min default
            result = subprocess.run(
                cmd,
                shell=isinstance(cmd, str),
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ.copy(),
                cwd="/Users/claudemini/Claude"  # Set home directory
            )
            
            # Update execution record
            end_time = datetime.now(timezone.utc)
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            with self.db_conn.cursor() as cur:
                if result.returncode == 0:
                    status = 'success'
                    # Reset retry count on success
                    if task['id'] in self.retry_attempts:
                        del self.retry_attempts[task['id']]
                    
                    cur.execute("""
                        UPDATE task_executions 
                        SET status = %s, output = %s, completed_at = NOW(),
                            execution_time_ms = %s
                        WHERE id = %s
                    """, (status, result.stdout, execution_time_ms, execution_id))
                    
                    # Calculate next run time
                    if task['schedule_type'] == 'interval' or task['schedule_type'] == 'recurring':
                        interval = task.get('interval_seconds', 300)  # Default 5 min
                        cur.execute("""
                            UPDATE scheduled_tasks 
                            SET next_run_at = NOW() + INTERVAL '%s seconds'
                            WHERE id = %s
                        """, (interval, task['id']))
                    else:
                        # One-time task
                        cur.execute("""
                            UPDATE scheduled_tasks 
                            SET status = 'completed'
                            WHERE id = %s
                        """, (task['id'],))
                else:
                    status = 'failed'
                    error = result.stderr or f"Exit code: {result.returncode}"
                    cur.execute("""
                        UPDATE task_executions 
                        SET status = %s, error = %s, completed_at = NOW(),
                            execution_time_ms = %s
                        WHERE id = %s
                    """, (status, error, execution_time_ms, execution_id))
                    
                    cur.execute("""
                        UPDATE scheduled_tasks 
                        SET next_run_at = NOW() + INTERVAL '5 minutes'
                        WHERE id = %s
                    """, (task['id'],))
                    
                self.db_conn.commit()
                logger.info(f"Task {task['task_name']} completed with status: {status}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"Task {task['task_name']} timed out")
            self._handle_task_failure(task['id'], execution_id, 'timeout', 'Task execution timed out')
        except Exception as e:
            logger.error(f"Task {task['task_name']} failed: {e}")
            self._handle_task_failure(task['id'], execution_id, 'failed', str(e))
            
    def _handle_task_failure(self, task_id, execution_id, status, error):
        """Handle task failure with exponential backoff retry logic"""
        try:
            # Rollback any pending transaction
            self.db_conn.rollback()
            
            # Track retry attempts
            if task_id not in self.retry_attempts:
                self.retry_attempts[task_id] = 0
            
            self.retry_attempts[task_id] += 1
            retry_count = self.retry_attempts[task_id]
            
            with self.db_conn.cursor() as cur:
                if execution_id:
                    cur.execute("""
                        UPDATE task_executions 
                        SET status = %s, error = %s, completed_at = NOW()
                        WHERE id = %s
                    """, (status, error, execution_id))
                
                # Determine next retry time based on retry count
                if retry_count <= self.max_retries:
                    # Use exponential backoff
                    delay_seconds = self.retry_delays[min(retry_count - 1, len(self.retry_delays) - 1)]
                    logger.info(f"Task {task_id} will retry in {delay_seconds} seconds (attempt {retry_count}/{self.max_retries})")
                    
                    cur.execute("""
                        UPDATE scheduled_tasks 
                        SET next_run_at = NOW() + INTERVAL '%s seconds'
                        WHERE id = %s
                    """, (delay_seconds, task_id))
                else:
                    # Max retries exceeded, disable task
                    logger.error(f"Task {task_id} exceeded max retries ({self.max_retries}), disabling")
                    cur.execute("""
                        UPDATE scheduled_tasks 
                        SET status = 'failed',
                            next_run_at = NULL
                        WHERE id = %s
                    """, (task_id,))
                    
                    # Store memory about the failure
                    from memory_manager import MemoryManager
                    memory = MemoryManager()
                    memory.store_memory(
                        f"Task {task_id} failed after {self.max_retries} retries with error: {error}",
                        memory_type="task",
                        tags=["task_failure", "automation"],
                        importance=7
                    )
                    
                self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error handling task failure: {e}")
            self.db_conn.rollback()
            
    async def main_loop(self):
        """Main game loop"""
        logger.info("Task daemon started")
        tick_count = 0
        
        while self.running:
            tick_start = time.time()
            tick_count += 1
            
            try:
                # Get pending tasks
                tasks = self.get_pending_tasks()
                
                if tasks:
                    logger.info(f"Tick #{tick_count}: Found {len(tasks)} pending tasks")
                    
                    # Execute tasks (could be made concurrent)
                    for task in tasks:
                        if not self.running:
                            break
                        self.execute_task(task)
                        
                # Ensure connection is healthy
                self.db_conn.commit()
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                # Try to reconnect to database
                try:
                    self.connect_db()
                except:
                    pass
                    
            # Calculate sleep time to maintain tick rate
            tick_duration = time.time() - tick_start
            sleep_time = max(0, self.tick_interval - tick_duration)
            
            if sleep_time > 0 and self.running:
                await asyncio.sleep(sleep_time)
                
        logger.info("Task daemon stopped")
        
    def run(self):
        """Run the daemon"""
        try:
            # Load context
            self.load_context()
            
            # Connect to database
            self.connect_db()
            
            # Run main loop
            asyncio.run(self.main_loop())
            
        finally:
            if self.db_conn:
                self.db_conn.close()
                

if __name__ == "__main__":
    daemon = TaskDaemon()
    daemon.run()