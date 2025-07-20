#!/usr/bin/env python3
"""
Advanced File System Monitor for Claude's home directory
Monitors, categorizes, and manages files with automatic organization
"""

import os
import json
import shutil
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import subprocess
import re

class FileSystemMonitor:
    def __init__(self, base_path: str = "/Users/claudemini/Claude"):
        self.base_path = Path(base_path)
        self.state_file = self.base_path / ".fs_monitor_state.json"
        self.archive_dir = self.base_path / "archive"
        self.reports_dir = self.base_path / "reports"
        
        # File categories with patterns and importance
        self.categories = {
            "code": {
                "patterns": [r"\.py$", r"\.js$", r"\.ts$", r"\.sh$", r"\.json$", r"\.toml$", r"\.lock$"],
                "importance": "high",
                "subdirs": ["Code"]
            },
            "security": {
                "patterns": [r"security_", r"audit", r"\.env", r"secrets", r"private_key", r"\.pem$"],
                "importance": "critical",
                "subdirs": []
            },
            "reports": {
                "patterns": [r"report", r"summary", r"analysis", r"\.md$", r"\.txt$"],
                "importance": "medium",
                "subdirs": ["reports"]
            },
            "logs": {
                "patterns": [r"\.log$", r"logs/", r"_log\."],
                "importance": "low",
                "subdirs": ["logs"]
            },
            "data": {
                "patterns": [r"\.csv$", r"\.json$", r"\.db$", r"\.sqlite"],
                "importance": "medium",
                "subdirs": ["data"]
            },
            "temp": {
                "patterns": [r"\.tmp$", r"\.temp$", r"~$", r"\.swp$", r"\.DS_Store"],
                "importance": "low",
                "subdirs": []
            },
            "media": {
                "patterns": [r"\.png$", r"\.jpg$", r"\.jpeg$", r"\.gif$", r"\.mp4$", r"\.mp3$"],
                "importance": "low",
                "subdirs": ["media"]
            },
            "archives": {
                "patterns": [r"\.tar$", r"\.gz$", r"\.zip$", r"\.7z$"],
                "importance": "medium",
                "subdirs": ["archives"]
            }
        }
        
        # Load previous state
        self.state = self.load_state()
        
        # Create necessary directories
        self.archive_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
    
    def load_state(self) -> Dict:
        """Load previous monitoring state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            "last_scan": None,
            "known_files": {},
            "archived_files": [],
            "alerts": []
        }
    
    def save_state(self):
        """Save current monitoring state"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)
    
    def calculate_file_hash(self, filepath: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except:
            return "error"
    
    def categorize_file(self, filepath: Path) -> Tuple[str, str]:
        """Categorize a file based on patterns"""
        filename = filepath.name
        file_path_str = str(filepath)
        
        for category, config in self.categories.items():
            for pattern in config["patterns"]:
                if re.search(pattern, filename, re.IGNORECASE) or re.search(pattern, file_path_str):
                    return category, config["importance"]
        
        return "uncategorized", "low"
    
    def scan_directory(self) -> Dict[str, List[Dict]]:
        """Scan directory and categorize all files"""
        results = {
            "new_files": [],
            "modified_files": [],
            "deleted_files": [],
            "suspicious_files": [],
            "large_files": [],
            "attention_needed": []
        }
        
        current_files = {}
        
        # Walk through directory
        for root, dirs, files in os.walk(self.base_path):
            # Skip hidden directories and archives
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'archive']
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                filepath = Path(root) / file
                
                try:
                    stat = filepath.stat()
                    file_info = {
                        "path": str(filepath),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "category": None,
                        "importance": None,
                        "hash": None
                    }
                    
                    # Categorize file
                    category, importance = self.categorize_file(filepath)
                    file_info["category"] = category
                    file_info["importance"] = importance
                    
                    # Check for large files (>100MB)
                    if stat.st_size > 100 * 1024 * 1024:
                        results["large_files"].append(file_info)
                    
                    # Check for suspicious patterns
                    if self.is_suspicious(filepath):
                        results["suspicious_files"].append(file_info)
                    
                    # Calculate hash for important files
                    if importance in ["critical", "high"]:
                        file_info["hash"] = self.calculate_file_hash(filepath)
                    
                    # Check if file is new or modified
                    rel_path = str(filepath.relative_to(self.base_path))
                    current_files[rel_path] = file_info
                    
                    if rel_path not in self.state["known_files"]:
                        results["new_files"].append(file_info)
                        if importance in ["critical", "high"]:
                            results["attention_needed"].append({
                                **file_info,
                                "reason": "New important file detected"
                            })
                    else:
                        old_info = self.state["known_files"][rel_path]
                        if file_info["modified"] != old_info.get("modified"):
                            results["modified_files"].append(file_info)
                            if importance == "critical":
                                results["attention_needed"].append({
                                    **file_info,
                                    "reason": "Critical file modified"
                                })
                
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
        
        # Check for deleted files
        if "known_files" in self.state:
            for old_path in self.state["known_files"]:
                if old_path not in current_files:
                    old_info = self.state["known_files"][old_path]
                    results["deleted_files"].append(old_info)
                    if old_info.get("importance") in ["critical", "high"]:
                        results["attention_needed"].append({
                            **old_info,
                            "reason": "Important file deleted"
                        })
        
        # Update state
        self.state["known_files"] = current_files
        self.state["last_scan"] = datetime.now().isoformat()
        
        return results
    
    def is_suspicious(self, filepath: Path) -> bool:
        """Check if file matches suspicious patterns"""
        suspicious_patterns = [
            r"\.exe$", r"\.dll$", r"\.bat$",  # Windows executables
            r"malware", r"virus", r"trojan",  # Obvious bad names
            r"base64", r"eval\(", r"exec\(",  # Code injection patterns
            r"\/\.\.\/",  # Path traversal
        ]
        
        filename = filepath.name.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, filename):
                return True
        
        return False
    
    def organize_files(self, results: Dict) -> Dict[str, int]:
        """Organize files based on rules"""
        organized = {
            "archived": 0,
            "moved": 0,
            "cleaned": 0
        }
        
        # Archive old logs
        for file_info in self.state.get("known_files", {}).values():
            if file_info["category"] == "logs":
                filepath = Path(file_info["path"])
                if filepath.exists():
                    # Archive logs older than 7 days
                    modified = datetime.fromisoformat(file_info["modified"])
                    if datetime.now() - modified > timedelta(days=7):
                        archive_path = self.archive_dir / f"logs_{modified.strftime('%Y%m%d')}"
                        archive_path.mkdir(exist_ok=True)
                        try:
                            shutil.move(str(filepath), str(archive_path / filepath.name))
                            organized["archived"] += 1
                        except:
                            pass
        
        # Clean temp files
        temp_files = [f for f in self.state.get("known_files", {}).values() if f["category"] == "temp"]
        for file_info in temp_files:
            filepath = Path(file_info["path"])
            if filepath.exists():
                try:
                    filepath.unlink()
                    organized["cleaned"] += 1
                except:
                    pass
        
        # Move reports to reports directory
        for file_info in results["new_files"]:
            if file_info["category"] == "reports":
                filepath = Path(file_info["path"])
                if filepath.exists() and filepath.parent != self.reports_dir:
                    try:
                        shutil.move(str(filepath), str(self.reports_dir / filepath.name))
                        organized["moved"] += 1
                    except:
                        pass
        
        return organized
    
    def generate_report(self, results: Dict, organized: Dict) -> str:
        """Generate detailed monitoring report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# File System Monitoring Report
Generated: {timestamp}
Base Path: {self.base_path}

## Summary
- New Files: {len(results['new_files'])}
- Modified Files: {len(results['modified_files'])}
- Deleted Files: {len(results['deleted_files'])}
- Suspicious Files: {len(results['suspicious_files'])}
- Large Files (>100MB): {len(results['large_files'])}
- Files Needing Attention: {len(results['attention_needed'])}

## Organization Actions
- Files Archived: {organized['archived']}
- Files Moved: {organized['moved']}
- Temp Files Cleaned: {organized['cleaned']}

## Files Needing Attention
"""
        
        for file in results['attention_needed']:
            report += f"\n### {file['path']}\n"
            report += f"- Reason: {file['reason']}\n"
            report += f"- Category: {file['category']}\n"
            report += f"- Importance: {file['importance']}\n"
            report += f"- Size: {file['size']:,} bytes\n"
            report += f"- Modified: {file['modified']}\n"
        
        if results['suspicious_files']:
            report += "\n## Suspicious Files Detected\n"
            for file in results['suspicious_files']:
                report += f"- {file['path']} (Size: {file['size']:,} bytes)\n"
        
        if results['large_files']:
            report += "\n## Large Files\n"
            for file in results['large_files']:
                size_mb = file['size'] / (1024 * 1024)
                report += f"- {file['path']} ({size_mb:.1f} MB)\n"
        
        # Category breakdown
        report += "\n## File Categories\n"
        category_counts = {}
        for file_info in self.state["known_files"].values():
            cat = file_info["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            report += f"- {category}: {count} files\n"
        
        # Directory size analysis
        report += "\n## Directory Sizes\n"
        dir_sizes = self.get_directory_sizes()
        for dir_path, size in sorted(dir_sizes.items(), key=lambda x: x[1], reverse=True)[:10]:
            size_mb = size / (1024 * 1024)
            report += f"- {dir_path}: {size_mb:.1f} MB\n"
        
        return report
    
    def get_directory_sizes(self) -> Dict[str, int]:
        """Get sizes of subdirectories"""
        dir_sizes = {}
        
        for root, dirs, files in os.walk(self.base_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            dir_path = Path(root)
            total_size = 0
            
            for file in files:
                if not file.startswith('.'):
                    try:
                        filepath = dir_path / file
                        total_size += filepath.stat().st_size
                    except:
                        pass
            
            rel_path = str(dir_path.relative_to(self.base_path))
            if rel_path != '.':
                dir_sizes[rel_path] = total_size
        
        return dir_sizes
    
    def store_memory(self, summary: str):
        """Store monitoring results in memory system"""
        try:
            cmd = [
                "/Users/claudemini/Claude/Code/utils/memory.sh",
                "store",
                summary,
                "--type", "task",
                "--tags", "monitoring filesystem security",
                "--importance", "7"
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except Exception as e:
            print(f"Failed to store memory: {e}")
    
    def run(self):
        """Run the monitoring process"""
        print(f"Starting file system monitoring at {datetime.now()}")
        
        # Scan directory
        results = self.scan_directory()
        
        # Organize files
        organized = self.organize_files(results)
        
        # Generate report
        report = self.generate_report(results, organized)
        
        # Save report
        report_file = self.reports_dir / f"fs_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"Report saved to: {report_file}")
        
        # Save JSON data for further processing
        json_file = self.base_path / f"fs_monitor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": results,
                "organized": organized,
                "state": self.state
            }, f, indent=2, default=str)
        
        # Store summary in memory
        summary = f"File system monitoring completed. Found {len(results['new_files'])} new files, "\
                  f"{len(results['modified_files'])} modified, {len(results['attention_needed'])} need attention. "\
                  f"Organized {sum(organized.values())} files."
        self.store_memory(summary)
        
        # Save state
        self.save_state()
        
        # Print summary
        print("\nMonitoring Summary:")
        print(f"- New files: {len(results['new_files'])}")
        print(f"- Modified files: {len(results['modified_files'])}")
        print(f"- Files needing attention: {len(results['attention_needed'])}")
        print(f"- Files organized: {sum(organized.values())}")
        
        return report_file


if __name__ == "__main__":
    monitor = FileSystemMonitor()
    monitor.run()