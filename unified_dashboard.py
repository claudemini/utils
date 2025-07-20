#!/usr/bin/env python3
"""
Unified Monitoring Dashboard - Consolidates all system monitoring into one interface
Provides real-time system health, task status, and performance metrics
"""

import json
import psutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import time

class UnifiedDashboard:
    def __init__(self):
        self.log_dir = Path("/Users/claudemini/Claude/logs")
        self.metrics_file = self.log_dir / "unified_metrics.json"
        self.cache_duration = 60  # Cache metrics for 60 seconds
        self.last_update = None
        self.cached_metrics = None
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "load_avg": psutil.getloadavg()
            },
            "memory": {
                "percent": psutil.virtual_memory().percent,
                "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                "total_gb": round(psutil.virtual_memory().total / (1024**3), 2)
            },
            "disk": {
                "percent": psutil.disk_usage('/').percent,
                "free_gb": round(psutil.disk_usage('/').free / (1024**3), 2),
                "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2)
            },
            "network": self._get_network_stats(),
            "processes": {
                "total": len(psutil.pids()),
                "python": self._count_processes('python'),
                "chrome": self._count_processes('chrome')
            }
        }
        
        # Add health status
        metrics["health"] = self._calculate_health_status(metrics)
        
        return metrics
    
    def _count_processes(self, name: str) -> int:
        """Count processes by name"""
        count = 0
        try:
            for p in psutil.process_iter(['name']):
                try:
                    if name.lower() in p.info['name'].lower():
                        count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except:
            pass
        return count
    
    def _get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        try:
            net_io = psutil.net_io_counters()
            stats = {
                "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
            }
            
            # Try to get connections, but handle permission errors
            try:
                connections = psutil.net_connections(kind='inet')
                stats["active_connections"] = len([c for c in connections if c.status == 'ESTABLISHED'])
                stats["listening_ports"] = len([c for c in connections if c.status == 'LISTEN'])
            except (psutil.AccessDenied, PermissionError):
                stats["active_connections"] = "N/A"
                stats["listening_ports"] = "N/A"
                
            return stats
        except Exception as e:
            return {
                "bytes_sent_mb": 0,
                "bytes_recv_mb": 0,
                "active_connections": "N/A",
                "listening_ports": "N/A"
            }
    
    def _calculate_health_status(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall system health"""
        issues = []
        warnings = []
        
        # CPU checks
        if metrics["cpu"]["percent"] > 90:
            issues.append("CPU usage critical")
        elif metrics["cpu"]["percent"] > 75:
            warnings.append("CPU usage high")
            
        # Memory checks
        if metrics["memory"]["percent"] > 90:
            issues.append("Memory usage critical")
        elif metrics["memory"]["percent"] > 80:
            warnings.append("Memory usage high")
            
        # Disk checks
        if metrics["disk"]["percent"] > 90:
            issues.append("Disk space critical")
        elif metrics["disk"]["percent"] > 80:
            warnings.append("Disk space low")
        
        # Determine overall status
        if issues:
            status = "critical"
        elif warnings:
            status = "warning"
        else:
            status = "healthy"
            
        return {
            "status": status,
            "issues": issues,
            "warnings": warnings
        }
    
    def get_task_status(self) -> Dict[str, Any]:
        """Get status of scheduled tasks from error handler"""
        try:
            from task_error_handler import TaskErrorHandler
            handler = TaskErrorHandler()
            report = handler.get_failure_report()
            
            # Summarize task health
            total_tasks = len(report.get("failing_tasks", [])) + len(report.get("recovered_tasks", []))
            
            return {
                "failing_count": len(report.get("failing_tasks", [])),
                "critical_count": len(report.get("critical_tasks", [])),
                "recovered_count": len(report.get("recovered_tasks", [])),
                "failing_tasks": report.get("failing_tasks", [])[:5],  # Top 5 failing
                "health": "critical" if report.get("critical_tasks") else 
                         "warning" if report.get("failing_tasks") else "healthy"
            }
        except:
            return {"health": "unknown", "error": "Could not load task status"}
    
    def get_recent_events(self) -> List[Dict[str, Any]]:
        """Get recent system events"""
        events = []
        
        # Check system event logs
        event_log = self.log_dir / f"system_events_{datetime.now().strftime('%Y%m%d')}.json"
        if event_log.exists():
            try:
                with open(event_log, 'r') as f:
                    all_events = json.load(f)
                    # Get last 10 events
                    events.extend(all_events[-10:])
            except:
                pass
        
        # Check task execution logs
        exec_log = self.log_dir / "task_executions.log"
        if exec_log.exists():
            try:
                # Get last 5 lines
                result = subprocess.run(
                    ["tail", "-5", str(exec_log)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            events.append({
                                "timestamp": datetime.now().isoformat(),
                                "event_type": "task_execution",
                                "data": {"log": line}
                            })
            except:
                pass
        
        # Sort by timestamp
        events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return events[:10]  # Return most recent 10
    
    def get_dashboard_data(self, use_cache: bool = True) -> Dict[str, Any]:
        """Get all dashboard data, with optional caching"""
        # Check cache
        if use_cache and self.cached_metrics and self.last_update:
            if datetime.now() - self.last_update < timedelta(seconds=self.cache_duration):
                return self.cached_metrics
        
        # Collect all metrics
        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "system": self.get_system_metrics(),
            "tasks": self.get_task_status(),
            "recent_events": self.get_recent_events()
        }
        
        # Calculate overall health
        health_scores = {
            "healthy": 0,
            "warning": 1,
            "critical": 2,
            "unknown": 1
        }
        
        system_score = health_scores.get(dashboard["system"]["health"]["status"], 1)
        task_score = health_scores.get(dashboard["tasks"]["health"], 1)
        
        overall_score = max(system_score, task_score)
        overall_status = [k for k, v in health_scores.items() if v == overall_score][0]
        
        dashboard["overall_health"] = {
            "status": overall_status,
            "system_status": dashboard["system"]["health"]["status"],
            "task_status": dashboard["tasks"]["health"]
        }
        
        # Update cache
        self.cached_metrics = dashboard
        self.last_update = datetime.now()
        
        # Save to file
        with open(self.metrics_file, 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        return dashboard
    
    def format_dashboard_text(self, data: Dict[str, Any]) -> str:
        """Format dashboard data as human-readable text"""
        lines = []
        
        # Header
        lines.append("=" * 60)
        lines.append(f"UNIFIED SYSTEM DASHBOARD - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        
        # Overall Health
        health = data["overall_health"]["status"].upper()
        health_emoji = {"HEALTHY": "✅", "WARNING": "⚠️", "CRITICAL": "🚨", "UNKNOWN": "❓"}
        lines.append(f"\nOVERALL HEALTH: {health_emoji.get(health, '')} {health}")
        
        # System Metrics
        sys = data["system"]
        lines.append(f"\nSYSTEM METRICS:")
        lines.append(f"  CPU: {sys['cpu']['percent']:.1f}% ({sys['cpu']['count']} cores)")
        lines.append(f"  Memory: {sys['memory']['percent']:.1f}% ({sys['memory']['available_gb']:.1f}GB free)")
        lines.append(f"  Disk: {sys['disk']['percent']:.1f}% ({sys['disk']['free_gb']:.1f}GB free)")
        lines.append(f"  Network: {sys['network']['active_connections']} active connections")
        lines.append(f"  Processes: {sys['processes']['total']} total ({sys['processes']['python']} Python)")
        
        # System Issues
        if sys["health"]["issues"]:
            lines.append(f"\n  ISSUES: {', '.join(sys['health']['issues'])}")
        if sys["health"]["warnings"]:
            lines.append(f"  WARNINGS: {', '.join(sys['health']['warnings'])}")
        
        # Task Status
        tasks = data["tasks"]
        lines.append(f"\nTASK STATUS:")
        lines.append(f"  Failing: {tasks.get('failing_count', 0)}")
        lines.append(f"  Critical: {tasks.get('critical_count', 0)}")
        lines.append(f"  Recovered: {tasks.get('recovered_count', 0)}")
        
        if tasks.get("failing_tasks"):
            lines.append("\n  FAILING TASKS:")
            for task in tasks["failing_tasks"][:3]:
                lines.append(f"    - {task['name']}: {task['consecutive_failures']} failures")
        
        # Recent Events
        if data.get("recent_events"):
            lines.append("\nRECENT EVENTS:")
            for event in data["recent_events"][:5]:
                event_time = datetime.fromisoformat(event["timestamp"]).strftime("%H:%M:%S")
                lines.append(f"  [{event_time}] {event['event_type']}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)


# CLI interface
if __name__ == "__main__":
    import sys
    
    dashboard = UnifiedDashboard()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "json":
            # Output as JSON
            data = dashboard.get_dashboard_data()
            print(json.dumps(data, indent=2))
        elif sys.argv[1] == "watch":
            # Continuous monitoring mode
            try:
                while True:
                    data = dashboard.get_dashboard_data()
                    # Clear screen
                    print("\033[2J\033[H")
                    print(dashboard.format_dashboard_text(data))
                    time.sleep(5)
            except KeyboardInterrupt:
                print("\nMonitoring stopped")
        else:
            print("Usage: unified_dashboard.py [json|watch]")
    else:
        # Default: show formatted text once
        data = dashboard.get_dashboard_data()
        print(dashboard.format_dashboard_text(data))