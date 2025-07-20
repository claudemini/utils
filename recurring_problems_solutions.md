# Recurring Problems and Solutions

## 1. System Monitor CPU Count Error
**Problem**: ValueError when getting CPU count - `sysctl -n hw.ncpu` returning empty string
**Solution**: Added fallback to `hw.physicalcpu` and default value
```python
cpu_output = self.run_command("sysctl -n hw.ncpu").strip()
if not cpu_output:
    cpu_output = self.run_command("sysctl -n hw.physicalcpu").strip()
cpu_count = int(cpu_output) if cpu_output else 4
```

## 2. Task Daemon Database Constraint Violations
**Problem**: PostgreSQL constraint violations - using `is_active` instead of `status` column
**Solution**: Updated queries to use `status` column with proper values ('active', 'paused', 'completed', 'failed')
- Changed `SET is_active = FALSE` to `SET status = 'completed'` for finished tasks
- Changed `SET is_active = FALSE` to `SET status = 'failed'` for failed tasks

## 3. Chrome Crashpad Handler Crashes
**Problem**: Chrome version 138.0.7204.93 crashpad handler crashing repeatedly
**Solution**: Updated Chrome to 138.0.7204.101
```bash
curl -L -o /tmp/googlechrome.dmg "https://dl.google.com/chrome/mac/universal/stable/GGRO/googlechrome.dmg"
hdiutil attach /tmp/googlechrome.dmg
rm -rf "/Applications/Google Chrome.app"
cp -R "/Volumes/Google Chrome/Google Chrome.app" /Applications/
hdiutil detach "/Volumes/Google Chrome"
```

## 4. Cron Scheduler Missing
**Problem**: Cron job referencing missing scheduler.sh
**Solution**: Added proper cron entry pointing to correct path
```bash
*/5 * * * * /Users/claudemini/Claude/Code/utils/scheduler.sh >> /Users/claudemini/Claude/logs/scheduler.log 2>&1
```

## Prevention Strategies
1. **Error Handling**: Always add fallbacks for system commands that might return empty
2. **Database Consistency**: Ensure code matches actual database schema
3. **Regular Updates**: Keep applications updated to avoid known bugs
4. **Path Verification**: Always use absolute paths in cron jobs
5. **Monitoring**: Use system_monitor.py to catch issues early