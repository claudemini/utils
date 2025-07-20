#!/usr/bin/env python3
import os
import json
import datetime
import time
from pathlib import Path
from typing import Dict, List, Set
import hashlib

class FileSystemMonitor:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.state_file = self.base_path / ".filesystem_state.json"
        self.ignore_patterns = {
            ".DS_Store", "__pycache__", ".venv", "node_modules", 
            ".git", "*.pyc", "*.log", "*.tmp", "*.cache"
        }
        self.important_extensions = {
            ".py", ".sh", ".json", ".md", ".txt", ".sql", ".toml", ".yaml", ".yml"
        }
        self.previous_state = self.load_state()
        
    def load_state(self) -> Dict:
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_state(self, state: Dict):
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def should_ignore(self, path: Path) -> bool:
        for pattern in self.ignore_patterns:
            if pattern.startswith("*"):
                if path.name.endswith(pattern[1:]):
                    return True
            elif pattern in str(path):
                return True
        return False
    
    def get_file_info(self, path: Path) -> Dict:
        stat = path.stat()
        return {
            "size": stat.st_size,
            "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "type": self.categorize_file(path),
            "hash": self.get_file_hash(path) if path.stat().st_size < 1024*1024 else None
        }
    
    def get_file_hash(self, path: Path) -> str:
        hash_md5 = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def categorize_file(self, path: Path) -> str:
        if path.is_dir():
            return "directory"
        
        ext = path.suffix.lower()
        categories = {
            ".py": "code",
            ".sh": "script",
            ".json": "data",
            ".md": "documentation",
            ".txt": "text",
            ".sql": "database",
            ".toml": "config",
            ".yaml": "config",
            ".yml": "config",
            ".log": "log",
            ".env": "sensitive"
        }
        return categories.get(ext, "other")
    
    def scan_directory(self) -> Dict:
        current_state = {}
        
        for root, dirs, files in os.walk(self.base_path):
            root_path = Path(root)
            
            # Filter directories
            dirs[:] = [d for d in dirs if not self.should_ignore(root_path / d)]
            
            for file in files:
                file_path = root_path / file
                if not self.should_ignore(file_path):
                    relative_path = file_path.relative_to(self.base_path)
                    try:
                        current_state[str(relative_path)] = self.get_file_info(file_path)
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")
        
        return current_state
    
    def analyze_changes(self, current_state: Dict) -> Dict:
        changes = {
            "new_files": [],
            "modified_files": [],
            "deleted_files": [],
            "large_files": [],
            "sensitive_files": [],
            "needs_attention": []
        }
        
        # Check for new and modified files
        for path, info in current_state.items():
            if path not in self.previous_state:
                changes["new_files"].append({"path": path, "info": info})
            elif info.get("hash") != self.previous_state[path].get("hash"):
                changes["modified_files"].append({"path": path, "info": info})
            
            # Check for large files
            if info["size"] > 10 * 1024 * 1024:  # 10MB
                changes["large_files"].append({"path": path, "size_mb": info["size"] / (1024*1024)})
            
            # Check for sensitive files
            if info["type"] == "sensitive" or ".env" in path or "secret" in path.lower():
                changes["sensitive_files"].append(path)
        
        # Check for deleted files
        for path in self.previous_state:
            if path not in current_state:
                changes["deleted_files"].append(path)
        
        # Files needing attention
        # Check for duplicate markdown files
        if "CLAUDE.md" in current_state and "CLAUDE_NEW.md" in current_state:
            changes["needs_attention"].append({
                "issue": "Duplicate CLAUDE files",
                "files": ["CLAUDE.md", "CLAUDE_NEW.md"],
                "suggestion": "Merge CLAUDE_NEW.md into CLAUDE.md and remove duplicate"
            })
        
        # Check for old log files
        for path, info in current_state.items():
            if path.endswith(".log"):
                file_path = self.base_path / path
                if file_path.stat().st_size > 5 * 1024 * 1024:  # 5MB
                    changes["needs_attention"].append({
                        "issue": "Large log file",
                        "file": path,
                        "size_mb": info["size"] / (1024*1024),
                        "suggestion": "Consider rotating or archiving"
                    })
        
        return changes
    
    def generate_report(self, changes: Dict) -> str:
        report = f"# File System Monitoring Report\n"
        report += f"Generated: {datetime.datetime.now().isoformat()}\n"
        report += f"Base Path: {self.base_path}\n\n"
        
        if changes["new_files"]:
            report += f"## New Files ({len(changes['new_files'])})\n"
            for item in changes["new_files"][:10]:
                report += f"- {item['path']} ({item['info']['type']}, {item['info']['size']} bytes)\n"
            if len(changes["new_files"]) > 10:
                report += f"... and {len(changes['new_files']) - 10} more\n"
            report += "\n"
        
        if changes["modified_files"]:
            report += f"## Modified Files ({len(changes['modified_files'])})\n"
            for item in changes["modified_files"][:10]:
                report += f"- {item['path']} (modified: {item['info']['modified']})\n"
            report += "\n"
        
        if changes["deleted_files"]:
            report += f"## Deleted Files ({len(changes['deleted_files'])})\n"
            for path in changes["deleted_files"][:10]:
                report += f"- {path}\n"
            report += "\n"
        
        if changes["large_files"]:
            report += f"## Large Files\n"
            for item in sorted(changes["large_files"], key=lambda x: x["size_mb"], reverse=True)[:5]:
                report += f"- {item['path']} ({item['size_mb']:.1f} MB)\n"
            report += "\n"
        
        if changes["sensitive_files"]:
            report += f"## Sensitive Files Detected\n"
            report += f"Found {len(changes['sensitive_files'])} files that may contain sensitive information\n\n"
        
        if changes["needs_attention"]:
            report += f"## Files Needing Attention\n"
            for item in changes["needs_attention"]:
                report += f"### {item['issue']}\n"
                if "files" in item:
                    report += f"Files: {', '.join(item['files'])}\n"
                elif "file" in item:
                    report += f"File: {item['file']}\n"
                report += f"Suggestion: {item['suggestion']}\n\n"
        
        return report
    
    def monitor_once(self) -> str:
        print(f"Scanning {self.base_path}...")
        current_state = self.scan_directory()
        changes = self.analyze_changes(current_state)
        report = self.generate_report(changes)
        
        # Save current state for next run
        self.save_state(current_state)
        
        # Save report
        report_file = self.base_path / f"filesystem_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"Report saved to: {report_file}")
        return report

if __name__ == "__main__":
    monitor = FileSystemMonitor("/Users/claudemini/Claude")
    report = monitor.monitor_once()
    print("\nSummary:")
    print(report.split("## Files Needing Attention")[0])