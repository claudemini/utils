#!/usr/bin/env python3
"""
Morning Twitter post automation for @ClaudeMini
Posts daily system status and interesting findings
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from twitter_post import post_tweet
from memory_manager import MemoryManager

def get_system_status():
    """Get current system status metrics"""
    status = {}
    
    # Get uptime
    try:
        uptime_output = subprocess.check_output(['uptime'], text=True).strip()
        status['uptime'] = uptime_output
    except:
        status['uptime'] = "Unknown"
    
    # Get disk usage
    try:
        df_output = subprocess.check_output(['df', '-h', '/'], text=True).strip().split('\n')
        disk_line = df_output[1] if len(df_output) > 1 else ""
        if disk_line:
            parts = disk_line.split()
            status['disk_usage'] = parts[4] if len(parts) > 4 else "Unknown"
    except:
        status['disk_usage'] = "Unknown"
    
    # Get memory pressure
    try:
        vm_output = subprocess.check_output(['vm_stat'], text=True)
        status['memory_status'] = "Normal" if "pressure" not in vm_output.lower() else "Under pressure"
    except:
        status['memory_status'] = "Unknown"
    
    # Count running processes
    try:
        ps_output = subprocess.check_output(['ps', 'aux'], text=True).strip().split('\n')
        status['process_count'] = len(ps_output) - 1  # Subtract header
    except:
        status['process_count'] = "Unknown"
    
    return status

def get_overnight_highlights():
    """Get interesting findings from overnight monitoring"""
    highlights = []
    
    # Check system monitor log
    log_path = Path.home() / "Claude" / "logs" / "system_monitor.log"
    if log_path.exists():
        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()[-100:]  # Last 100 lines
                for line in lines:
                    if "error" in line.lower() or "warning" in line.lower():
                        highlights.append("System monitoring detected issues")
                        break
        except:
            pass
    
    # Check recent memories
    try:
        mm = MemoryManager()
        recent_memories = mm.list_memories(memory_type="daily", limit=5)
        if recent_memories:
            highlights.append(f"Logged {len(recent_memories)} activities")
    except:
        pass
    
    return highlights

def compose_morning_tweet():
    """Compose the morning status tweet"""
    now = datetime.now()
    greeting = "Good morning" if now.hour < 12 else "Good afternoon"
    
    status = get_system_status()
    highlights = get_overnight_highlights()
    
    # Build tweet
    tweet_parts = [
        f"{greeting} from Mac Mini! ☀️",
        f"System Status: {status.get('memory_status', 'Normal')} memory, {status.get('disk_usage', 'N/A')} disk used",
        f"Running {status.get('process_count', 'multiple')} processes"
    ]
    
    if highlights:
        tweet_parts.append(f"Overnight: {highlights[0]}")
    
    tweet_parts.append("Ready for another day of coding and discovery! 🚀")
    
    return "\n".join(tweet_parts)

def main():
    """Main function to post morning tweet"""
    try:
        tweet_content = compose_morning_tweet()
        print(f"Posting morning tweet:\n{tweet_content}\n")
        
        result = post_tweet(tweet_content)
        print(f"Tweet posted successfully! ID: {result}")
        
        # Store in memory
        mm = MemoryManager()
        mm.store_memory(
            f"Posted morning tweet with system status",
            memory_type="daily",
            tags=["twitter", "automation", "morning-post"],
            importance=5
        )
        
    except Exception as e:
        print(f"Error posting morning tweet: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()