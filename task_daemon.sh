#!/bin/bash

# Task Daemon Management Script
# Usage: ./task_daemon.sh [start|stop|restart|status|logs]

UTILS_DIR="/Users/claudemini/Claude/Code/utils"
SESSION_NAME="task_daemon"
PYTHON_CMD="/Users/claudemini/.local/bin/uv run python"

cd "$UTILS_DIR"

case "$1" in
    start)
        # Check if session already exists
        if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
            echo "Task daemon is already running in tmux session '$SESSION_NAME'"
            exit 1
        fi
        
        echo "Starting task daemon..."
        
        # Create tmux session and run daemon
        tmux new-session -d -s "$SESSION_NAME" -c "$UTILS_DIR"
        tmux send-keys -t "$SESSION_NAME" "$PYTHON_CMD task_daemon.py" Enter
        
        echo "Task daemon started in tmux session '$SESSION_NAME'"
        echo "Use './task_daemon.sh logs' to view output"
        ;;
        
    stop)
        echo "Stopping task daemon..."
        
        # Send SIGTERM to daemon
        tmux send-keys -t "$SESSION_NAME" C-c
        sleep 2
        
        # Kill session if still exists
        if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
            tmux kill-session -t "$SESSION_NAME"
        fi
        
        echo "Task daemon stopped"
        ;;
        
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
        
    status)
        if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
            echo "Task daemon is running in tmux session '$SESSION_NAME'"
            echo ""
            echo "Recent executions:"
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
        else
            echo "Task daemon is not running"
        fi
        ;;
        
    logs)
        if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
            echo "Attaching to task daemon session (press Ctrl-B then D to detach)..."
            tmux attach-session -t "$SESSION_NAME"
        else
            echo "Task daemon is not running"
            echo "Showing recent log entries:"
            tail -n 50 logs/task_daemon.log
        fi
        ;;
        
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo "  start   - Start the task daemon"
        echo "  stop    - Stop the task daemon"
        echo "  restart - Restart the task daemon"
        echo "  status  - Check daemon status and recent executions"
        echo "  logs    - View daemon logs (attach to tmux session)"
        exit 1
        ;;
esac