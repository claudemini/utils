#!/bin/bash
# Backup verification script

echo "[$(date)] Starting backup verification..."

# Check if critical files exist and are recent
CRITICAL_FILES=(
    "/Users/claudemini/Claude/.env"
    "/Users/claudemini/Claude/CLAUDE.md"
)

ISSUES=0

for file in "${CRITICAL_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "ERROR: Critical file missing: $file"
        ISSUES=$((ISSUES + 1))
    else
        # Check if file was modified in last 7 days (168 hours)
        if [ $(find "$file" -mtime +7 | wc -l) -gt 0 ]; then
            echo "WARNING: $file hasn't been modified in over 7 days"
        fi
    fi
done

# Check database backup
LAST_BACKUP=$(psql -U claudemini -d claudemini -t -c "
SELECT MAX(started_at) 
FROM task_executions te
JOIN scheduled_tasks st ON te.task_id = st.id
WHERE st.task_name LIKE '%backup%' 
AND te.status = 'success';
")

if [ -z "$LAST_BACKUP" ]; then
    echo "WARNING: No successful backup tasks found"
    ISSUES=$((ISSUES + 1))
fi

# Store result in memory
if [ $ISSUES -eq 0 ]; then
    /Users/claudemini/Claude/Code/utils/memory.sh store "Backup verification passed - all systems healthy" --type daily --importance 3
else
    /Users/claudemini/Claude/Code/utils/memory.sh store "Backup verification found $ISSUES issues requiring attention" --type daily --importance 8 --tags security backup
fi

echo "[$(date)] Backup verification completed with $ISSUES issues"