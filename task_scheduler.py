#!/usr/bin/env python3

"""
Task Scheduler for Claude Brain
Runs every 5 minutes to execute pending tasks
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import subprocess
from typing import List, Dict, Optional
import json
import traceback

# Add utils directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from claude_executor import ClaudeExecutor
from task_templates import TaskTemplates

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/claudemini/Claude/Code/utils/logs/task_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('task_scheduler')

class TaskScheduler:
    def __init__(self):
        self.executor = ClaudeExecutor()
        self.running = True
        self.conn = psycopg2.connect(
            dbname="claudemini",
            user="claudemini",
            host="localhost"
        )
        self.conn.autocommit = False
        
        # Create logs directory if it doesn't exist
        os.makedirs('/Users/claudemini/Claude/Code/utils/logs', exist_ok=True)
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
    
    def handle_shutdown(self, signum, frame):
        """Gracefully shutdown the scheduler"""
        logger.info("Received shutdown signal, finishing current tasks...")
        self.running = False
    
    def get_pending_tasks(self, batch_size: int = 10) -> List[Dict]:
        """Get tasks that are ready to run"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM get_pending_tasks(%s)", (batch_size,))
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting pending tasks: {e}")
            self.conn.rollback()
            return []
    
    def start_task_execution(self, task_id: int) -> Optional[int]:
        """Create a task execution record"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO task_executions (task_id, status, started_at)
                    VALUES (%s, 'running', CURRENT_TIMESTAMP)
                    RETURNING id
                """, (task_id,))
                execution_id = cur.fetchone()[0]
                
                # Update task last_run_at
                cur.execute("""
                    UPDATE scheduled_tasks 
                    SET last_run_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (task_id,))
                
                self.conn.commit()
                return execution_id
        except Exception as e:
            logger.error(f"Error starting task execution: {e}")
            self.conn.rollback()
            return None
    
    def complete_task_execution(self, execution_id: int, result: Dict):
        """Update task execution with results"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE task_executions
                    SET status = %s,
                        completed_at = CURRENT_TIMESTAMP,
                        output = %s,
                        error = %s,
                        execution_time_ms = %s,
                        memory_ids = %s,
                        log_file_path = %s
                    WHERE id = %s
                """, (
                    result['status'],
                    result.get('output'),
                    result.get('error'),
                    result.get('execution_time_ms'),
                    result.get('memory_ids', []),
                    result.get('log_file_path'),
                    execution_id
                ))
                
                # Get task info for next run calculation
                cur.execute("""
                    SELECT st.* 
                    FROM scheduled_tasks st
                    JOIN task_executions te ON te.task_id = st.id
                    WHERE te.id = %s
                """, (execution_id,))
                task = cur.fetchone()
                
                if task:
                    # Update task based on result
                    if result['status'] == 'success':
                        # Reset retry count and calculate next run
                        cur.execute("""
                            UPDATE scheduled_tasks
                            SET retry_count = 0,
                                last_success_at = CURRENT_TIMESTAMP,
                                next_run_at = calculate_next_run(
                                    schedule_type, 
                                    cron_expression, 
                                    interval_minutes, 
                                    CURRENT_TIMESTAMP
                                ),
                                status = CASE 
                                    WHEN schedule_type = 'once' THEN 'completed'
                                    ELSE 'active'
                                END
                            WHERE id = %s
                        """, (task[0],))  # task[0] is the id
                    else:
                        # Increment retry count
                        cur.execute("""
                            UPDATE scheduled_tasks
                            SET retry_count = retry_count + 1,
                                status = CASE 
                                    WHEN retry_count + 1 >= max_retries THEN 'failed'
                                    ELSE status
                                END,
                                next_run_at = CASE
                                    WHEN retry_count + 1 < max_retries 
                                    THEN CURRENT_TIMESTAMP + INTERVAL '5 minutes'
                                    ELSE next_run_at
                                END
                            WHERE id = %s
                        """, (task[0],))
                
                self.conn.commit()
                
        except Exception as e:
            logger.error(f"Error completing task execution: {e}")
            logger.error(traceback.format_exc())
            self.conn.rollback()
    
    def execute_task(self, task: Dict) -> Dict:
        """Execute a single task"""
        logger.info(f"Executing task: {task['task_name']} (ID: {task['id']})")
        
        # Check for special handling
        metadata = task.get('metadata', {})
        
        # Execute the task
        result = self.executor.execute_task(task)
        
        # Special handling for social media posts
        if (task['task_type'] == 'social_media' and 
            metadata.get('auto_post') and 
            result['status'] == 'success' and 
            result.get('output')):
            
            try:
                # Post the tweet
                tweet_result = subprocess.run(
                    ['./tweet.sh'],
                    input=result['output'],
                    text=True,
                    capture_output=True,
                    cwd='/Users/claudemini/Claude/Code/utils'
                )
                
                if tweet_result.returncode == 0:
                    logger.info(f"Successfully posted tweet: {result['output'][:50]}...")
                else:
                    logger.error(f"Failed to post tweet: {tweet_result.stderr}")
                    
            except Exception as e:
                logger.error(f"Error posting tweet: {e}")
        
        return result
    
    def run_single_batch(self):
        """Run a single batch of tasks"""
        tasks = self.get_pending_tasks()
        
        if not tasks:
            logger.debug("No pending tasks found")
            return
        
        logger.info(f"Found {len(tasks)} pending tasks")
        
        for task in tasks:
            if not self.running:
                break
            
            # Start execution record
            execution_id = self.start_task_execution(task['id'])
            if not execution_id:
                logger.error(f"Failed to start execution for task {task['id']}")
                continue
            
            try:
                # Execute the task
                result = self.execute_task(task)
                
                # Record results
                self.complete_task_execution(execution_id, result)
                
                logger.info(
                    f"Task {task['task_name']} completed with status: {result['status']}"
                )
                
            except Exception as e:
                logger.error(f"Error executing task {task['id']}: {e}")
                logger.error(traceback.format_exc())
                
                # Record failure
                self.complete_task_execution(execution_id, {
                    'status': 'failed',
                    'error': str(e),
                    'execution_time_ms': 0
                })
    
    def initialize_tasks(self):
        """Initialize database with task templates"""
        logger.info("Checking for task initialization...")
        
        try:
            with self.conn.cursor() as cur:
                # Check if we already have tasks
                cur.execute("SELECT COUNT(*) FROM scheduled_tasks")
                count = cur.fetchone()[0]
                
                if count == 0:
                    logger.info("No tasks found, initializing with templates...")
                    templates = TaskTemplates.get_all_templates()
                    
                    for template in templates:
                        # Calculate initial next_run_at
                        if template['schedule_type'] == 'recurring':
                            next_run = datetime.now() + timedelta(
                                minutes=template['interval_minutes']
                            )
                        else:
                            # For cron tasks, use the calculate_next_run function
                            cur.execute(
                                "SELECT calculate_next_run(%s, %s, %s, %s)",
                                (
                                    template['schedule_type'],
                                    template.get('cron_expression'),
                                    template.get('interval_minutes'),
                                    datetime.now()
                                )
                            )
                            next_run = cur.fetchone()[0]
                        
                        # Insert task
                        cur.execute("""
                            INSERT INTO scheduled_tasks (
                                task_name, task_type, description, command,
                                schedule_type, cron_expression, interval_minutes,
                                next_run_at, priority, timeout_seconds,
                                requires_brain, metadata
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            template['task_name'],
                            template['task_type'],
                            template.get('description'),
                            template['command'],
                            template['schedule_type'],
                            template.get('cron_expression'),
                            template.get('interval_minutes'),
                            next_run,
                            template.get('priority', 5),
                            template.get('timeout_seconds', 300),
                            template.get('requires_brain', False),
                            Json(template.get('metadata', {}))
                        ))
                    
                    self.conn.commit()
                    logger.info(f"Initialized {len(templates)} tasks")
                else:
                    logger.info(f"Found {count} existing tasks")
                    
        except Exception as e:
            logger.error(f"Error initializing tasks: {e}")
            self.conn.rollback()
    
    def run(self):
        """Main scheduler loop"""
        logger.info("Task scheduler started")
        
        # Initialize tasks if needed
        self.initialize_tasks()
        
        # Run one batch
        self.run_single_batch()
        
        logger.info("Task scheduler completed")


def main():
    """Main entry point"""
    scheduler = TaskScheduler()
    
    try:
        scheduler.run()
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()