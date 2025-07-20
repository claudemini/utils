#!/usr/bin/env python3
"""
Chrome Process Manager - Handles Chrome crashes and resource issues
Monitors Chrome processes, cleans up crashes, and manages memory usage
"""

import psutil
import subprocess
import os
import signal
import time
from datetime import datetime
from pathlib import Path
import json
import shutil

class ChromeProcessManager:
    def __init__(self):
        self.log_dir = Path("/Users/claudemini/Claude/logs")
        self.crash_log = self.log_dir / "chrome_crashes.log"
        self.chrome_names = ['Google Chrome', 'Chrome', 'chrome', 'chromium']
        self.max_memory_gb = 4.0  # Max GB per Chrome process
        self.max_total_memory_gb = 8.0  # Max total Chrome memory
        
    def get_chrome_processes(self):
        """Get all Chrome-related processes"""
        chrome_procs = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'create_time']):
                try:
                    if any(chrome in proc.info['name'] for chrome in self.chrome_names):
                        chrome_procs.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'memory_mb': proc.info['memory_info'].rss / (1024**2),
                            'create_time': proc.info['create_time']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            self.log_error(f"Error getting Chrome processes: {e}")
            
        return chrome_procs
    
    def check_crashed_processes(self):
        """Check for crashed Chrome processes"""
        crashed = []
        
        # Check for crashpad_handler processes
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'crashpad_handler' in proc.info['name']:
                        crashed.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': ' '.join(proc.info.get('cmdline', []))
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            self.log_error(f"Error checking crashed processes: {e}")
            
        # Check crash reports directory
        crash_dirs = [
            Path.home() / "Library/Application Support/Google/Chrome/Crashpad/completed",
            Path("/tmp") / "crashpad",
            Path("/var/folders").rglob("**/crashpad_*")
        ]
        
        for crash_dir in crash_dirs:
            if isinstance(crash_dir, Path) and crash_dir.exists():
                # Count recent crash files
                try:
                    crash_files = list(crash_dir.glob("*.dmp"))
                    if crash_files:
                        crashed.append({
                            'type': 'crash_dump',
                            'location': str(crash_dir),
                            'count': len(crash_files)
                        })
                except:
                    pass
                    
        return crashed
    
    def analyze_memory_usage(self):
        """Analyze Chrome memory usage"""
        chrome_procs = self.get_chrome_processes()
        
        total_memory_mb = sum(p['memory_mb'] for p in chrome_procs)
        high_memory_procs = [p for p in chrome_procs if p['memory_mb'] > self.max_memory_gb * 1024]
        
        return {
            'total_processes': len(chrome_procs),
            'total_memory_mb': total_memory_mb,
            'total_memory_gb': total_memory_mb / 1024,
            'high_memory_processes': high_memory_procs,
            'exceeds_limit': total_memory_mb / 1024 > self.max_total_memory_gb
        }
    
    def clean_crashed_processes(self):
        """Clean up crashed Chrome processes"""
        cleaned = 0
        
        # Kill crashpad_handler processes
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'crashpad_handler' in proc.info['name']:
                        os.kill(proc.info['pid'], signal.SIGTERM)
                        cleaned += 1
                        self.log_action(f"Killed crashpad_handler process {proc.info['pid']}")
                        time.sleep(0.5)  # Give it time to terminate
                except (psutil.NoSuchProcess, psutil.AccessDenied, ProcessLookupError):
                    pass
        except Exception as e:
            self.log_error(f"Error cleaning crashed processes: {e}")
            
        # Clean up crash dumps
        crash_locations = [
            Path.home() / "Library/Application Support/Google/Chrome/Crashpad/completed",
            Path("/tmp")
        ]
        
        for location in crash_locations:
            if location.exists():
                try:
                    # Remove old crash dumps (older than 7 days)
                    for crash_file in location.glob("*.dmp"):
                        if crash_file.stat().st_mtime < time.time() - (7 * 24 * 3600):
                            crash_file.unlink()
                            cleaned += 1
                except Exception as e:
                    self.log_error(f"Error cleaning crash dumps in {location}: {e}")
                    
        return cleaned
    
    def restart_chrome_safely(self):
        """Safely restart Chrome"""
        # First, try to quit Chrome gracefully
        try:
            subprocess.run(['osascript', '-e', 'tell application "Google Chrome" to quit'], 
                         capture_output=True, timeout=10)
            time.sleep(2)
        except:
            pass
            
        # Kill remaining processes
        killed = 0
        for proc in self.get_chrome_processes():
            try:
                os.kill(proc['pid'], signal.SIGTERM)
                killed += 1
            except:
                pass
                
        if killed > 0:
            time.sleep(2)
            
        # Restart Chrome
        try:
            subprocess.Popen(['open', '-a', 'Google Chrome'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            self.log_action("Restarted Google Chrome")
            return True
        except Exception as e:
            self.log_error(f"Failed to restart Chrome: {e}")
            return False
    
    def manage_high_memory_processes(self):
        """Manage Chrome processes with high memory usage"""
        memory_info = self.analyze_memory_usage()
        actions_taken = []
        
        # If total memory exceeds limit, restart Chrome
        if memory_info['exceeds_limit']:
            self.log_action(f"Chrome using {memory_info['total_memory_gb']:.1f}GB, exceeds limit of {self.max_total_memory_gb}GB")
            if self.restart_chrome_safely():
                actions_taken.append("Restarted Chrome due to high memory usage")
        else:
            # Kill individual high-memory processes
            for proc in memory_info['high_memory_processes']:
                try:
                    os.kill(proc['pid'], signal.SIGTERM)
                    actions_taken.append(f"Killed high-memory Chrome process {proc['pid']} ({proc['memory_mb']:.0f}MB)")
                    self.log_action(f"Killed Chrome process {proc['pid']} using {proc['memory_mb']:.0f}MB")
                except:
                    pass
                    
        return actions_taken
    
    def log_action(self, message):
        """Log an action taken"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] ACTION: {message}\n"
        
        with open(self.crash_log, 'a') as f:
            f.write(log_entry)
            
    def log_error(self, message):
        """Log an error"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] ERROR: {message}\n"
        
        with open(self.crash_log, 'a') as f:
            f.write(log_entry)
    
    def run_maintenance(self):
        """Run full Chrome maintenance"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'crashed_processes': [],
            'memory_analysis': {},
            'actions_taken': []
        }
        
        # Check for crashes
        crashed = self.check_crashed_processes()
        if crashed:
            report['crashed_processes'] = crashed
            cleaned = self.clean_crashed_processes()
            if cleaned > 0:
                report['actions_taken'].append(f"Cleaned {cleaned} crashed processes/files")
                
        # Analyze memory
        memory_info = self.analyze_memory_usage()
        report['memory_analysis'] = memory_info
        
        # Handle high memory
        if memory_info['high_memory_processes'] or memory_info['exceeds_limit']:
            actions = self.manage_high_memory_processes()
            report['actions_taken'].extend(actions)
            
        # Log if actions were taken
        if report['actions_taken']:
            self.log_action(f"Maintenance completed: {', '.join(report['actions_taken'])}")
            
            # Store in memory system
            memory_cmd = f'/Users/claudemini/Claude/Code/utils/memory.sh store "Chrome maintenance: {report["actions_taken"][0]}" --type daily --tags "maintenance chrome" --importance 4'
            subprocess.run(memory_cmd, shell=True)
            
        return report


# CLI interface
if __name__ == "__main__":
    import sys
    
    manager = ChromeProcessManager()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            # Show Chrome status
            procs = manager.get_chrome_processes()
            memory = manager.analyze_memory_usage()
            crashed = manager.check_crashed_processes()
            
            print(f"Chrome Status:")
            print(f"  Processes: {len(procs)}")
            print(f"  Total Memory: {memory['total_memory_gb']:.1f}GB")
            print(f"  Crashed: {len(crashed)}")
            
            if memory['high_memory_processes']:
                print(f"\n  High Memory Processes:")
                for proc in memory['high_memory_processes']:
                    print(f"    PID {proc['pid']}: {proc['memory_mb']:.0f}MB")
                    
        elif sys.argv[1] == "clean":
            # Clean crashed processes
            cleaned = manager.clean_crashed_processes()
            print(f"Cleaned {cleaned} crashed processes/files")
            
        elif sys.argv[1] == "restart":
            # Restart Chrome
            if manager.restart_chrome_safely():
                print("Chrome restarted successfully")
            else:
                print("Failed to restart Chrome")
                
        elif sys.argv[1] == "json":
            # Run maintenance and output JSON
            report = manager.run_maintenance()
            print(json.dumps(report, indent=2))
            
    else:
        # Default: run maintenance
        report = manager.run_maintenance()
        
        if report['actions_taken']:
            print("Chrome maintenance completed:")
            for action in report['actions_taken']:
                print(f"  - {action}")
        else:
            print("Chrome is running normally")