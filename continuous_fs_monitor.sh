#!/bin/bash

# Continuous file system monitoring script
# Monitors the Claude home directory for changes

WATCH_DIR="/Users/claudemini/Claude"
MONITOR_SCRIPT="/Users/claudemini/Claude/Code/utils/filesystem_monitor.py"
LOG_DIR="/Users/claudemini/Claude/logs"
LOG_FILE="$LOG_DIR/fs_monitor_$(date +%Y-%m-%d).log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Store memory about the monitoring activity
store_memory() {
    /Users/claudemini/Claude/Code/utils/memory.sh store "Ran filesystem monitoring - found $1 changes" --type daily --tags monitoring filesystem --importance 3
}

log_message "Starting continuous filesystem monitoring for $WATCH_DIR"

# Run initial scan
python "$MONITOR_SCRIPT"

# Main monitoring loop
while true; do
    # Wait for 30 minutes
    sleep 1800
    
    log_message "Running scheduled filesystem scan"
    
    # Run the monitor and capture output
    output=$(python "$MONITOR_SCRIPT" 2>&1)
    
    # Check if there were significant changes
    if echo "$output" | grep -q "New Files\|Modified Files\|Files Needing Attention"; then
        log_message "Significant changes detected"
        
        # Count changes
        new_files=$(echo "$output" | grep -oP 'New Files \(\K\d+' || echo "0")
        modified_files=$(echo "$output" | grep -oP 'Modified Files \(\K\d+' || echo "0")
        total_changes=$((new_files + modified_files))
        
        # Store memory if significant changes
        if [ $total_changes -gt 0 ]; then
            store_memory "$total_changes"
        fi
    else
        log_message "No significant changes detected"
    fi
done