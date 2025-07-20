#!/usr/bin/env python3
"""Debug version of task daemon to find the status='running' issue"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def test_update():
    """Test the UPDATE statement that's causing issues"""
    try:
        conn = psycopg2.connect(
            database="claudemini",
            user="claudemini",
            host="localhost"
        )
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # First, let's see what get_pending_tasks returns
            cur.execute("""
                SELECT * FROM scheduled_tasks 
                WHERE is_active = TRUE 
                AND next_run_at <= NOW() 
                ORDER BY priority DESC, next_run_at ASC
                LIMIT 1
            """)
            task = cur.fetchone()
            
            if not task:
                print("No pending tasks found")
                return
                
            print(f"Task ID: {task['id']}")
            print(f"Task Name: {task['task_name']}")
            print(f"Current Status: {task['status']}")
            print(f"Task dict keys: {list(task.keys())}")
            
            # Now try the UPDATE that's failing
            print("\nAttempting UPDATE...")
            try:
                cur.execute("""
                    UPDATE scheduled_tasks 
                    SET last_run_at = NOW() 
                    WHERE id = %s
                """, (task['id'],))
                print("UPDATE successful!")
                conn.rollback()  # Don't actually commit
            except psycopg2.Error as e:
                print(f"UPDATE failed: {e}")
                print(f"Error code: {e.pgcode}")
                print(f"Error detail: {e.diag.message_detail if hasattr(e, 'diag') else 'N/A'}")
                
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_update()