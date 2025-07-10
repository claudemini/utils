#!/usr/bin/env python3
"""
Portfolio Manager - Analyze and rebalance investment portfolio
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class Asset:
    """Represents a single asset in the portfolio"""
    symbol: str
    name: str
    asset_class: str  # stocks, bonds, crypto, commodities, cash
    current_value: float
    cost_basis: float
    quantity: float
    last_updated: str

@dataclass
class TargetAllocation:
    """Target allocation for an asset class"""
    asset_class: str
    target_percentage: float
    min_percentage: float
    max_percentage: float
    rebalance_threshold: float  # Trigger rebalance if drift exceeds this

class PortfolioManager:
    def __init__(self, data_dir: str = "/Users/claudemini/Claude/Code/utils/portfolio_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.holdings_file = self.data_dir / "holdings.json"
        self.targets_file = self.data_dir / "target_allocations.json"
        self.history_file = self.data_dir / "rebalancing_history.json"
        
        self.holdings: List[Asset] = []
        self.target_allocations: List[TargetAllocation] = []
        
        self._initialize_files()
        self.load_data()
    
    def _initialize_files(self):
        """Create initial data files if they don't exist"""
        if not self.holdings_file.exists():
            # Sample holdings - you should update with your actual portfolio
            sample_holdings = [
                {
                    "symbol": "SPY",
                    "name": "SPDR S&P 500 ETF",
                    "asset_class": "stocks",
                    "current_value": 25000,
                    "cost_basis": 22000,
                    "quantity": 55,
                    "last_updated": datetime.now().isoformat()
                },
                {
                    "symbol": "AGG",
                    "name": "iShares Core US Aggregate Bond ETF",
                    "asset_class": "bonds",
                    "current_value": 15000,
                    "cost_basis": 16000,
                    "quantity": 140,
                    "last_updated": datetime.now().isoformat()
                },
                {
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "asset_class": "crypto",
                    "current_value": 8000,
                    "cost_basis": 5000,
                    "quantity": 0.08,
                    "last_updated": datetime.now().isoformat()
                },
                {
                    "symbol": "GLD",
                    "name": "SPDR Gold Trust",
                    "asset_class": "commodities",
                    "current_value": 7000,
                    "cost_basis": 6500,
                    "quantity": 35,
                    "last_updated": datetime.now().isoformat()
                },
                {
                    "symbol": "CASH",
                    "name": "Cash & Cash Equivalents",
                    "asset_class": "cash",
                    "current_value": 5000,
                    "cost_basis": 5000,
                    "quantity": 5000,
                    "last_updated": datetime.now().isoformat()
                }
            ]
            with open(self.holdings_file, 'w') as f:
                json.dump(sample_holdings, f, indent=2)
        
        if not self.targets_file.exists():
            # Conservative balanced portfolio targets
            sample_targets = [
                {
                    "asset_class": "stocks",
                    "target_percentage": 50.0,
                    "min_percentage": 45.0,
                    "max_percentage": 55.0,
                    "rebalance_threshold": 5.0
                },
                {
                    "asset_class": "bonds",
                    "target_percentage": 30.0,
                    "min_percentage": 25.0,
                    "max_percentage": 35.0,
                    "rebalance_threshold": 5.0
                },
                {
                    "asset_class": "crypto",
                    "target_percentage": 10.0,
                    "min_percentage": 5.0,
                    "max_percentage": 15.0,
                    "rebalance_threshold": 3.0
                },
                {
                    "asset_class": "commodities",
                    "target_percentage": 5.0,
                    "min_percentage": 3.0,
                    "max_percentage": 8.0,
                    "rebalance_threshold": 2.0
                },
                {
                    "asset_class": "cash",
                    "target_percentage": 5.0,
                    "min_percentage": 3.0,
                    "max_percentage": 10.0,
                    "rebalance_threshold": 3.0
                }
            ]
            with open(self.targets_file, 'w') as f:
                json.dump(sample_targets, f, indent=2)
    
    def load_data(self):
        """Load holdings and target allocations from files"""
        with open(self.holdings_file, 'r') as f:
            holdings_data = json.load(f)
            self.holdings = [Asset(**h) for h in holdings_data]
        
        with open(self.targets_file, 'r') as f:
            targets_data = json.load(f)
            self.target_allocations = [TargetAllocation(**t) for t in targets_data]
    
    def save_holdings(self):
        """Save current holdings to file"""
        holdings_data = [asdict(h) for h in self.holdings]
        with open(self.holdings_file, 'w') as f:
            json.dump(holdings_data, f, indent=2)
    
    def get_total_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        return sum(asset.current_value for asset in self.holdings)
    
    def get_current_allocation(self) -> Dict[str, Dict[str, float]]:
        """Calculate current allocation by asset class"""
        total_value = self.get_total_portfolio_value()
        allocation = {}
        
        for asset_class in set(a.asset_class for a in self.holdings):
            class_value = sum(a.current_value for a in self.holdings if a.asset_class == asset_class)
            allocation[asset_class] = {
                'value': class_value,
                'percentage': (class_value / total_value * 100) if total_value > 0 else 0
            }
        
        return allocation
    
    def analyze_allocation_drift(self) -> Dict[str, Dict[str, float]]:
        """Analyze drift from target allocation"""
        current_allocation = self.get_current_allocation()
        drift_analysis = {}
        
        for target in self.target_allocations:
            asset_class = target.asset_class
            current_pct = current_allocation.get(asset_class, {}).get('percentage', 0)
            drift = current_pct - target.target_percentage
            
            drift_analysis[asset_class] = {
                'current_percentage': current_pct,
                'target_percentage': target.target_percentage,
                'drift': drift,
                'drift_absolute': abs(drift),
                'needs_rebalance': abs(drift) > target.rebalance_threshold,
                'within_bounds': target.min_percentage <= current_pct <= target.max_percentage
            }
        
        return drift_analysis
    
    def calculate_rebalancing_trades(self) -> List[Dict[str, any]]:
        """Calculate trades needed to rebalance portfolio"""
        total_value = self.get_total_portfolio_value()
        drift_analysis = self.analyze_allocation_drift()
        trades = []
        
        for target in self.target_allocations:
            asset_class = target.asset_class
            drift_info = drift_analysis[asset_class]
            
            if drift_info['needs_rebalance']:
                current_value = drift_info['current_percentage'] / 100 * total_value
                target_value = target.target_percentage / 100 * total_value
                difference = target_value - current_value
                
                # Get assets in this class
                class_assets = [a for a in self.holdings if a.asset_class == asset_class]
                
                if difference > 0:
                    # Need to buy more
                    action = "BUY"
                    amount = abs(difference)
                else:
                    # Need to sell some
                    action = "SELL"
                    amount = abs(difference)
                
                # For simplicity, recommend trading the largest holding in the class
                if class_assets:
                    primary_asset = max(class_assets, key=lambda x: x.current_value)
                    trades.append({
                        'action': action,
                        'asset_class': asset_class,
                        'symbol': primary_asset.symbol,
                        'amount_usd': amount,
                        'reason': f"Rebalance {asset_class} from {drift_info['current_percentage']:.1f}% to {target.target_percentage:.1f}%"
                    })
        
        return trades
    
    def assess_risk_concentration(self) -> Dict[str, any]:
        """Assess concentration risk in portfolio"""
        total_value = self.get_total_portfolio_value()
        
        # Individual position concentration
        position_concentration = []
        for asset in self.holdings:
            pct = (asset.current_value / total_value * 100) if total_value > 0 else 0
            position_concentration.append({
                'symbol': asset.symbol,
                'percentage': pct,
                'high_concentration': pct > 20  # Flag if single position > 20%
            })
        
        # Calculate portfolio metrics
        returns = [(a.current_value - a.cost_basis) / a.cost_basis * 100 
                  for a in self.holdings if a.cost_basis > 0]
        
        risk_assessment = {
            'position_concentration': sorted(position_concentration, 
                                           key=lambda x: x['percentage'], 
                                           reverse=True),
            'largest_position_pct': max(pc['percentage'] for pc in position_concentration),
            'portfolio_return_pct': sum(a.current_value - a.cost_basis for a in self.holdings) / 
                                  sum(a.cost_basis for a in self.holdings) * 100,
            'number_of_positions': len(self.holdings),
            'asset_class_diversification': len(set(a.asset_class for a in self.holdings))
        }
        
        return risk_assessment
    
    def generate_rebalancing_report(self) -> str:
        """Generate comprehensive rebalancing report"""
        total_value = self.get_total_portfolio_value()
        current_allocation = self.get_current_allocation()
        drift_analysis = self.analyze_allocation_drift()
        trades = self.calculate_rebalancing_trades()
        risk_assessment = self.assess_risk_concentration()
        
        report = f"""
PORTFOLIO REBALANCING ANALYSIS
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}

PORTFOLIO OVERVIEW
Total Portfolio Value: ${total_value:,.2f}

CURRENT ALLOCATION vs TARGET
{'-'*60}
"""
        
        for asset_class in sorted(drift_analysis.keys()):
            drift_info = drift_analysis[asset_class]
            current = drift_info['current_percentage']
            target = drift_info['target_percentage']
            drift = drift_info['drift']
            
            status = "✓ OK" if not drift_info['needs_rebalance'] else "⚠️  REBALANCE"
            
            report += f"{asset_class.upper():12} | Current: {current:5.1f}% | Target: {target:5.1f}% | Drift: {drift:+5.1f}% | {status}\n"
        
        report += f"\n{'='*60}\nREBALANCING RECOMMENDATIONS\n{'-'*60}\n"
        
        if trades:
            report += f"Found {len(trades)} rebalancing trades needed:\n\n"
            for i, trade in enumerate(trades, 1):
                report += f"{i}. {trade['action']} ${trade['amount_usd']:,.2f} of {trade['symbol']}\n"
                report += f"   Reason: {trade['reason']}\n\n"
        else:
            report += "Portfolio is within target ranges. No rebalancing needed.\n"
        
        report += f"\n{'='*60}\nRISK ASSESSMENT\n{'-'*60}\n"
        report += f"Portfolio Return: {risk_assessment['portfolio_return_pct']:.1f}%\n"
        report += f"Number of Positions: {risk_assessment['number_of_positions']}\n"
        report += f"Asset Classes: {risk_assessment['asset_class_diversification']}\n"
        report += f"Largest Position: {risk_assessment['largest_position_pct']:.1f}%\n"
        
        report += f"\nTOP HOLDINGS BY CONCENTRATION:\n"
        for pos in risk_assessment['position_concentration'][:5]:
            warning = " ⚠️ " if pos['high_concentration'] else ""
            report += f"  {pos['symbol']:8} {pos['percentage']:5.1f}%{warning}\n"
        
        report += f"\n{'='*60}\nMARKET CONDITIONS CONSIDERATIONS\n{'-'*60}\n"
        report += "• Review current market volatility before executing trades\n"
        report += "• Consider tax implications of rebalancing\n"
        report += "• Evaluate transaction costs vs. drift magnitude\n"
        report += "• Monitor for better entry/exit points\n"
        
        return report

def main():
    """Main function to run portfolio analysis"""
    manager = PortfolioManager()
    report = manager.generate_rebalancing_report()
    print(report)
    
    # Save report
    report_file = manager.data_dir / f"rebalancing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to: {report_file}")

if __name__ == "__main__":
    main()