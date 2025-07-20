#!/usr/bin/env python3
"""
File System Activity Monitor - Comprehensive monitoring for Claude's home directory
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import hashlib
import subprocess
from typing import Dict, List, Set, Tuple

class FileSystemActivityMonitor:
    def __init__(self, base_path: str = "/Users/claudemini/Claude"):
        self.base_path = Path(base_path)
        self.state_file = self.base_path / ".fs_activity_state.json"
        self.report_file = self.base_path / f"fs_activity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.previous_state = self.load_state()
        self.current_state = {}
        
        # Categories for file organization
        self.file_categories = {
            'code': {'.py', '.js', '.ts', '.jsx', '.tsx', '.sh', '.sql', '.html', '.css'},
            'data': {'.json', '.csv', '.xlsx', '.db', '.sqlite'},
            'docs': {'.md', '.txt', '.pdf', '.doc', '.docx'},
            'logs': {'.log'},
            'images': {'.png', '.jpg', '.jpeg', '.gif', '.svg'},
            'temp': {'.tmp', '.cache', '.pyc'},
            'git': {'.git'}
        }
        
        # Important directories to monitor
        self.important_dirs = {
            'code': self.base_path / 'Code',
            'logs': self.base_path / 'logs',
            'utils': self.base_path / 'Code/utils'
        }
        
    def load_state(self) -> dict:
        """Load previous monitoring state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_state(self):
        """Save current monitoring state"""
        with open(self.state_file, 'w') as f:
            json.dump(self.current_state, f, indent=2, default=str)
    
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate file hash for change detection"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
    
    def categorize_file(self, file_path: Path) -> str:
        """Categorize file by extension"""
        ext = file_path.suffix.lower()
        for category, extensions in self.file_categories.items():
            if ext in extensions:
                return category
        return 'other'
    
    def scan_directory(self) -> Dict:
        """Comprehensive directory scan"""
        scan_results = {
            'timestamp': datetime.now().isoformat(),
            'files': {},
            'directories': {},
            'statistics': defaultdict(int),
            'large_files': [],
            'recent_changes': [],
            'temp_files': [],
            'security_concerns': []
        }
        
        # Walk through directory
        for root, dirs, files in os.walk(self.base_path):
            root_path = Path(root)
            
            # Skip .git directories for performance
            if '.git' in root_path.parts:
                continue
                
            # Process directories
            for dir_name in dirs:
                dir_path = root_path / dir_name
                scan_results['directories'][str(dir_path)] = {
                    'mtime': dir_path.stat().st_mtime,
                    'files_count': len(list(dir_path.iterdir()))
                }
            
            # Process files
            for file_name in files:
                file_path = root_path / file_name
                try:
                    stat = file_path.stat()
                    file_info = {
                        'size': stat.st_size,
                        'mtime': stat.st_mtime,
                        'category': self.categorize_file(file_path),
                        'hash': self.get_file_hash(file_path) if stat.st_size < 1_000_000 else None
                    }
                    
                    scan_results['files'][str(file_path)] = file_info
                    scan_results['statistics'][file_info['category']] += 1
                    scan_results['statistics']['total_size'] += stat.st_size
                    
                    # Track large files (>10MB)
                    if stat.st_size > 10_485_760:
                        scan_results['large_files'].append({
                            'path': str(file_path),
                            'size': stat.st_size,
                            'size_mb': round(stat.st_size / 1_048_576, 2)
                        })
                    
                    # Track recent changes (last 24 hours)
                    if datetime.fromtimestamp(stat.st_mtime) > datetime.now() - timedelta(days=1):
                        scan_results['recent_changes'].append({
                            'path': str(file_path),
                            'mtime': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'category': file_info['category']
                        })
                    
                    # Track temp files
                    if file_info['category'] == 'temp' or file_name.startswith('.'):
                        scan_results['temp_files'].append(str(file_path))
                    
                    # Security checks
                    if file_name in ['.env', 'secrets.json', 'credentials.json']:
                        scan_results['security_concerns'].append({
                            'path': str(file_path),
                            'reason': 'sensitive file detected',
                            'permissions': oct(stat.st_mode)[-3:]
                        })
                        
                except Exception as e:
                    scan_results['statistics']['errors'] += 1
        
        self.current_state = scan_results
        return scan_results
    
    def detect_changes(self) -> Dict:
        """Detect changes since last scan"""
        changes = {
            'new_files': [],
            'deleted_files': [],
            'modified_files': [],
            'moved_files': []
        }
        
        if not self.previous_state:
            return changes
        
        prev_files = set(self.previous_state.get('files', {}).keys())
        curr_files = set(self.current_state.get('files', {}).keys())
        
        # New files
        changes['new_files'] = list(curr_files - prev_files)
        
        # Deleted files
        changes['deleted_files'] = list(prev_files - curr_files)
        
        # Modified files
        for file_path in curr_files & prev_files:
            curr_info = self.current_state['files'][file_path]
            prev_info = self.previous_state['files'][file_path]
            
            if curr_info.get('hash') and prev_info.get('hash'):
                if curr_info['hash'] != prev_info['hash']:
                    changes['modified_files'].append(file_path)
            elif curr_info['mtime'] != prev_info['mtime']:
                changes['modified_files'].append(file_path)
        
        return changes
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on scan results"""
        recommendations = []
        
        # Large files
        if self.current_state['large_files']:
            total_size = sum(f['size'] for f in self.current_state['large_files'])
            recommendations.append(
                f"Found {len(self.current_state['large_files'])} large files "
                f"(>{10}MB) totaling {round(total_size/1_048_576, 2)}MB"
            )
        
        # Temp files
        temp_count = len(self.current_state['temp_files'])
        if temp_count > 100:
            recommendations.append(
                f"High number of temporary files detected ({temp_count}). "
                "Consider running cleanup."
            )
        
        # Security
        if self.current_state['security_concerns']:
            recommendations.append(
                f"Security review needed: {len(self.current_state['security_concerns'])} "
                "sensitive files detected"
            )
        
        # Git repositories
        git_dirs = [d for d in self.current_state['directories'] if '.git' in d]
        if git_dirs:
            recommendations.append(
                f"Found {len(git_dirs)} git repositories. "
                "Ensure all changes are committed and pushed."
            )
        
        return recommendations
    
    def generate_report(self) -> Dict:
        """Generate comprehensive activity report"""
        scan_results = self.scan_directory()
        changes = self.detect_changes()
        recommendations = self.generate_recommendations()
        
        report = {
            'scan_summary': {
                'timestamp': scan_results['timestamp'],
                'total_files': len(scan_results['files']),
                'total_directories': len(scan_results['directories']),
                'total_size_mb': round(scan_results['statistics']['total_size'] / 1_048_576, 2),
                'file_categories': dict(scan_results['statistics'])
            },
            'recent_activity': {
                'files_modified_24h': len(scan_results['recent_changes']),
                'new_files': len(changes['new_files']),
                'deleted_files': len(changes['deleted_files']),
                'modified_files': len(changes['modified_files'])
            },
            'attention_needed': {
                'large_files': scan_results['large_files'][:10],  # Top 10
                'temp_files_count': len(scan_results['temp_files']),
                'security_concerns': scan_results['security_concerns']
            },
            'recommendations': recommendations,
            'detailed_changes': changes if len(changes['new_files']) < 50 else {
                'summary': 'Too many changes to list individually',
                'counts': {k: len(v) for k, v in changes.items()}
            }
        }
        
        # Save report
        with open(self.report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save state for next run
        self.save_state()
        
        return report
    
    def print_summary(self, report: Dict):
        """Print human-readable summary"""
        print("=== File System Activity Report ===")
        print(f"Timestamp: {report['scan_summary']['timestamp']}")
        print(f"\nSummary:")
        print(f"  Total files: {report['scan_summary']['total_files']}")
        print(f"  Total size: {report['scan_summary']['total_size_mb']} MB")
        print(f"  Files modified (24h): {report['recent_activity']['files_modified_24h']}")
        
        print(f"\nChanges detected:")
        for change_type, count in report['recent_activity'].items():
            if count > 0:
                print(f"  {change_type}: {count}")
        
        if report['attention_needed']['large_files']:
            print(f"\nLarge files found:")
            for lf in report['attention_needed']['large_files'][:5]:
                print(f"  {lf['size_mb']} MB - {Path(lf['path']).name}")
        
        if report['attention_needed']['security_concerns']:
            print(f"\n⚠️  Security concerns:")
            for sc in report['attention_needed']['security_concerns']:
                print(f"  {sc['path']} - {sc['reason']}")
        
        if report['recommendations']:
            print(f"\nRecommendations:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
        
        print(f"\nFull report saved to: {self.report_file}")

def main():
    monitor = FileSystemActivityMonitor()
    report = monitor.generate_report()
    monitor.print_summary(report)
    
    # Store activity in memory
    memory_cmd = [
        "/Users/claudemini/Claude/Code/utils/memory.sh", 
        "store",
        f"File system scan: {report['scan_summary']['total_files']} files, "
        f"{report['recent_activity']['files_modified_24h']} modified in 24h, "
        f"{len(report['attention_needed']['large_files'])} large files",
        "--type", "daily",
        "--tags", "filesystem monitoring",
        "--importance", "5"
    ]
    subprocess.run(memory_cmd)

if __name__ == "__main__":
    main()