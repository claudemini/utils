#!/bin/bash

# Task Scheduler wrapper script
# Usage: ./scheduler.sh [run|status|init|list]

UTILS_DIR="$(dirname "$0")"
cd "$UTILS_DIR"

case "$1" in
    run)
        echo "Running task scheduler..."
        /Users/claudemini/.local/bin/uv run python task_scheduler.py
        ;;
    
    status)
        echo "Recent task executions:"
        psql -d claudemini -c "
            SELECT 
                te.started_at,
                st.task_name,
                te.status,
                te.execution_time_ms
            FROM task_executions te
            JOIN scheduled_tasks st ON te.task_id = st.id
            ORDER BY te.started_at DESC
            LIMIT 10;
        "
        ;;
    
    list)
        echo "Active scheduled tasks:"
        psql -d claudemini -c "
            SELECT 
                id,
                task_name,
                task_type,
                schedule_type,
                next_run_at,
                status
            FROM scheduled_tasks
            WHERE is_active = TRUE
            ORDER BY next_run_at;
        "
        ;;
    
    init)
        echo "Initializing database tables..."
        psql -d claudemini -f create_task_tables.sql
        echo "Tables created. Run './scheduler.sh run' to initialize tasks."
        ;;
    
    *)
        echo "Usage: $0 {run|status|init|list}"
        echo "  run    - Run the task scheduler once"
        echo "  status - Show recent task executions"
        echo "  init   - Initialize database tables"
        echo "  list   - List all active tasks"
        exit 1
        ;;
esac