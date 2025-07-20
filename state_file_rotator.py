#!/usr/bin/env python3
"""
State File Rotator - Manages and rotates large JSON state files
Prevents state files from growing too large and impacting performance
"""

import json
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import logging
import subprocess

class StateFileRotator:
    def __init__(self, max_size_mb: float = 5.0, archive_days: int = 7):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.archive_days = archive_days
        self.archive_dir = Path("/Users/claudemini/Claude/archives")
        self.archive_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('StateFileRotator')
        
        # State files to monitor
        self.monitored_files = [
            Path("/Users/claudemini/Claude/.fs_activity_state.json"),
            Path("/Users/claudemini/Claude/logs/.task_error_state.json"),
            Path("/Users/claudemini/Claude/Code/utils/.trading_state.json"),
            Path("/Users/claudemini/Claude/.memory_index_state.json")
        ]
    
    def check_file_size(self, file_path: Path) -> bool:
        """Check if file exceeds size limit"""
        if not file_path.exists():
            return False
        return file_path.stat().st_size > self.max_size_bytes
    
    def rotate_file(self, file_path: Path):
        """Rotate a single state file"""
        if not file_path.exists():
            return
        
        self.logger.info(f"Rotating {file_path.name} (size: {file_path.stat().st_size / 1024 / 1024:.2f}MB)")
        
        try:
            # Create archive filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"{file_path.stem}_{timestamp}{file_path.suffix}.gz"
            archive_path = self.archive_dir / archive_name
            
            # Read current state
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Determine what to keep in active file
            if isinstance(data, dict):
                # For dict-based state files, keep recent entries
                new_data = self._filter_recent_entries(data)
            elif isinstance(data, list):
                # For list-based state files, keep last N entries
                new_data = data[-1000:] if len(data) > 1000 else data
            else:
                new_data = data
            
            # Archive old data
            with gzip.open(archive_path, 'wt', encoding='utf-8') as gz:
                json.dump(data, gz, indent=2)
            
            # Write filtered data back
            with open(file_path, 'w') as f:
                json.dump(new_data, f, indent=2)
            
            self.logger.info(f"Archived to {archive_path}, reduced size from "
                           f"{len(json.dumps(data))} to {len(json.dumps(new_data))} bytes")
            
            # Store rotation event in memory
            memory_cmd = f'/Users/claudemini/Claude/Code/utils/memory.sh store "Rotated large state file {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.2f}MB)" --type daily --tags "maintenance automation" --importance 3'
            subprocess.run(memory_cmd, shell=True)
            
        except Exception as e:
            self.logger.error(f"Error rotating {file_path}: {e}")
    
    def _filter_recent_entries(self, data: dict) -> dict:
        """Filter dictionary to keep only recent entries"""
        filtered = {}
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for key, value in data.items():
            # Try to detect timestamp fields
            if isinstance(value, dict):
                # Check for timestamp fields
                timestamp = None
                for ts_field in ['timestamp', 'created_at', 'updated_at', 'last_seen']:
                    if ts_field in value:
                        try:
                            timestamp = datetime.fromisoformat(value[ts_field].replace('Z', '+00:00'))
                            break
                        except:
                            continue
                
                # Keep if recent or no timestamp found
                if timestamp is None or timestamp > cutoff_date:
                    filtered[key] = value
            else:
                # Keep non-dict values
                filtered[key] = value
        
        return filtered
    
    def clean_old_archives(self):
        """Remove archives older than archive_days"""
        cutoff_date = datetime.now() - timedelta(days=self.archive_days)
        
        for archive in self.archive_dir.glob("*.gz"):
            if archive.stat().st_mtime < cutoff_date.timestamp():
                self.logger.info(f"Removing old archive: {archive.name}")
                archive.unlink()
    
    def rotate_all(self):
        """Check and rotate all monitored files"""
        rotated_count = 0
        
        for file_path in self.monitored_files:
            if self.check_file_size(file_path):
                self.rotate_file(file_path)
                rotated_count += 1
        
        # Also check for any other large JSON files
        for json_file in Path("/Users/claudemini/Claude").rglob("*.json"):
            if json_file not in self.monitored_files and self.check_file_size(json_file):
                # Skip virtual environment and node_modules
                if ".venv" in str(json_file) or "node_modules" in str(json_file):
                    continue
                    
                self.logger.info(f"Found large unmonitored file: {json_file}")
                self.rotate_file(json_file)
                rotated_count += 1
        
        # Clean old archives
        self.clean_old_archives()
        
        return rotated_count
    
    def get_state_report(self):
        """Generate report of state file sizes"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "files": [],
            "total_size_mb": 0
        }
        
        for file_path in self.monitored_files:
            if file_path.exists():
                size_mb = file_path.stat().st_size / 1024 / 1024
                report["files"].append({
                    "path": str(file_path),
                    "size_mb": round(size_mb, 2),
                    "needs_rotation": size_mb > (self.max_size_bytes / 1024 / 1024)
                })
                report["total_size_mb"] += size_mb
        
        report["total_size_mb"] = round(report["total_size_mb"], 2)
        return report


# CLI interface
if __name__ == "__main__":
    import sys
    
    rotator = StateFileRotator()
    
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        # Show state file report
        report = rotator.get_state_report()
        print(json.dumps(report, indent=2))
    else:
        # Perform rotation
        print("Checking state files for rotation...")
        count = rotator.rotate_all()
        print(f"Rotated {count} files")
        
        # Show current state
        report = rotator.get_state_report()
        print("\nCurrent state file sizes:")
        for file_info in report["files"]:
            status = "⚠️  NEEDS ROTATION" if file_info["needs_rotation"] else "✓"
            print(f"  {Path(file_info['path']).name}: {file_info['size_mb']}MB {status}")