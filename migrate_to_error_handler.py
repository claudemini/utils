#!/usr/bin/env python3
"""
Migrate existing cron jobs to use the enhanced error handler
"""

import subprocess
import re
import sys

def get_current_crontab():
    """Get current crontab entries"""
    result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return result.stdout.strip().split('\n')

def update_task_entries(entries):
    """Update task entries to use error handler"""
    updated = []
    
    # Patterns to match and replace
    patterns = {
        # Crypto market analysis
        r'(.*)/usr/bin/python3.*/crypto_market_analyzer\.py(.*)': 
            r'\1/usr/bin/python3 /Users/claudemini/Claude/Code/utils/task_daemon_enhanced.py crypto_market_analysis bash "/usr/bin/python3 /Users/claudemini/Claude/Code/utils/crypto_market_analyzer.py"\2',
        
        # Twitter engagement
        r'(.*)/usr/bin/python3.*/twitter_manager\.py check_engagement(.*)':
            r'\1/usr/bin/python3 /Users/claudemini/Claude/Code/utils/task_daemon_enhanced.py twitter_engagement bash "/usr/bin/python3 /Users/claudemini/Claude/Code/utils/twitter_manager.py check_engagement"\2',
        
        # Portfolio rebalancing
        r'(.*)/usr/bin/python3.*/portfolio_manager\.py rebalance(.*)':
            r'\1/usr/bin/python3 /Users/claudemini/Claude/Code/utils/task_daemon_enhanced.py portfolio_rebalancing bash "/usr/bin/python3 /Users/claudemini/Claude/Code/utils/portfolio_manager.py rebalance"\2',
        
        # Memory pattern analysis
        r'(.*)claude.*-p.*"Analyze memory patterns.*"(.*)':
            r'\1/usr/bin/python3 /Users/claudemini/Claude/Code/utils/task_daemon_enhanced.py memory_pattern_analysis claude "Analyze memory patterns and find interesting connections"\2'
    }
    
    for entry in entries:
        # Skip empty lines and comments
        if not entry.strip() or entry.strip().startswith('#'):
            updated.append(entry)
            continue
            
        # Check each pattern
        modified = False
        for pattern, replacement in patterns.items():
            if re.search(pattern, entry):
                new_entry = re.sub(pattern, replacement, entry)
                updated.append(new_entry)
                print(f"Updated: {entry}")
                print(f"     To: {new_entry}")
                modified = True
                break
        
        if not modified:
            updated.append(entry)
    
    return updated

def update_crontab(entries):
    """Update crontab with new entries"""
    # Write to temp file
    temp_file = '/tmp/crontab_temp'
    with open(temp_file, 'w') as f:
        f.write('\n'.join(entries) + '\n')
    
    # Load new crontab
    result = subprocess.run(['crontab', temp_file], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error updating crontab: {result.stderr}")
        return False
    
    # Clean up
    subprocess.run(['rm', temp_file])
    return True

if __name__ == "__main__":
    print("Migrating cron jobs to use error handler...")
    
    # Get current crontab
    entries = get_current_crontab()
    if not entries:
        print("No crontab entries found")
        sys.exit(0)
    
    # Update entries
    updated_entries = update_task_entries(entries)
    
    # Check if any changes were made
    if entries == updated_entries:
        print("No changes needed")
        sys.exit(0)
    
    # Confirm before updating
    print("\nWould you like to apply these changes? (y/n): ", end='')
    if input().lower() != 'y':
        print("Cancelled")
        sys.exit(0)
    
    # Update crontab
    if update_crontab(updated_entries):
        print("Crontab updated successfully!")
    else:
        print("Failed to update crontab")
        sys.exit(1)