#!/bin/bash
# Add Chrome maintenance to cron

# Add Chrome maintenance every 2 hours
(crontab -l 2>/dev/null; echo "0 */2 * * * /usr/bin/python3 /Users/claudemini/Claude/Code/utils/chrome_process_manager.py >> /Users/claudemini/Claude/logs/chrome_maintenance.log 2>&1") | crontab -

echo "Chrome maintenance added to cron"