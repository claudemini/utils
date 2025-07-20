#!/usr/bin/env python3
"""
Workflow Dashboard - Unified monitoring for all automated processes
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone, timedelta
import subprocess
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
import time
import argparse

console = Console()

class WorkflowDashboard:
    def __init__(self):
        self.db_conn = psycopg2.connect(
            dbname="claudemini",
            user="claudemini",
            host="localhost"
        )
        
    def get_task_status(self):
        """Get current status of all scheduled tasks"""
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    st.id,
                    st.task_name,
                    st.is_active,
                    st.last_run_at,
                    st.next_run_at,
                    st.schedule_type,
                    te.status as last_status,
                    te.error as last_error
                FROM scheduled_tasks st
                LEFT JOIN LATERAL (
                    SELECT status, error 
                    FROM task_executions 
                    WHERE task_id = st.id 
                    ORDER BY started_at DESC 
                    LIMIT 1
                ) te ON true
                ORDER BY st.priority DESC, st.created_at
            """)
            return cur.fetchall()
    
    def get_recent_executions(self, limit=10):
        """Get recent task executions"""
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    te.id,
                    st.task_name,
                    te.status,
                    te.started_at,
                    te.completed_at,
                    te.execution_time_ms,
                    te.error
                FROM task_executions te
                JOIN scheduled_tasks st ON te.task_id = st.id
                ORDER BY te.started_at DESC
                LIMIT %s
            """, (limit,))
            return cur.fetchall()
    
    def get_system_health(self):
        """Get system health metrics"""
        health = {}
        
        # Check task daemon
        result = subprocess.run(['pgrep', '-f', 'task_daemon.py'], capture_output=True)
        health['task_daemon'] = 'Running' if result.returncode == 0 else 'Stopped'
        
        # Check cron jobs
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        health['cron_jobs'] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        
        # Check memory usage
        with self.db_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM memories")
            health['total_memories'] = cur.fetchone()[0]
            
            cur.execute("""
                SELECT memory_type, COUNT(*) as count 
                FROM memories 
                GROUP BY memory_type
            """)
            health['memory_types'] = dict(cur.fetchall())
        
        # System resources
        result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 5:
                    health['disk_usage'] = parts[4]
        
        return health
    
    def get_workflow_stats(self):
        """Get workflow statistics"""
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Success rate
            cur.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as success,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                    COUNT(CASE WHEN status = 'timeout' THEN 1 END) as timeout,
                    COUNT(*) as total
                FROM task_executions
                WHERE started_at > NOW() - INTERVAL '24 hours'
            """)
            stats = cur.fetchone()
            
            # Average execution time
            cur.execute("""
                SELECT 
                    AVG(execution_time_ms) as avg_time,
                    MIN(execution_time_ms) as min_time,
                    MAX(execution_time_ms) as max_time
                FROM task_executions
                WHERE status = 'success' 
                AND started_at > NOW() - INTERVAL '24 hours'
            """)
            time_stats = cur.fetchone()
            
            stats.update(time_stats)
            return stats
    
    def create_dashboard_layout(self):
        """Create rich dashboard layout"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split_column(
            Layout(name="tasks"),
            Layout(name="stats", size=10)
        )
        
        layout["right"].split_column(
            Layout(name="health", size=15),
            Layout(name="executions")
        )
        
        return layout
    
    def render_header(self):
        """Render header panel"""
        return Panel(
            Text("Workflow Dashboard", style="bold cyan", justify="center"),
            subtitle=f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    
    def render_tasks_table(self, tasks):
        """Render tasks table"""
        table = Table(title="Scheduled Tasks", expand=True)
        table.add_column("Task", style="cyan")
        table.add_column("Active", justify="center")
        table.add_column("Last Run")
        table.add_column("Next Run")
        table.add_column("Status", justify="center")
        
        for task in tasks:
            active = "✓" if task['is_active'] else "✗"
            active_style = "green" if task['is_active'] else "red"
            
            status = task['last_status'] or "never run"
            status_style = {
                'success': 'green',
                'failed': 'red',
                'timeout': 'yellow',
                'running': 'blue'
            }.get(status, 'white')
            
            last_run = task['last_run_at'].strftime('%H:%M:%S') if task['last_run_at'] else "Never"
            next_run = task['next_run_at'].strftime('%H:%M:%S') if task['next_run_at'] else "N/A"
            
            table.add_row(
                task['task_name'][:30],
                Text(active, style=active_style),
                last_run,
                next_run,
                Text(status, style=status_style)
            )
        
        return Panel(table, title="Tasks")
    
    def render_health_panel(self, health):
        """Render system health panel"""
        lines = []
        lines.append(f"Task Daemon: [{health['task_daemon']}]")
        lines.append(f"Cron Jobs: {health['cron_jobs']}")
        lines.append(f"Disk Usage: {health.get('disk_usage', 'N/A')}")
        lines.append(f"Total Memories: {health['total_memories']}")
        lines.append("")
        lines.append("Memory Types:")
        for mtype, count in health.get('memory_types', {}).items():
            lines.append(f"  {mtype}: {count}")
        
        return Panel("\n".join(lines), title="System Health")
    
    def render_stats_panel(self, stats):
        """Render statistics panel"""
        if stats['total'] > 0:
            success_rate = (stats['success'] / stats['total']) * 100
            lines = [
                f"Success Rate: {success_rate:.1f}%",
                f"Total: {stats['total']} | Success: {stats['success']} | Failed: {stats['failed']}",
                "",
                "Execution Times:",
                f"  Avg: {stats['avg_time']:.0f}ms" if stats['avg_time'] else "  Avg: N/A",
                f"  Min: {stats['min_time']:.0f}ms" if stats['min_time'] else "  Min: N/A",
                f"  Max: {stats['max_time']:.0f}ms" if stats['max_time'] else "  Max: N/A"
            ]
        else:
            lines = ["No executions in last 24 hours"]
        
        return Panel("\n".join(lines), title="24hr Statistics")
    
    def render_executions_table(self, executions):
        """Render recent executions table"""
        table = Table(title="Recent Executions", expand=True)
        table.add_column("Task", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Time", justify="right")
        table.add_column("Duration", justify="right")
        
        for exec in executions:
            status_style = {
                'success': 'green',
                'failed': 'red',
                'timeout': 'yellow',
                'running': 'blue'
            }.get(exec['status'], 'white')
            
            time_str = exec['started_at'].strftime('%H:%M:%S')
            duration = f"{exec['execution_time_ms']}ms" if exec['execution_time_ms'] else "N/A"
            
            table.add_row(
                exec['task_name'][:25],
                Text(exec['status'], style=status_style),
                time_str,
                duration
            )
        
        return Panel(table, title="Recent Executions")
    
    def run_live_dashboard(self, refresh_rate=5):
        """Run live updating dashboard"""
        layout = self.create_dashboard_layout()
        
        with Live(layout, refresh_per_second=1/refresh_rate, screen=True) as live:
            while True:
                try:
                    # Fetch all data
                    tasks = self.get_task_status()
                    health = self.get_system_health()
                    stats = self.get_workflow_stats()
                    executions = self.get_recent_executions()
                    
                    # Update layout
                    layout["header"].update(self.render_header())
                    layout["tasks"].update(self.render_tasks_table(tasks))
                    layout["health"].update(self.render_health_panel(health))
                    layout["stats"].update(self.render_stats_panel(stats))
                    layout["executions"].update(self.render_executions_table(executions))
                    layout["footer"].update(Panel("Press Ctrl+C to exit", style="dim"))
                    
                    time.sleep(refresh_rate)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                    time.sleep(refresh_rate)

def main():
    parser = argparse.ArgumentParser(description="Workflow Dashboard")
    parser.add_argument('--refresh', type=int, default=5, help='Refresh rate in seconds')
    parser.add_argument('--once', action='store_true', help='Show dashboard once and exit')
    args = parser.parse_args()
    
    dashboard = WorkflowDashboard()
    
    if args.once:
        # Just show current state
        tasks = dashboard.get_task_status()
        health = dashboard.get_system_health()
        stats = dashboard.get_workflow_stats()
        
        console.print("\n[bold cyan]Workflow Dashboard[/bold cyan]\n")
        console.print(f"Task Daemon: {health['task_daemon']}")
        console.print(f"Active Tasks: {len([t for t in tasks if t['is_active']])}/{len(tasks)}")
        console.print(f"24hr Success Rate: {(stats['success']/stats['total']*100):.1f}%" if stats['total'] > 0 else "N/A")
    else:
        dashboard.run_live_dashboard(args.refresh)

if __name__ == "__main__":
    main()