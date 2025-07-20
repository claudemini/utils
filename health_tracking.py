#!/usr/bin/env python3
"""
Health tracking automation for Claude Mini
Daily logs, reminders, and wellness monitoring
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging

# Setup logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'health_tracking.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('health_tracking')

@dataclass
class HealthEntry:
    """Represents a daily health entry"""
    date: str
    system_uptime: float  # hours
    cpu_usage_avg: float  # percentage
    memory_usage_avg: float  # percentage
    disk_usage: float  # percentage
    network_activity: str  # low, medium, high
    error_count: int
    automated_tasks_completed: int
    notes: str = ""

class HealthTracker:
    """Main health tracking system"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent / "data" / "health"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.health_file = self.data_dir / "health_log.json"
        self.log_dir = Path(__file__).parent / "logs"
        
    def get_system_metrics(self) -> Dict:
        """Get current system health metrics"""
        try:
            import psutil
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime_hours = (datetime.now().timestamp() - boot_time) / 3600
            
            # CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network activity (simplified)
            net_io = psutil.net_io_counters()
            network_activity = "medium"  # Could be enhanced with historical comparison
            
            return {
                'uptime_hours': uptime_hours,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'network_activity': network_activity
            }
            
        except ImportError:
            logger.warning("psutil not available, using mock data")
            return {
                'uptime_hours': 24.0,
                'cpu_percent': 15.0,
                'memory_percent': 65.0,
                'disk_percent': 45.0,
                'network_activity': 'medium'
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def count_daily_errors(self) -> int:
        """Count errors from today's logs"""
        try:
            error_count = 0
            log_files = list(self.log_dir.glob("*.log"))
            today = datetime.now().strftime('%Y-%m-%d')
            
            for log_file in log_files:
                try:
                    with open(log_file, 'r') as f:
                        for line in f:
                            if today in line and 'ERROR' in line:
                                error_count += 1
                except Exception:
                    continue
                    
            return error_count
            
        except Exception as e:
            logger.warning(f"Error counting daily errors: {e}")
            return 0
    
    def count_completed_tasks(self) -> int:
        """Count automated tasks completed today"""
        try:
            # Check cron scheduler log for completed tasks
            cron_log = self.log_dir / "cron_scheduler.log"
            if not cron_log.exists():
                return 0
                
            completed_count = 0
            today = datetime.now().strftime('%Y-%m-%d')
            
            with open(cron_log, 'r') as f:
                for line in f:
                    if today in line and 'completed successfully' in line:
                        completed_count += 1
                        
            return completed_count
            
        except Exception as e:
            logger.warning(f"Error counting completed tasks: {e}")
            return 0
    
    def create_daily_entry(self, notes: str = "") -> HealthEntry:
        """Create a health entry for today"""
        metrics = self.get_system_metrics()
        error_count = self.count_daily_errors()
        completed_tasks = self.count_completed_tasks()
        
        entry = HealthEntry(
            date=datetime.now().strftime('%Y-%m-%d'),
            system_uptime=metrics.get('uptime_hours', 0),
            cpu_usage_avg=metrics.get('cpu_percent', 0),
            memory_usage_avg=metrics.get('memory_percent', 0),
            disk_usage=metrics.get('disk_percent', 0),
            network_activity=metrics.get('network_activity', 'unknown'),
            error_count=error_count,
            automated_tasks_completed=completed_tasks,
            notes=notes
        )
        
        return entry
    
    def save_health_entry(self, entry: HealthEntry):
        """Save health entry to log"""
        # Load existing entries
        entries = []
        if self.health_file.exists():
            try:
                with open(self.health_file, 'r') as f:
                    data = json.load(f)
                    entries = data.get('entries', [])
            except Exception as e:
                logger.warning(f"Error loading existing health data: {e}")
        
        # Add new entry (replace if same date exists)
        entries = [e for e in entries if e.get('date') != entry.date]
        entries.append(asdict(entry))
        
        # Sort by date
        entries.sort(key=lambda x: x['date'])
        
        # Keep only last 30 days
        if len(entries) > 30:
            entries = entries[-30:]
        
        # Save updated data
        data = {
            'entries': entries,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(self.health_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Health entry saved for {entry.date}")
    
    def generate_health_report(self) -> str:
        """Generate a health summary report"""
        if not self.health_file.exists():
            return "No health data available yet."
        
        try:
            with open(self.health_file, 'r') as f:
                data = json.load(f)
                entries = data.get('entries', [])
            
            if not entries:
                return "No health entries found."
            
            # Get latest entry
            latest = entries[-1]
            
            # Calculate averages for last 7 days
            recent_entries = entries[-7:] if len(entries) >= 7 else entries
            avg_cpu = sum(e['cpu_usage_avg'] for e in recent_entries) / len(recent_entries)
            avg_memory = sum(e['memory_usage_avg'] for e in recent_entries) / len(recent_entries)
            total_errors = sum(e['error_count'] for e in recent_entries)
            total_tasks = sum(e['automated_tasks_completed'] for e in recent_entries)
            
            # Generate status indicators
            cpu_status = "🟢" if avg_cpu < 50 else "🟡" if avg_cpu < 80 else "🔴"
            memory_status = "🟢" if avg_memory < 70 else "🟡" if avg_memory < 85 else "🔴"
            error_status = "🟢" if total_errors < 5 else "🟡" if total_errors < 20 else "🔴"
            
            report = [
                "🏥 System Health Report",
                "=" * 30,
                "",
                f"📅 Report Date: {latest['date']}",
                f"⏱️ Uptime: {latest['system_uptime']:.1f} hours",
                "",
                "📊 7-Day Averages:",
                f"{cpu_status} CPU Usage: {avg_cpu:.1f}%",
                f"{memory_status} Memory Usage: {avg_memory:.1f}%",
                f"💾 Disk Usage: {latest['disk_usage']:.1f}%",
                f"🌐 Network: {latest['network_activity']}",
                "",
                "🤖 Automation Performance:",
                f"{error_status} Errors (7 days): {total_errors}",
                f"✅ Tasks Completed (7 days): {total_tasks}",
                "",
                "📈 Trend:" 
            ]
            
            if len(entries) >= 2:
                prev_cpu = entries[-2]['cpu_usage_avg']
                cpu_trend = "📈" if latest['cpu_usage_avg'] > prev_cpu else "📉"
                report.append(f"{cpu_trend} CPU: {latest['cpu_usage_avg']:.1f}% (was {prev_cpu:.1f}%)")
            
            if latest['notes']:
                report.extend(["", f"📝 Notes: {latest['notes']}"])
            
            report.append(f"\n🤖 Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error generating health report: {e}")
            return f"Error generating health report: {str(e)}"
    
    def store_health_memory(self, entry: HealthEntry):
        """Store health summary in memory system"""
        try:
            summary = f"Daily health check: {entry.system_uptime:.1f}h uptime, {entry.cpu_usage_avg:.1f}% CPU, {entry.memory_usage_avg:.1f}% memory, {entry.error_count} errors, {entry.automated_tasks_completed} tasks completed. System running {'well' if entry.error_count < 5 else 'with issues'}."
            
            # Use the memory system
            memory_script = Path(__file__).parent / "memory.sh"
            if memory_script.exists():
                import subprocess
                cmd = [
                    str(memory_script), "store", summary,
                    "--type", "health",
                    "--tags", "system-health monitoring daily",
                    "--importance", "5"
                ]
                subprocess.run(cmd, cwd=str(memory_script.parent), capture_output=True)
                
        except Exception as e:
            logger.warning(f"Failed to store health memory: {e}")
    
    def daily_health_check(self) -> str:
        """Perform daily health check and return report"""
        logger.info("Starting daily health check...")
        
        # Create health entry
        entry = self.create_daily_entry()
        
        # Save entry
        self.save_health_entry(entry)
        
        # Store in memory
        self.store_health_memory(entry)
        
        # Generate report
        report = self.generate_health_report()
        
        logger.info("Daily health check complete")
        return report

def main():
    """Main function"""
    tracker = HealthTracker()
    
    if len(os.sys.argv) > 1:
        command = os.sys.argv[1]
        
        if command == 'check':
            report = tracker.daily_health_check()
            print(report)
        elif command == 'report':
            report = tracker.generate_health_report()
            print(report)
    else:
        # Default: daily check
        report = tracker.daily_health_check()
        print(report)

if __name__ == "__main__":
    import sys
    main()