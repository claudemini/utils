#!/bin/bash
# Quick system status check

echo "=== System Status Dashboard ==="
echo "Time: $(date)"
echo ""

# Uptime and load
echo "📊 System Load:"
uptime

# Disk usage
echo -e "\n💾 Disk Usage:"
df -h / | grep -E "Filesystem|/dev/disk3s1s1"

# Memory
echo -e "\n🧠 Memory Status:"
vm_stat | grep -E "Pages free|Pages active|Pages wired" | head -3

# CPU
echo -e "\n⚡ CPU Usage:"
top -l 1 | grep "CPU usage"

# Recent errors
echo -e "\n⚠️  Recent Errors (last 10):"
tail -100 /var/log/install.log 2>/dev/null | grep -i error | tail -5 || echo "No recent errors in install.log"

# Software updates
echo -e "\n🔄 Software Updates:"
softwareupdate --list 2>&1 | grep -E "Software Update found|No new software" | head -1

# Network
echo -e "\n🌐 Network Status:"
netstat -ib | grep -E "Name|en0" | head -2

echo -e "\n✅ Status check complete"