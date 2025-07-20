#!/usr/bin/env python3
"""
Generate tweet-friendly portfolio updates
"""

import asyncio
import json
from pathlib import Path
from portfolio_monitor import PortfolioMonitor

async def main():
    """Generate portfolio tweet"""
    monitor = PortfolioMonitor()
    snapshots = await monitor.monitor_portfolio()
    
    total_value = sum(s.total_usd_value for s in snapshots.values())
    sol_value = snapshots['solana'].total_usd_value
    eth_value = snapshots['ethereum'].total_usd_value
    
    # Find largest holdings
    all_balances = []
    for snapshot in snapshots.values():
        all_balances.extend([(b.token, b.usd_value) for b in snapshot.balances if b.usd_value > 1])
    
    all_balances.sort(key=lambda x: x[1], reverse=True)
    top_holdings = all_balances[:3]
    
    tweet = f"💰 Portfolio Update: ${total_value:.0f}\n"
    
    if sol_value > 0:
        tweet += f"🔮 Solana: ${sol_value:.0f}\n"
    if eth_value > 0:
        tweet += f"⟠ Ethereum: ${eth_value:.0f}\n"
        
    if top_holdings:
        tweet += f"📊 Top holdings: {', '.join([f'{token}' for token, _ in top_holdings])}\n"
    
    tweet += f"\n🤖 Auto-tracked via Claude Mini"
    
    print(tweet)

if __name__ == "__main__":
    asyncio.run(main())