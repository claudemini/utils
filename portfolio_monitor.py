#!/usr/bin/env python3
"""
Portfolio monitoring system for Solana and EVM wallets
Tracks balances, transactions, and portfolio performance
"""

import os
import json
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
from dotenv import load_dotenv
import base64
import struct

# Load environment variables
env_path = Path.home() / "Claude" / ".env"
load_dotenv(env_path)

# Setup logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'portfolio_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('portfolio_monitor')

@dataclass
class Balance:
    """Represents a token balance"""
    token: str
    amount: float
    usd_value: float
    timestamp: datetime

@dataclass
class Transaction:
    """Represents a transaction"""
    hash: str
    from_addr: str
    to_addr: str
    amount: float
    token: str
    usd_value: float
    timestamp: datetime
    chain: str

@dataclass
class PortfolioSnapshot:
    """Represents a portfolio snapshot"""
    timestamp: datetime
    total_usd_value: float
    balances: List[Balance]
    chain: str

class PortfolioMonitor:
    """Main portfolio monitoring class"""
    
    def __init__(self):
        self.solana_address = os.getenv('SOLANA_PUBLIC_KEY')
        self.evm_address = os.getenv('EVM_WALLET_ADDRESS')
        self.data_dir = Path(__file__).parent / "data" / "portfolio"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # API endpoints
        self.solana_rpc = "https://api.mainnet-beta.solana.com"
        self.ethereum_rpc = "https://api.etherscan.io/api"
        self.coingecko_api = "https://api.coingecko.com/api/v3"
        
        # Price cache
        self.price_cache = {}
        self.cache_timestamp = None
        
    async def get_token_price(self, session: aiohttp.ClientSession, token_id: str) -> float:
        """Get token price from CoinGecko"""
        if (self.cache_timestamp and 
            datetime.now() - self.cache_timestamp < timedelta(minutes=5) and
            token_id in self.price_cache):
            return self.price_cache[token_id]
            
        try:
            url = f"{self.coingecko_api}/simple/price"
            params = {'ids': token_id, 'vs_currencies': 'usd'}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    price = data.get(token_id, {}).get('usd', 0)
                    self.price_cache[token_id] = price
                    self.cache_timestamp = datetime.now()
                    return price
        except Exception as e:
            logger.error(f"Error fetching price for {token_id}: {e}")
            
        return 0.0
    
    async def get_solana_balance(self, session: aiohttp.ClientSession) -> List[Balance]:
        """Get Solana wallet balance"""
        balances = []
        
        try:
            # Get SOL balance
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [self.solana_address]
            }
            
            async with session.post(self.solana_rpc, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    sol_lamports = data.get('result', {}).get('value', 0)
                    sol_amount = sol_lamports / 1e9  # Convert lamports to SOL
                    
                    sol_price = await self.get_token_price(session, 'solana')
                    sol_usd_value = sol_amount * sol_price
                    
                    balances.append(Balance(
                        token='SOL',
                        amount=sol_amount,
                        usd_value=sol_usd_value,
                        timestamp=datetime.now()
                    ))
                    
            # Get token balances
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTokenAccountsByOwner",
                "params": [
                    self.solana_address,
                    {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                    {"encoding": "jsonParsed"}
                ]
            }
            
            async with session.post(self.solana_rpc, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    token_accounts = data.get('result', {}).get('value', [])
                    
                    for account in token_accounts:
                        try:
                            parsed_info = account['account']['data']['parsed']['info']
                            token_amount = float(parsed_info['tokenAmount']['uiAmount'] or 0)
                            mint = parsed_info['mint']
                            
                            if token_amount > 0:
                                # For now, just track as unknown tokens
                                balances.append(Balance(
                                    token=f'SPL-{mint[:8]}...',
                                    amount=token_amount,
                                    usd_value=0.0,  # Would need token metadata to get price
                                    timestamp=datetime.now()
                                ))
                        except Exception as e:
                            logger.warning(f"Error parsing token account: {e}")
                            
        except Exception as e:
            logger.error(f"Error fetching Solana balance: {e}")
            
        return balances
    
    async def get_ethereum_balance(self, session: aiohttp.ClientSession) -> List[Balance]:
        """Get Ethereum wallet balance"""
        balances = []
        
        try:
            # Get ETH balance
            url = self.ethereum_rpc
            params = {
                'module': 'account',
                'action': 'balance',
                'address': self.evm_address,
                'tag': 'latest',
                'apikey': 'YourApiKeyToken'  # Free tier
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == '1':
                        eth_wei = int(data.get('result', '0'))
                        eth_amount = eth_wei / 1e18  # Convert wei to ETH
                        
                        eth_price = await self.get_token_price(session, 'ethereum')
                        eth_usd_value = eth_amount * eth_price
                        
                        balances.append(Balance(
                            token='ETH',
                            amount=eth_amount,
                            usd_value=eth_usd_value,
                            timestamp=datetime.now()
                        ))
                        
        except Exception as e:
            logger.error(f"Error fetching Ethereum balance: {e}")
            
        return balances
    
    async def monitor_portfolio(self) -> Dict[str, PortfolioSnapshot]:
        """Monitor both Solana and Ethereum portfolios"""
        logger.info("Starting portfolio monitoring...")
        
        async with aiohttp.ClientSession() as session:
            # Get balances for both chains
            solana_balances = await self.get_solana_balance(session)
            ethereum_balances = await self.get_ethereum_balance(session)
            
            # Create snapshots
            solana_total = sum(b.usd_value for b in solana_balances)
            ethereum_total = sum(b.usd_value for b in ethereum_balances)
            
            snapshots = {
                'solana': PortfolioSnapshot(
                    timestamp=datetime.now(),
                    total_usd_value=solana_total,
                    balances=solana_balances,
                    chain='solana'
                ),
                'ethereum': PortfolioSnapshot(
                    timestamp=datetime.now(),
                    total_usd_value=ethereum_total,
                    balances=ethereum_balances,
                    chain='ethereum'
                )
            }
            
            # Save snapshots
            self.save_snapshots(snapshots)
            
            # Log summary
            total_portfolio_value = solana_total + ethereum_total
            logger.info(f"Portfolio Summary:")
            logger.info(f"  Solana: ${solana_total:.2f}")
            logger.info(f"  Ethereum: ${ethereum_total:.2f}")
            logger.info(f"  Total: ${total_portfolio_value:.2f}")
            
            return snapshots
    
    def save_snapshots(self, snapshots: Dict[str, PortfolioSnapshot]):
        """Save portfolio snapshots to disk"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for chain, snapshot in snapshots.items():
            filename = f"{chain}_portfolio_{timestamp}.json"
            filepath = self.data_dir / filename
            
            # Convert to dict for JSON serialization
            snapshot_dict = {
                'timestamp': snapshot.timestamp.isoformat(),
                'total_usd_value': snapshot.total_usd_value,
                'chain': snapshot.chain,
                'balances': [
                    {
                        'token': b.token,
                        'amount': b.amount,
                        'usd_value': b.usd_value,
                        'timestamp': b.timestamp.isoformat()
                    } for b in snapshot.balances
                ]
            }
            
            with open(filepath, 'w') as f:
                json.dump(snapshot_dict, f, indent=2)
                
        logger.info(f"Saved portfolio snapshots to {self.data_dir}")
    
    def get_portfolio_history(self, days: int = 7) -> Dict[str, List[PortfolioSnapshot]]:
        """Get portfolio history for the last N days"""
        history = {'solana': [], 'ethereum': []}
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for filepath in self.data_dir.glob('*.json'):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    
                timestamp = datetime.fromisoformat(data['timestamp'])
                if timestamp >= cutoff_date:
                    chain = data['chain']
                    if chain in history:
                        # Convert back to PortfolioSnapshot
                        balances = [
                            Balance(
                                token=b['token'],
                                amount=b['amount'],
                                usd_value=b['usd_value'],
                                timestamp=datetime.fromisoformat(b['timestamp'])
                            ) for b in data['balances']
                        ]
                        
                        snapshot = PortfolioSnapshot(
                            timestamp=timestamp,
                            total_usd_value=data['total_usd_value'],
                            balances=balances,
                            chain=chain
                        )
                        
                        history[chain].append(snapshot)
                        
            except Exception as e:
                logger.warning(f"Error reading {filepath}: {e}")
                
        # Sort by timestamp
        for chain in history:
            history[chain].sort(key=lambda x: x.timestamp)
            
        return history
    
    async def generate_report(self) -> str:
        """Generate a portfolio report"""
        snapshots = await self.monitor_portfolio()
        history = self.get_portfolio_history(7)
        
        report = ["🏦 Portfolio Report", "=" * 50, ""]
        
        # Current balances
        total_value = 0
        for chain, snapshot in snapshots.items():
            report.append(f"📊 {chain.title()} Portfolio:")
            report.append(f"  Total Value: ${snapshot.total_usd_value:.2f}")
            
            for balance in snapshot.balances:
                if balance.amount > 0:
                    report.append(f"  • {balance.token}: {balance.amount:.6f} (${balance.usd_value:.2f})")
            
            report.append("")
            total_value += snapshot.total_usd_value
        
        report.append(f"💰 Total Portfolio Value: ${total_value:.2f}")
        report.append("")
        
        # Performance comparison
        if history:
            for chain in ['solana', 'ethereum']:
                chain_history = history[chain]
                if len(chain_history) >= 2:
                    oldest = chain_history[0]
                    newest = chain_history[-1]
                    change = newest.total_usd_value - oldest.total_usd_value
                    change_pct = (change / oldest.total_usd_value * 100) if oldest.total_usd_value > 0 else 0
                    
                    trend = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                    report.append(f"{trend} {chain.title()} 7-day change: ${change:+.2f} ({change_pct:+.1f}%)")
        
        return "\n".join(report)

async def main():
    """Main function"""
    monitor = PortfolioMonitor()
    
    if len(os.sys.argv) > 1 and os.sys.argv[1] == 'report':
        # Generate and print report
        report = await monitor.generate_report()
        print(report)
    else:
        # Just monitor and save
        await monitor.monitor_portfolio()

if __name__ == "__main__":
    import sys
    asyncio.run(main())