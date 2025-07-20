#!/bin/bash

# Task Diagnostics Script
# Analyzes failing tasks and provides detailed debugging information

echo "=== Task Daemon Diagnostics ==="
echo "Started at: $(date)"
echo

# Check if task daemon is running
echo "1. Checking task daemon status..."
if pgrep -f "task_daemon.py" > /dev/null; then
    echo "✓ Task daemon is running (PID: $(pgrep -f 'task_daemon.py'))"
else
    echo "✗ Task daemon is NOT running"
fi
echo

# Check database connectivity
echo "2. Checking database connectivity..."
if psql -U claudemini -d claudemini -c "SELECT 1" > /dev/null 2>&1; then
    echo "✓ Database connection successful"
else
    echo "✗ Database connection failed"
fi
echo

# Analyze recent task failures
echo "3. Analyzing recent task failures..."
psql -U claudemini -d claudemini -t -c "
SELECT 
    name,
    status,
    error_message,
    last_run,
    next_run
FROM tasks 
WHERE status IN ('failed', 'error') 
ORDER BY last_run DESC 
LIMIT 10;
" 2>/dev/null | while IFS='|' read -r name status error last_run next_run; do
    echo "Task: $name"
    echo "  Status: $status"
    echo "  Error: $error"
    echo "  Last Run: $last_run"
    echo "  Next Run: $next_run"
    echo
done

# Check system resources
echo "4. Checking system resources..."
echo "Memory Usage:"
vm_stat | grep -E "(free|active|inactive|wired)"
echo
echo "Disk Usage:"
df -h /Users/claudemini
echo
echo "CPU Load:"
uptime
echo

# Check permissions
echo "5. Checking permissions..."
echo "Task daemon script: $(ls -la /Users/claudemini/Claude/Code/utils/task_daemon.py 2>/dev/null || echo 'Not found')"
echo "Memory manager: $(ls -la /Users/claudemini/Claude/Code/utils/memory_manager.py 2>/dev/null || echo 'Not found')"
echo

# Check Python dependencies
echo "6. Checking Python environment..."
if command -v uv &> /dev/null; then
    echo "✓ uv is installed"
    cd /Users/claudemini/Claude/Code/utils
    if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
        echo "Dependencies status:"
        uv pip list 2>/dev/null | grep -E "(psycopg2|schedule|requests)" || echo "Key dependencies may be missing"
    fi
else
    echo "✗ uv is not available"
fi
echo

# Check logs
echo "7. Recent error patterns in logs..."
if [ -f "/Users/claudemini/Claude/task_daemon.log" ]; then
    echo "Last 20 errors from task daemon log:"
    grep -i "error\|fail\|exception" /Users/claudemini/Claude/task_daemon.log | tail -20
else
    echo "No task daemon log found"
fi

echo
echo "=== Diagnostics Complete ==="
echo "Timestamp: $(date)"