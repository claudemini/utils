#!/usr/bin/env python3
"""
Virtual Environment Optimizer - Reduces venv size by removing unnecessary files
"""

import os
import shutil
from pathlib import Path
import subprocess

def optimize_venv(venv_path: Path):
    """Optimize a virtual environment"""
    if not venv_path.exists():
        print(f"Virtual environment not found: {venv_path}")
        return
        
    initial_size = get_dir_size(venv_path)
    print(f"Initial venv size: {initial_size / (1024**2):.1f}MB")
    
    # Remove cache files
    cache_patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/pip-wheel-metadata",
        "**/pip-selfcheck.json",
        "**/.pytest_cache",
        "**/.mypy_cache",
        "**/dist-info/RECORD",
        "**/dist-info/WHEEL",
        "**/dist-info/METADATA"
    ]
    
    removed_count = 0
    for pattern in cache_patterns:
        for file_path in venv_path.rglob(pattern):
            try:
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                removed_count += 1
            except:
                pass
                
    # Remove test directories
    test_dirs = [
        "**/tests",
        "**/test",
        "**/testing",
        "**/examples",
        "**/docs",
        "**/documentation"
    ]
    
    for pattern in test_dirs:
        for dir_path in venv_path.rglob(pattern):
            if dir_path.is_dir() and "site-packages" in str(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    removed_count += 1
                except:
                    pass
                    
    # Remove duplicate packages
    site_packages = venv_path / "lib" / "python3.12" / "site-packages"
    if site_packages.exists():
        # Find and remove old versions of packages
        packages = {}
        for item in site_packages.iterdir():
            if item.is_dir() and "-" in item.name:
                pkg_name = item.name.split("-")[0]
                if pkg_name not in packages:
                    packages[pkg_name] = []
                packages[pkg_name].append(item)
                
        for pkg_name, versions in packages.items():
            if len(versions) > 1:
                # Keep the newest version
                versions.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                for old_version in versions[1:]:
                    try:
                        shutil.rmtree(old_version)
                        removed_count += 1
                        print(f"Removed old version: {old_version.name}")
                    except:
                        pass
                        
    # Compress remaining .py files
    print(f"\nRemoved {removed_count} files/directories")
    
    final_size = get_dir_size(venv_path)
    saved = initial_size - final_size
    print(f"Final venv size: {final_size / (1024**2):.1f}MB")
    print(f"Space saved: {saved / (1024**2):.1f}MB ({saved / initial_size * 100:.1f}%)")
    
    return {
        "initial_size_mb": initial_size / (1024**2),
        "final_size_mb": final_size / (1024**2),
        "saved_mb": saved / (1024**2),
        "removed_items": removed_count
    }

def get_dir_size(path: Path) -> int:
    """Get total size of directory"""
    total = 0
    for entry in path.rglob("*"):
        if entry.is_file():
            total += entry.stat().st_size
    return total

def create_requirements_file(venv_path: Path):
    """Create requirements.txt from current venv"""
    pip_path = venv_path / "bin" / "pip"
    if pip_path.exists():
        req_file = venv_path.parent / "requirements.txt"
        result = subprocess.run(
            [str(pip_path), "freeze"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            with open(req_file, 'w') as f:
                f.write(result.stdout)
            print(f"Created requirements.txt at {req_file}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        venv_path = Path(sys.argv[1])
    else:
        # Default to utils venv
        venv_path = Path("/Users/claudemini/Claude/Code/utils/.venv")
        
    if venv_path.exists():
        # First create requirements.txt
        create_requirements_file(venv_path)
        
        # Then optimize
        optimize_venv(venv_path)
    else:
        print(f"Virtual environment not found: {venv_path}")