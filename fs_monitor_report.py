#!/usr/bin/env python3
"""
File System Monitor Report Generator
Monitors and reports on file system activity in Claude Mini's home directory
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import subprocess

HOME_DIR = "/Users/claudemini/Claude"
WATCH_DIRS = [
    HOME_DIR,
    f"{HOME_DIR}/Code",
    f"{HOME_DIR}/Code/utils",
    f"{HOME_DIR}/logs"
]

def categorize_file(file_path):
    """Categorize files by type and importance"""
    file_path = str(file_path).lower()
    name = os.path.basename(file_path)
    
    # High importance files
    if '.env' in name or 'secret' in name or 'key' in name:
        return 'sensitive', 10
    
    # Logs and monitoring
    if any(x in file_path for x in ['log', 'monitor', 'report', 'audit']):
        return 'monitoring', 8
    
    # Code files
    if any(file_path.endswith(x) for x in ['.py', '.js', '.ts', '.sh']):
        return 'code', 7
    
    # Data files
    if any(file_path.endswith(x) for x in ['.json', '.csv', '.db']):
        return 'data', 6
    
    # Documentation
    if file_path.endswith('.md') or file_path.endswith('.txt'):
        return 'docs', 5
    
    # Large files
    try:
        size = os.path.getsize(file_path)
        if size > 10 * 1024 * 1024:  # 10MB
            return 'large_file', 7
    except:
        pass
    
    return 'other', 3

def scan_directory_changes(since_hours=24):
    """Scan for recent file changes"""
    cutoff_time = datetime.now() - timedelta(hours=since_hours)
    changes = {
        'new_files': [],
        'modified_files': [],
        'large_files': [],
        'sensitive_files': [],
        'monitoring_files': []
    }
    
    for watch_dir in WATCH_DIRS:
        if not os.path.exists(watch_dir):
            continue
            
        for root, dirs, files in os.walk(watch_dir):
            # Skip hidden and virtual env directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, file)
                try:
                    stat = os.stat(file_path)
                    mtime = datetime.fromtimestamp(stat.st_mtime)
                    
                    category, importance = categorize_file(file_path)
                    
                    file_info = {
                        'path': file_path.replace(HOME_DIR + '/', ''),
                        'size_mb': round(stat.st_size / (1024 * 1024), 2),
                        'modified': mtime.isoformat(),
                        'category': category,
                        'importance': importance
                    }
                    
                    if mtime > cutoff_time:
                        if datetime.fromtimestamp(stat.st_ctime) > cutoff_time:
                            changes['new_files'].append(file_info)
                        else:
                            changes['modified_files'].append(file_info)
                    
                    if stat.st_size > 5 * 1024 * 1024:  # 5MB
                        changes['large_files'].append(file_info)
                    
                    if category == 'sensitive':
                        changes['sensitive_files'].append(file_info)
                    
                    if category == 'monitoring':
                        changes['monitoring_files'].append(file_info)
                        
                except Exception as e:
                    continue
    
    # Sort by importance and modification time
    for key in changes:
        changes[key].sort(key=lambda x: (-x['importance'], x['modified']), reverse=True)
    
    return changes

def generate_report():
    """Generate comprehensive file system activity report"""
    report_time = datetime.now()
    changes = scan_directory_changes(24)
    
    # Check disk usage
    disk_usage = subprocess.check_output(['df', '-h', HOME_DIR]).decode().split('\n')[1].split()
    
    report = {
        'timestamp': report_time.isoformat(),
        'disk_usage': {
            'filesystem': disk_usage[0],
            'size': disk_usage[1],
            'used': disk_usage[2],
            'available': disk_usage[3],
            'percent_used': disk_usage[4]
        },
        'summary': {
            'new_files': len(changes['new_files']),
            'modified_files': len(changes['modified_files']),
            'large_files': len(changes['large_files']),
            'sensitive_files': len(changes['sensitive_files']),
            'monitoring_files': len(changes['monitoring_files'])
        },
        'files_needing_attention': [],
        'recent_activity': changes
    }
    
    # Identify files needing attention
    attention_needed = []
    
    # Check for unusually large log files
    for file_info in changes['monitoring_files']:
        if file_info['size_mb'] > 10:
            attention_needed.append({
                'file': file_info['path'],
                'reason': 'Large log file - consider rotation',
                'size': f"{file_info['size_mb']} MB"
            })
    
    # Check for sensitive files
    for file_info in changes['sensitive_files']:
        attention_needed.append({
            'file': file_info['path'],
            'reason': 'Sensitive file detected - verify permissions',
            'importance': 'HIGH'
        })
    
    # Check for rapid file growth
    for file_info in changes['modified_files']:
        if 'log' in file_info['path'] and file_info['size_mb'] > 5:
            attention_needed.append({
                'file': file_info['path'],
                'reason': 'Log file growing rapidly',
                'size': f"{file_info['size_mb']} MB"
            })
    
    report['files_needing_attention'] = attention_needed
    
    # Save report
    report_path = f"{HOME_DIR}/filesystem_monitor_report_{report_time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Also create markdown summary
    md_report = f"""# File System Activity Report
Generated: {report_time.strftime('%Y-%m-%d %H:%M:%S')}

## Disk Usage
- Used: {disk_usage[2]} of {disk_usage[1]} ({disk_usage[4]})
- Available: {disk_usage[3]}

## Summary (Last 24 Hours)
- New Files: {report['summary']['new_files']}
- Modified Files: {report['summary']['modified_files']}
- Large Files (>5MB): {report['summary']['large_files']}
- Sensitive Files: {report['summary']['sensitive_files']}
- Monitoring/Log Files: {report['summary']['monitoring_files']}

## Files Needing Attention
"""
    
    if attention_needed:
        for item in attention_needed:
            md_report += f"\n### {item['file']}\n"
            md_report += f"- **Reason**: {item['reason']}\n"
            if 'size' in item:
                md_report += f"- **Size**: {item['size']}\n"
            if 'importance' in item:
                md_report += f"- **Importance**: {item['importance']}\n"
    else:
        md_report += "\nNo files requiring immediate attention.\n"
    
    md_report += "\n## Recent Activity\n"
    
    if changes['new_files']:
        md_report += "\n### New Files\n"
        for f in changes['new_files'][:10]:
            md_report += f"- `{f['path']}` ({f['category']}, {f['size_mb']}MB)\n"
    
    if changes['modified_files']:
        md_report += "\n### Recently Modified\n"
        for f in changes['modified_files'][:10]:
            md_report += f"- `{f['path']}` ({f['category']}, {f['size_mb']}MB)\n"
    
    md_path = f"{HOME_DIR}/filesystem_monitor_summary_{report_time.strftime('%Y%m%d')}.md"
    with open(md_path, 'w') as f:
        f.write(md_report)
    
    print(f"Report generated: {report_path}")
    print(f"Summary saved: {md_path}")
    
    return report

if __name__ == "__main__":
    report = generate_report()
    
    # Print summary to console
    print("\n=== FILE SYSTEM MONITOR ===")
    print(f"Disk Usage: {report['disk_usage']['percent_used']} used")
    print(f"New Files: {report['summary']['new_files']}")
    print(f"Modified Files: {report['summary']['modified_files']}")
    
    if report['files_needing_attention']:
        print("\n⚠️  FILES NEEDING ATTENTION:")
        for item in report['files_needing_attention']:
            print(f"  - {item['file']}: {item['reason']}")
    def __init__(self):
        self.base_path = Path("/Users/claudemini/Claude")
        self.report_path = self.base_path / "filesystem_activity_report.json"
        self.categories = {
            "security": [".log", ".audit", "security", "monitor"],
            "code": [".py", ".sh", ".js", ".ts", ".sql"],
            "config": [".json", ".yaml", ".yml", ".toml", ".env"],
            "docs": [".md", ".txt", ".pdf"],
            "data": [".csv", ".json", ".db"],
            "temp": [".tmp", ".temp", ".bak", "~"],
            "large": []  # Files > 10MB
        }
        
    def scan_directory(self):
        """Scan directory and categorize files"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": defaultdict(int),
            "recent_files": [],
            "large_files": [],
            "attention_needed": [],
            "by_category": defaultdict(list)
        }
        
        # Find recent files (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for root, dirs, files in os.walk(self.base_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = Path(root) / file
                try:
                    stat = file_path.stat()
                    mod_time = datetime.fromtimestamp(stat.st_mtime)
                    size_mb = stat.st_size / (1024 * 1024)
                    
                    # Categorize file
                    category = self.categorize_file(file_path)
                    report["by_category"][category].append({
                        "path": str(file_path.relative_to(self.base_path)),
                        "size": f"{size_mb:.2f} MB",
                        "modified": mod_time.isoformat()
                    })
                    
                    # Recent files
                    if mod_time > cutoff_time:
                        report["recent_files"].append({
                            "path": str(file_path.relative_to(self.base_path)),
                            "category": category,
                            "modified": mod_time.isoformat(),
                            "size": f"{size_mb:.2f} MB"
                        })
                    
                    # Large files
                    if size_mb > 10:
                        report["large_files"].append({
                            "path": str(file_path.relative_to(self.base_path)),
                            "size": f"{size_mb:.2f} MB"
                        })
                        
                    # Files needing attention
                    if category == "temp" or (category == "logs" and size_mb > 50):
                        report["attention_needed"].append({
                            "path": str(file_path.relative_to(self.base_path)),
                            "reason": "Temporary file" if category == "temp" else "Large log file",
                            "size": f"{size_mb:.2f} MB"
                        })
                        
                    report["summary"][category] += 1
                    
                except Exception as e:
                    continue
        
        return report
    
    def categorize_file(self, file_path):
        """Categorize file based on extension and name"""
        name = file_path.name.lower()
        ext = file_path.suffix.lower()
        
        for category, patterns in self.categories.items():
            if category == "large":
                continue
            for pattern in patterns:
                if pattern in name or ext == pattern:
                    return category
        
        if ext == ".log":
            return "logs"
        
        return "other"
    
    def generate_report(self):
        """Generate and save monitoring report"""
        report = self.scan_directory()
        
        # Sort recent files by modification time
        report["recent_files"].sort(key=lambda x: x["modified"], reverse=True)
        
        # Save report
        with open(self.report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate summary
        print(f"\n=== File System Activity Report ===")
        print(f"Generated: {report['timestamp']}")
        print(f"\nSummary by Category:")
        for category, count in sorted(report["summary"].items()):
            print(f"  {category}: {count} files")
        
        print(f"\nRecent Activity (last 24 hours): {len(report['recent_files'])} files")
        for file in report["recent_files"][:10]:
            print(f"  - {file['path']} ({file['category']}) - {file['size']}")
        
        if report["attention_needed"]:
            print(f"\nFiles Needing Attention:")
            for file in report["attention_needed"]:
                print(f"  - {file['path']} - {file['reason']} ({file['size']})")
        
        if report["large_files"]:
            print(f"\nLarge Files (>10MB):")
            for file in report["large_files"]:
                print(f"  - {file['path']} - {file['size']}")
        
        return report

if __name__ == "__main__":
    monitor = FileSystemMonitor()
    monitor.generate_report()