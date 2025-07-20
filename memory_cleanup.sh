#!/bin/bash
# Memory cleanup script - removes old low-importance memories

echo "[$(date)] Starting memory cleanup..."

# Remove old daily memories (older than 30 days) with low importance
psql -U claudemini -d claudemini -c "
DELETE FROM memories 
WHERE memory_type = 'daily' 
AND importance < 5 
AND created_at < NOW() - INTERVAL '30 days';
"

# Remove old conversation memories (older than 7 days) with low importance
psql -U claudemini -d claudemini -c "
DELETE FROM memories 
WHERE memory_type = 'conversation' 
AND importance < 4 
AND created_at < NOW() - INTERVAL '7 days';
"

# Vacuum the database to reclaim space
psql -U claudemini -d claudemini -c "VACUUM ANALYZE memories;"

# Store a memory about the cleanup
/Users/claudemini/Claude/Code/utils/memory.sh store "Performed routine memory cleanup" --type daily --importance 2

echo "[$(date)] Memory cleanup completed"