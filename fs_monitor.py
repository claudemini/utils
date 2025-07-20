#!/usr/bin/env python3
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
from collections import defaultdict

class FileSystemMonitor:
    def __init__(self, base_path="/Users/claudemini/Claude"):
        self.base_path = Path(base_path)
        self.state_file = self.base_path / ".fs_monitor_state.json"
        self.report_file = self.base_path / "fs_monitor_report.json"
        self.previous_state = self.load_state()
        self.current_state = {}
        
        # File categories
        self.categories = {
            'logs': ['.log'],
            'reports': ['.md', '.txt'],
            'data': ['.json', '.csv'],
            'code': ['.py', '.sh', '.js', '.ts'],
            'config': ['.env', '.toml', '.yaml', '.yml'],
            'sensitive': ['.env', 'secret', 'key', 'token', 'password'],
            'temporary': ['.tmp', '.temp', '.swp', '.DS_Store']
        }
        
        # Directories to monitor
        self.watch_dirs = [
            'Code',
            'logs',
            '.'
        ]
        
    def load_state(self):
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {}
    
    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.current_state, f, indent=2)
    
    def get_file_hash(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def categorize_file(self, filepath):
        path = Path(filepath)
        categories = []
        
        # Check by extension
        for category, extensions in self.categories.items():
            if any(str(path).endswith(ext) for ext in extensions):
                categories.append(category)
        
        # Check for sensitive content
        if any(keyword in str(path).lower() for keyword in ['secret', 'key', 'token', 'password']):
            categories.append('sensitive')
            
        return categories if categories else ['other']
    
    def scan_directory(self):
        current_time = datetime.now()
        
        for watch_dir in self.watch_dirs:
            dir_path = self.base_path / watch_dir if watch_dir != '.' else self.base_path
            
            if not dir_path.exists():
                continue
                
            for root, dirs, files in os.walk(dir_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    filepath = Path(root) / file
                    
                    # Skip certain files
                    if file.startswith('.') and file not in ['.env']:
                        continue
                    
                    try:
                        stat = filepath.stat()
                        file_info = {
                            'path': str(filepath),
                            'size': stat.st_size,
                            'modified': stat.st_mtime,
                            'created': stat.st_ctime,
                            'hash': self.get_file_hash(filepath),
                            'categories': self.categorize_file(filepath)
                        }
                        
                        self.current_state[str(filepath)] = file_info
                    except:
                        pass
    
    def analyze_changes(self):
        changes = {
            'new_files': [],
            'modified_files': [],
            'deleted_files': [],
            'large_files': [],
            'sensitive_files': [],
            'files_needing_attention': []
        }
        
        # Find new and modified files
        for filepath, info in self.current_state.items():
            if filepath not in self.previous_state:
                changes['new_files'].append(info)
            elif info['hash'] != self.previous_state[filepath].get('hash'):
                changes['modified_files'].append(info)
            
            # Check for large files (>10MB)
            if info['size'] > 10 * 1024 * 1024:
                changes['large_files'].append(info)
            
            # Check for sensitive files
            if 'sensitive' in info['categories']:
                changes['sensitive_files'].append(info)
        
        # Find deleted files
        for filepath in self.previous_state:
            if filepath not in self.current_state:
                changes['deleted_files'].append({'path': filepath})
        
        # Identify files needing attention
        one_day_ago = time.time() - 86400
        for info in self.current_state.values():
            # Old log files
            if 'logs' in info['categories'] and info['modified'] < one_day_ago:
                changes['files_needing_attention'].append({
                    'file': info,
                    'reason': 'Old log file - consider archiving'
                })
            
            # Large JSON files
            if '.json' in info['path'] and info['size'] > 5 * 1024 * 1024:
                changes['files_needing_attention'].append({
                    'file': info,
                    'reason': 'Large JSON file - consider compression'
                })
        
        return changes
    
    def generate_report(self, changes):
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_files': len(self.current_state),
                'new_files': len(changes['new_files']),
                'modified_files': len(changes['modified_files']),
                'deleted_files': len(changes['deleted_files']),
                'files_by_category': defaultdict(int)
            },
            'changes': changes
        }
        
        # Count files by category
        for info in self.current_state.values():
            for category in info['categories']:
                report['summary']['files_by_category'][category] += 1
        
        report['summary']['files_by_category'] = dict(report['summary']['files_by_category'])
        
        # Save report
        with open(self.report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Create markdown summary
        self.create_markdown_summary(report)
        
        return report
    
    def create_markdown_summary(self, report):
        summary_file = self.base_path / f"fs_monitor_summary_{datetime.now().strftime('%Y%m%d')}.md"
        
        with open(summary_file, 'w') as f:
            f.write(f"# File System Monitor Report\n")
            f.write(f"Generated: {report['timestamp']}\n\n")
            
            f.write("## Summary\n")
            f.write(f"- Total files monitored: {report['summary']['total_files']}\n")
            f.write(f"- New files: {report['summary']['new_files']}\n")
            f.write(f"- Modified files: {report['summary']['modified_files']}\n")
            f.write(f"- Deleted files: {report['summary']['deleted_files']}\n\n")
            
            f.write("## Files by Category\n")
            for category, count in report['summary']['files_by_category'].items():
                f.write(f"- {category}: {count}\n")
            
            if report['changes']['files_needing_attention']:
                f.write("\n## Files Needing Attention\n")
                for item in report['changes']['files_needing_attention']:
                    f.write(f"- {item['file']['path']}: {item['reason']}\n")
            
            if report['changes']['sensitive_files']:
                f.write("\n## Sensitive Files Detected\n")
                for file in report['changes']['sensitive_files']:
                    f.write(f"- {file['path']} (size: {file['size']} bytes)\n")
    
    def monitor(self):
        print(f"Starting file system monitor for {self.base_path}")
        self.scan_directory()
        changes = self.analyze_changes()
        report = self.generate_report(changes)
        self.save_state()
        
        print(f"\n=== File System Monitor Report ===")
        print(f"Total files: {report['summary']['total_files']}")
        print(f"New files: {report['summary']['new_files']}")
        print(f"Modified files: {report['summary']['modified_files']}")
        print(f"Files needing attention: {len(changes['files_needing_attention'])}")
        
        if changes['files_needing_attention']:
            print("\nFiles needing attention:")
            for item in changes['files_needing_attention'][:5]:
                print(f"  - {item['file']['path']}: {item['reason']}")
        
        print(f"\nFull report saved to: {self.report_file}")
        return report

if __name__ == "__main__":
    monitor = FileSystemMonitor()
    monitor.monitor()