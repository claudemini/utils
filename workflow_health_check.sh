#!/bin/bash
# Workflow health check - monitors all automated systems

echo "[$(date)] Starting workflow health check..."

ISSUES=0

# Check task daemon
if ! pgrep -f "task_daemon.py" > /dev/null; then
    echo "ERROR: Task daemon is not running!"
    # Try to restart it
    cd /Users/claudemini/Claude/Code/utils
    nohup python task_daemon.py > /Users/claudemini/Claude/task_daemon.log 2>&1 &
    echo "Attempted to restart task daemon"
    ISSUES=$((ISSUES + 1))
fi

# Check failed tasks
FAILED_TASKS=$(psql -U claudemini -d claudemini -t -c "
SELECT COUNT(*) 
FROM scheduled_tasks 
WHERE is_active = FALSE 
AND task_name NOT LIKE '%test%';
")

if [ $FAILED_TASKS -gt 5 ]; then
    echo "WARNING: $FAILED_TASKS tasks have been disabled due to failures"
    ISSUES=$((ISSUES + 1))
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "WARNING: Disk usage is at $DISK_USAGE%"
    ISSUES=$((ISSUES + 1))
fi

# Check memory table size
MEMORY_COUNT=$(psql -U claudemini -d claudemini -t -c "SELECT COUNT(*) FROM memories;")
if [ $MEMORY_COUNT -gt 10000 ]; then
    echo "INFO: Memory table has $MEMORY_COUNT entries - consider cleanup"
fi

# Store health check result
if [ $ISSUES -eq 0 ]; then
    /Users/claudemini/Claude/Code/utils/memory.sh store "Workflow health check passed - all systems operational" --type daily --importance 2
else
    /Users/claudemini/Claude/Code/utils/memory.sh store "Workflow health check found $ISSUES issues" --type daily --importance 7 --tags health monitoring
    
    # Create a task to investigate issues
    psql -U claudemini -d claudemini -c "
    INSERT INTO scheduled_tasks (task_name, task_type, schedule_type, priority, parameters)
    VALUES ('Investigate Workflow Issues', 'claude_task', 'once', 9, 
        '{\"prompt\": \"Review recent workflow health issues and fix any problems found\"}'::jsonb)
    ON CONFLICT DO NOTHING;
    "
fi

echo "[$(date)] Health check completed with $ISSUES issues"