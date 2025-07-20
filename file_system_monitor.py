#!/usr/bin/env python3
"""
Enhanced File System Monitor for Claude's Home Directory
Monitors file system activity, categorizes files, and provides actionable insights
"""

import os
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import subprocess
import hashlib

class FileSystemMonitor:
    def __init__(self, base_path="/Users/claudemini/Claude"):
        self.base_path = Path(base_path)
        self.state_file = self.base_path / ".fs_monitor_state.json"
        self.report_dir = self.base_path / "reports"
        self.report_dir.mkdir(exist_ok=True)
        
        # File categories by importance
        self.categories = {
            "critical": [".env", "CLAUDE.md", ".ssh", "private_key", "secret"],
            "code": [".py", ".js", ".ts", ".sh", ".sql"],
            "config": [".json", ".yaml", ".yml", ".toml", ".ini"],
            "docs": [".md", ".txt", ".pdf", ".doc"],
            "data": [".csv", ".xlsx", ".db", ".sqlite"],
            "logs": [".log", ".out"],
            "temp": [".tmp", ".cache", "~", ".swp"],
            "media": [".png", ".jpg", ".jpeg", ".gif", ".mp4"],
            "archives": [".zip", ".tar", ".gz", ".bz2"]
        }
        
        # Directories to monitor closely
        self.important_dirs = [
            "Code", "logs", "reports", ".claude", "archive"
        ]
        
        # Load previous state
        self.load_state()
    
    def load_state(self):
        """Load previous monitoring state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)
        else:
            self.state = {
                "last_scan": None,
                "file_hashes": {},
                "known_issues": []
            }
    
    def save_state(self):
        """Save current monitoring state"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)
    
    def categorize_file(self, file_path):
        """Categorize a file based on its type and content"""
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        name = file_path.name.lower()
        
        # Check for critical files
        for pattern in self.categories["critical"]:
            if pattern in name:
                return "critical"
        
        # Check by extension
        for category, extensions in self.categories.items():
            if ext in extensions:
                return category
        
        return "other"
    
    def get_file_info(self, file_path):
        """Get detailed information about a file"""
        try:
            stat = file_path.stat()
            return {
                "path": str(file_path),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "created": datetime.fromtimestamp(stat.st_ctime),
                "category": self.categorize_file(file_path),
                "permissions": oct(stat.st_mode)[-3:]
            }
        except Exception as e:
            return None
    
    def scan_directory(self):
        """Scan the entire directory structure"""
        results = {
            "total_files": 0,
            "total_size": 0,
            "by_category": defaultdict(list),
            "new_files": [],
            "modified_files": [],
            "deleted_files": [],
            "large_files": [],
            "old_logs": [],
            "temp_files": [],
            "security_concerns": []
        }
        
        current_files = {}
        
        # Walk through directory
        for root, dirs, files in os.walk(self.base_path):
            # Skip .venv and .git directories
            dirs[:] = [d for d in dirs if d not in ['.venv', '.git', '__pycache__', '.DS_Store']]
            
            for file in files:
                if file.startswith('.DS_Store'):
                    continue
                    
                file_path = Path(root) / file
                file_info = self.get_file_info(file_path)
                
                if not file_info:
                    continue
                
                results["total_files"] += 1
                results["total_size"] += file_info["size"]
                
                # Categorize file
                category = file_info["category"]
                results["by_category"][category].append(file_info)
                
                # Check for new/modified files
                file_hash = self.get_file_hash(file_path)
                current_files[str(file_path)] = file_hash
                
                if str(file_path) not in self.state.get("file_hashes", {}):
                    results["new_files"].append(file_info)
                elif self.state["file_hashes"][str(file_path)] != file_hash:
                    results["modified_files"].append(file_info)
                
                # Check for large files (>10MB)
                if file_info["size"] > 10 * 1024 * 1024:
                    results["large_files"].append(file_info)
                
                # Check for old logs (>7 days)
                if category == "logs" and (datetime.now() - file_info["modified"]).days > 7:
                    results["old_logs"].append(file_info)
                
                # Check for temp files
                if category == "temp":
                    results["temp_files"].append(file_info)
                
                # Security checks
                if category == "critical" and file_info["permissions"] != "600":
                    results["security_concerns"].append({
                        "file": file_info,
                        "issue": f"Critical file has loose permissions: {file_info['permissions']}"
                    })
        
        # Check for deleted files
        for old_file in self.state.get("file_hashes", {}).keys():
            if old_file not in current_files:
                results["deleted_files"].append({"path": old_file})
        
        # Update state
        self.state["file_hashes"] = current_files
        self.state["last_scan"] = datetime.now().isoformat()
        
        return results
    
    def get_file_hash(self, file_path):
        """Get hash of file for change detection"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read(1024)).hexdigest()
        except:
            return None
    
    def generate_report(self, results):
        """Generate a detailed report"""
        report = []
        report.append("# File System Monitoring Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Base Path: {self.base_path}\n")
        
        # Summary
        report.append("## Summary")
        report.append(f"- Total Files: {results['total_files']:,}")
        report.append(f"- Total Size: {self.format_size(results['total_size'])}")
        report.append(f"- New Files: {len(results['new_files'])}")
        report.append(f"- Modified Files: {len(results['modified_files'])}")
        report.append(f"- Deleted Files: {len(results['deleted_files'])}\n")
        
        # Files by category
        report.append("## Files by Category")
        for category, files in results["by_category"].items():
            total_size = sum(f["size"] for f in files)
            report.append(f"- **{category.title()}**: {len(files)} files ({self.format_size(total_size)})")
        
        # Attention needed
        if results["security_concerns"]:
            report.append("\n## 🚨 Security Concerns")
            for concern in results["security_concerns"]:
                report.append(f"- {concern['issue']}")
                report.append(f"  - File: {concern['file']['path']}")
        
        if results["large_files"]:
            report.append("\n## Large Files (>10MB)")
            for file in sorted(results["large_files"], key=lambda x: x["size"], reverse=True)[:10]:
                report.append(f"- {file['path']}: {self.format_size(file['size'])}")
        
        if results["old_logs"]:
            report.append("\n## Old Log Files (>7 days)")
            for file in results["old_logs"]:
                age = (datetime.now() - file["modified"]).days
                report.append(f"- {file['path']}: {age} days old")
        
        if results["temp_files"]:
            report.append("\n## Temporary Files")
            for file in results["temp_files"]:
                report.append(f"- {file['path']}: {self.format_size(file['size'])}")
        
        # Recent activity
        if results["new_files"]:
            report.append("\n## New Files")
            for file in results["new_files"][:20]:
                report.append(f"- {file['path']} ({file['category']})")
        
        if results["modified_files"]:
            report.append("\n## Recently Modified Files")
            for file in sorted(results["modified_files"], key=lambda x: x["modified"], reverse=True)[:20]:
                report.append(f"- {file['path']} - {file['modified'].strftime('%Y-%m-%d %H:%M')}")
        
        # Recommendations
        report.append("\n## Recommendations")
        
        if results["old_logs"]:
            report.append("- Archive or delete old log files to save space")
        
        if results["temp_files"]:
            report.append("- Clean up temporary files")
        
        if results["large_files"]:
            report.append("- Review large files and consider archiving if not actively used")
        
        if results["security_concerns"]:
            report.append("- Fix file permissions on critical files immediately")
        
        # Directory usage
        report.append("\n## Directory Usage")
        for dir_name in self.important_dirs:
            dir_path = self.base_path / dir_name
            if dir_path.exists():
                size = self.get_directory_size(dir_path)
                report.append(f"- {dir_name}: {self.format_size(size)}")
        
        return "\n".join(report)
    
    def get_directory_size(self, path):
        """Get total size of directory"""
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir() and entry.name not in ['.venv', '.git', '__pycache__']:
                    total += self.get_directory_size(entry.path)
        except:
            pass
        return total
    
    def format_size(self, bytes):
        """Format bytes to human readable size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"
    
    def archive_old_files(self):
        """Archive old files to save space"""
        archive_dir = self.base_path / "archive"
        archive_dir.mkdir(exist_ok=True)
        
        # Archive old logs
        for log_dir in [self.base_path / "logs", self.base_path / "Code" / "utils" / "logs"]:
            if log_dir.exists():
                for log_file in log_dir.glob("*.log"):
                    if (datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)).days > 30:
                        archive_path = archive_dir / f"{log_file.name}.{datetime.now().strftime('%Y%m%d')}"
                        log_file.rename(archive_path)
    
    def run(self):
        """Run the monitoring process"""
        print("Starting file system scan...")
        results = self.scan_directory()
        
        # Generate report
        report = self.generate_report(results)
        
        # Save report
        report_file = self.report_dir / f"fs_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Save state
        self.save_state()
        
        # Print summary
        print(f"\nMonitoring complete!")
        print(f"Report saved to: {report_file}")
        print(f"\nQuick Summary:")
        print(f"- Total Files: {results['total_files']:,}")
        print(f"- New Files: {len(results['new_files'])}")
        print(f"- Security Concerns: {len(results['security_concerns'])}")
        
        return report_file

if __name__ == "__main__":
    monitor = FileSystemMonitor()
    monitor.run()