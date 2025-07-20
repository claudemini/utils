#!/usr/bin/env python3
"""
System Event Monitor - Monitors and responds to system events
"""

import subprocess
import time
import json
import os
from datetime import datetime
from pathlib import Path

# Configuration
MONITOR_INTERVAL = 300  # 5 minutes
LOG_DIR = Path("/Users/claudemini/Claude/logs")
LOG_DIR.mkdir(exist_ok=True)
MEMORY_SCRIPT = "/Users/claudemini/Claude/Code/utils/memory.sh"

class SystemMonitor:
    def __init__(self):
        self.last_update_check = None
        self.known_issues = set()
        
    def run_command(self, cmd):
        """Run shell command and return output"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout.strip()
        except Exception as e:
            return f"Error: {str(e)}"
    
    def check_software_updates(self):
        """Check for available software updates"""
        updates = self.run_command("softwareupdate --list 2>&1")
        if "Software Update found the following" in updates:
            return {"status": "updates_available", "details": updates}
        return {"status": "up_to_date", "details": None}
    
    def check_disk_space(self):
        """Check disk space usage"""
        df_output = self.run_command("df -h / | tail -1")
        parts = df_output.split()
        if len(parts) >= 5:
            usage_percent = int(parts[4].strip('%'))
            return {
                "usage_percent": usage_percent,
                "critical": usage_percent > 90,
                "warning": usage_percent > 80
            }
        return {"usage_percent": 0, "critical": False, "warning": False}
    
    def check_memory_pressure(self):
        """Check memory pressure"""
        vm_stat = self.run_command("vm_stat")
        pressure_cmd = "memory_pressure | grep 'System-wide memory free percentage' | awk '{print $5}'"
        free_percent = self.run_command(pressure_cmd)
        
        try:
            free_pct = int(free_percent.strip('%'))
            return {
                "free_percent": free_pct,
                "critical": free_pct < 10,
                "warning": free_pct < 20
            }
        except:
            return {"free_percent": 100, "critical": False, "warning": False}
    
    def check_system_load(self):
        """Check system load average"""
        uptime = self.run_command("uptime")
        # Extract load averages
        if "load average" in uptime:
            load_part = uptime.split("load average")[1].strip()
            # Handle both "load average: " and "load averages: " formats
            load_part = load_part.lstrip("s:").strip()
            loads = [float(x) for x in load_part.split()[:3]]
            cpu_output = self.run_command("sysctl -n hw.ncpu").strip()
            if not cpu_output:
                # Fallback to alternative method
                cpu_output = self.run_command("sysctl -n hw.physicalcpu").strip()
            cpu_count = int(cpu_output) if cpu_output else 4  # Default to 4 if all else fails
            
            return {
                "load_1min": loads[0],
                "load_5min": loads[1],
                "load_15min": loads[2],
                "cpu_count": cpu_count,
                "critical": loads[0] > cpu_count * 2,
                "warning": loads[0] > cpu_count
            }
        return {"load_1min": 0, "critical": False, "warning": False}
    
    def check_recent_errors(self):
        """Check for recent system errors"""
        errors = []
        
        # Check install log
        install_errors = self.run_command(
            "tail -1000 /var/log/install.log 2>/dev/null | grep -E 'error|fail' | tail -10"
        )
        if install_errors:
            errors.extend(install_errors.split('\n'))
        
        # Check system.log if available
        system_errors = self.run_command(
            "tail -1000 /var/log/system.log 2>/dev/null | grep -E 'error|panic|crash' | tail -10"
        )
        if system_errors:
            errors.extend(system_errors.split('\n'))
            
        return errors
    
    def log_event(self, event_type, data):
        """Log system event"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "data": data
        }
        
        log_file = LOG_DIR / f"system_events_{datetime.now().strftime('%Y%m%d')}.json"
        
        # Read existing logs
        logs = []
        if log_file.exists():
            with open(log_file, 'r') as f:
                try:
                    logs = json.load(f)
                except:
                    logs = []
        
        # Append new entry
        logs.append(log_entry)
        
        # Write back
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def store_memory(self, content, importance=5):
        """Store important finding in memory system"""
        cmd = f'{MEMORY_SCRIPT} store "{content}" --type daily --tags "system monitoring automatic" --importance {importance}'
        self.run_command(cmd)
    
    def monitor_once(self):
        """Run one monitoring cycle"""
        findings = []
        actions = []
        
        # Check software updates
        updates = self.check_software_updates()
        if updates["status"] == "updates_available":
            findings.append("Software updates available")
            self.log_event("software_update", updates)
            
        # Check disk space
        disk = self.check_disk_space()
        if disk["critical"]:
            findings.append(f"CRITICAL: Disk usage at {disk['usage_percent']}%")
            actions.append("Clean up disk space immediately")
            self.store_memory(f"CRITICAL: Disk space at {disk['usage_percent']}%", importance=9)
        elif disk["warning"]:
            findings.append(f"Warning: Disk usage at {disk['usage_percent']}%")
            
        # Check memory
        memory = self.check_memory_pressure()
        if memory["critical"]:
            findings.append(f"CRITICAL: Memory free at {memory['free_percent']}%")
            actions.append("Close unnecessary applications")
            self.store_memory(f"CRITICAL: Low memory {memory['free_percent']}% free", importance=9)
        elif memory["warning"]:
            findings.append(f"Warning: Memory free at {memory['free_percent']}%")
            
        # Check system load
        load = self.check_system_load()
        if load["critical"]:
            findings.append(f"CRITICAL: System load at {load['load_1min']}")
            actions.append("Investigate high CPU usage")
            self.store_memory(f"CRITICAL: High system load {load['load_1min']}", importance=8)
        elif load["warning"]:
            findings.append(f"Warning: System load at {load['load_1min']}")
            
        # Check errors
        errors = self.check_recent_errors()
        new_errors = [e for e in errors if e not in self.known_issues]
        if new_errors:
            findings.append(f"Found {len(new_errors)} new system errors")
            self.known_issues.update(new_errors)
            self.log_event("system_errors", new_errors)
            
        # Log summary
        if findings:
            summary = {
                "findings": findings,
                "actions": actions,
                "timestamp": datetime.now().isoformat()
            }
            self.log_event("monitoring_summary", summary)
            
            # Store significant findings in memory
            if len(findings) > 2 or actions:
                memory_content = f"System monitoring: {', '.join(findings[:3])}"
                if actions:
                    memory_content += f". Actions needed: {', '.join(actions[:2])}"
                self.store_memory(memory_content, importance=7)
        
        return findings, actions
    
    def run_continuous(self):
        """Run continuous monitoring"""
        print(f"Starting system monitor (checking every {MONITOR_INTERVAL}s)")
        
        while True:
            try:
                findings, actions = self.monitor_once()
                
                if findings:
                    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
                    print("Findings:", ', '.join(findings))
                    if actions:
                        print("Actions needed:", ', '.join(actions))
                        
            except Exception as e:
                print(f"Monitor error: {str(e)}")
                
            time.sleep(MONITOR_INTERVAL)

if __name__ == "__main__":
    monitor = SystemMonitor()
    
    # Run once for immediate check
    print("Running initial system check...")
    findings, actions = monitor.monitor_once()
    
    if findings:
        print("\nCurrent System Status:")
        for finding in findings:
            print(f"  - {finding}")
            
        if actions:
            print("\nRecommended Actions:")
            for action in actions:
                print(f"  ! {action}")
    else:
        print("System appears healthy")
    
    # Option to run continuously
    print("\nTo run continuous monitoring, use: python system_monitor.py --continuous")
    
    import sys
    if "--continuous" in sys.argv:
        monitor.run_continuous()