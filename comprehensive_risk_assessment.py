#!/usr/bin/env python3
"""
Comprehensive Risk Assessment Tool
Analyzes portfolio risk across multiple dimensions
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import math

class RiskAssessment:
    def __init__(self, portfolio_data_dir: str = "/Users/claudemini/Claude/Code/utils/portfolio_data"):
        self.data_dir = Path(portfolio_data_dir)
        self.holdings_file = self.data_dir / "holdings.json"
        self.targets_file = self.data_dir / "target_allocations.json"
        
        with open(self.holdings_file, 'r') as f:
            self.holdings = json.load(f)
        
        with open(self.targets_file, 'r') as f:
            self.targets = json.load(f)
    
    def calculate_portfolio_metrics(self) -> Dict:
        """Calculate basic portfolio metrics"""
        total_value = sum(h['current_value'] for h in self.holdings)
        total_cost = sum(h['cost_basis'] for h in self.holdings)
        
        # Calculate returns by asset
        asset_returns = []
        for h in self.holdings:
            if h['cost_basis'] > 0:
                ret = (h['current_value'] - h['cost_basis']) / h['cost_basis'] * 100
                asset_returns.append({
                    'symbol': h['symbol'],
                    'return_pct': ret,
                    'gain_loss': h['current_value'] - h['cost_basis']
                })
        
        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_return_pct': (total_value - total_cost) / total_cost * 100,
            'total_gain_loss': total_value - total_cost,
            'asset_returns': sorted(asset_returns, key=lambda x: x['return_pct'], reverse=True)
        }
    
    def assess_concentration_risk(self) -> Dict:
        """Assess concentration risk in portfolio"""
        total_value = sum(h['current_value'] for h in self.holdings)
        
        # Position concentration
        positions = []
        for h in self.holdings:
            pct = h['current_value'] / total_value * 100
            positions.append({
                'symbol': h['symbol'],
                'asset_class': h['asset_class'],
                'value': h['current_value'],
                'percentage': pct,
                'risk_level': 'HIGH' if pct > 25 else 'MEDIUM' if pct > 15 else 'LOW'
            })
        
        # Asset class concentration
        asset_classes = {}
        for h in self.holdings:
            cls = h['asset_class']
            if cls not in asset_classes:
                asset_classes[cls] = 0
            asset_classes[cls] += h['current_value']
        
        class_concentration = []
        for cls, value in asset_classes.items():
            pct = value / total_value * 100
            class_concentration.append({
                'asset_class': cls,
                'value': value,
                'percentage': pct
            })
        
        # Calculate Herfindahl-Hirschman Index (HHI) for concentration
        hhi = sum((h['current_value'] / total_value * 100) ** 2 for h in self.holdings)
        
        return {
            'positions': sorted(positions, key=lambda x: x['percentage'], reverse=True),
            'asset_classes': sorted(class_concentration, key=lambda x: x['percentage'], reverse=True),
            'hhi_index': hhi,
            'hhi_interpretation': 'HIGH CONCENTRATION' if hhi > 2500 else 'MODERATE' if hhi > 1500 else 'WELL DIVERSIFIED',
            'largest_position_pct': max(p['percentage'] for p in positions),
            'top_two_positions_pct': sum(sorted([p['percentage'] for p in positions], reverse=True)[:2])
        }
    
    def assess_volatility_risk(self) -> Dict:
        """Assess volatility risk based on asset class composition"""
        # Typical volatility assumptions (annual)
        volatility_map = {
            'stocks': 20,
            'bonds': 5,
            'crypto': 80,
            'commodities': 25,
            'cash': 0
        }
        
        total_value = sum(h['current_value'] for h in self.holdings)
        
        # Calculate weighted portfolio volatility
        weighted_vol = 0
        vol_contributions = []
        
        for h in self.holdings:
            weight = h['current_value'] / total_value
            vol = volatility_map.get(h['asset_class'], 20)
            contribution = weight * vol
            weighted_vol += contribution
            
            vol_contributions.append({
                'symbol': h['symbol'],
                'asset_class': h['asset_class'],
                'weight_pct': weight * 100,
                'volatility': vol,
                'vol_contribution': contribution
            })
        
        # Risk categories based on volatility
        if weighted_vol < 10:
            risk_category = 'CONSERVATIVE'
        elif weighted_vol < 20:
            risk_category = 'MODERATE'
        elif weighted_vol < 30:
            risk_category = 'AGGRESSIVE'
        else:
            risk_category = 'VERY AGGRESSIVE'
        
        return {
            'portfolio_volatility': weighted_vol,
            'risk_category': risk_category,
            'volatility_contributions': sorted(vol_contributions, key=lambda x: x['vol_contribution'], reverse=True),
            'highest_vol_asset': max(vol_contributions, key=lambda x: x['volatility'])
        }
    
    def assess_liquidity_risk(self) -> Dict:
        """Assess liquidity risk of portfolio"""
        liquidity_scores = {
            'stocks': 10,  # Highly liquid
            'bonds': 8,    # Liquid
            'crypto': 7,   # Moderately liquid (24/7 but can have slippage)
            'commodities': 6,  # Less liquid than stocks
            'cash': 10     # Perfect liquidity
        }
        
        total_value = sum(h['current_value'] for h in self.holdings)
        
        liquidity_analysis = []
        weighted_liquidity = 0
        
        for h in self.holdings:
            weight = h['current_value'] / total_value
            liquidity = liquidity_scores.get(h['asset_class'], 5)
            weighted_liquidity += weight * liquidity
            
            liquidity_analysis.append({
                'symbol': h['symbol'],
                'asset_class': h['asset_class'],
                'value': h['current_value'],
                'liquidity_score': liquidity,
                'liquidity_category': 'HIGH' if liquidity >= 8 else 'MEDIUM' if liquidity >= 6 else 'LOW'
            })
        
        # Calculate how much can be liquidated quickly (score >= 8)
        high_liquidity_value = sum(h['current_value'] for h in self.holdings 
                                  if liquidity_scores.get(h['asset_class'], 5) >= 8)
        high_liquidity_pct = high_liquidity_value / total_value * 100
        
        return {
            'weighted_liquidity_score': weighted_liquidity,
            'high_liquidity_percentage': high_liquidity_pct,
            'high_liquidity_value': high_liquidity_value,
            'liquidity_breakdown': sorted(liquidity_analysis, key=lambda x: x['liquidity_score'], reverse=True),
            'overall_liquidity': 'HIGH' if weighted_liquidity >= 8 else 'MEDIUM' if weighted_liquidity >= 6 else 'LOW'
        }
    
    def assess_currency_risk(self) -> Dict:
        """Assess currency exposure risk"""
        # Simplified currency exposure assumptions
        currency_exposure = {
            'SPY': {'USD': 100},
            'AGG': {'USD': 100},
            'BTC': {'CRYPTO': 100},  # Not tied to any fiat
            'GLD': {'COMMODITY': 100},  # Physical commodity
            'CASH': {'USD': 100}
        }
        
        total_value = sum(h['current_value'] for h in self.holdings)
        
        # Calculate currency exposures
        exposures = {}
        for h in self.holdings:
            symbol_exposure = currency_exposure.get(h['symbol'], {'USD': 100})
            for currency, pct in symbol_exposure.items():
                if currency not in exposures:
                    exposures[currency] = 0
                exposures[currency] += h['current_value'] * pct / 100
        
        exposure_analysis = []
        for currency, value in exposures.items():
            exposure_analysis.append({
                'currency': currency,
                'exposure_value': value,
                'exposure_pct': value / total_value * 100
            })
        
        return {
            'currency_exposures': sorted(exposure_analysis, key=lambda x: x['exposure_pct'], reverse=True),
            'usd_exposure_pct': exposures.get('USD', 0) / total_value * 100,
            'non_fiat_exposure_pct': (exposures.get('CRYPTO', 0) + exposures.get('COMMODITY', 0)) / total_value * 100
        }
    
    def calculate_risk_score(self) -> Dict:
        """Calculate overall risk score"""
        metrics = self.calculate_portfolio_metrics()
        concentration = self.assess_concentration_risk()
        volatility = self.assess_volatility_risk()
        liquidity = self.assess_liquidity_risk()
        
        # Risk scoring (0-100, higher = riskier)
        risk_scores = {
            'concentration': min(concentration['hhi_index'] / 50, 100),  # HHI > 5000 = max risk
            'volatility': min(volatility['portfolio_volatility'] * 2.5, 100),  # Vol > 40% = max risk
            'liquidity': max(0, 100 - liquidity['weighted_liquidity_score'] * 10),  # Lower liquidity = higher risk
            'leverage': 0,  # No leverage detected
            'single_position': min(concentration['largest_position_pct'] * 2, 100)  # >50% = max risk
        }
        
        # Weighted average risk score
        weights = {
            'concentration': 0.25,
            'volatility': 0.30,
            'liquidity': 0.20,
            'leverage': 0.15,
            'single_position': 0.10
        }
        
        overall_risk_score = sum(risk_scores[k] * weights[k] for k in risk_scores)
        
        if overall_risk_score < 30:
            risk_level = 'LOW'
        elif overall_risk_score < 50:
            risk_level = 'MODERATE'
        elif overall_risk_score < 70:
            risk_level = 'HIGH'
        else:
            risk_level = 'VERY HIGH'
        
        return {
            'risk_scores': risk_scores,
            'overall_risk_score': overall_risk_score,
            'risk_level': risk_level
        }
    
    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive risk assessment report"""
        metrics = self.calculate_portfolio_metrics()
        concentration = self.assess_concentration_risk()
        volatility = self.assess_volatility_risk()
        liquidity = self.assess_liquidity_risk()
        currency = self.assess_currency_risk()
        risk_score = self.calculate_risk_score()
        
        report = f"""
COMPREHENSIVE RISK ASSESSMENT REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

EXECUTIVE SUMMARY
{'-'*80}
Portfolio Value: ${metrics['total_value']:,.2f}
Total Return: {metrics['total_return_pct']:.1f}% (${metrics['total_gain_loss']:,.2f})
Overall Risk Score: {risk_score['overall_risk_score']:.1f}/100 ({risk_score['risk_level']})
Risk Category: {volatility['risk_category']}

KEY RISK INDICATORS:
• Concentration Risk: {concentration['hhi_interpretation']} (HHI: {concentration['hhi_index']:.0f})
• Largest Position: {concentration['largest_position_pct']:.1f}% 
• Portfolio Volatility: {volatility['portfolio_volatility']:.1f}%
• Liquidity Score: {liquidity['overall_liquidity']} ({liquidity['weighted_liquidity_score']:.1f}/10)
• USD Exposure: {currency['usd_exposure_pct']:.1f}%

{'='*80}
1. CONCENTRATION RISK ANALYSIS
{'-'*80}
"""
        
        report += f"Herfindahl-Hirschman Index: {concentration['hhi_index']:.0f} ({concentration['hhi_interpretation']})\n"
        report += f"Top 2 Positions: {concentration['top_two_positions_pct']:.1f}% of portfolio\n\n"
        
        report += "Position Concentration:\n"
        for pos in concentration['positions']:
            report += f"  {pos['symbol']:8} {pos['percentage']:5.1f}% ({pos['risk_level']} concentration risk)\n"
        
        report += "\nAsset Class Distribution:\n"
        for ac in concentration['asset_classes']:
            report += f"  {ac['asset_class']:12} {ac['percentage']:5.1f}%\n"
        
        report += f"""
{'='*80}
2. VOLATILITY RISK ANALYSIS
{'-'*80}
Portfolio Volatility: {volatility['portfolio_volatility']:.1f}% (annualized)
Risk Category: {volatility['risk_category']}

Volatility Contributors:
"""
        for vc in volatility['volatility_contributions'][:5]:
            report += f"  {vc['symbol']:8} contributes {vc['vol_contribution']:4.1f}% to portfolio volatility\n"
        
        report += f"""
{'='*80}
3. LIQUIDITY RISK ANALYSIS
{'-'*80}
Overall Liquidity: {liquidity['overall_liquidity']}
High Liquidity Assets: {liquidity['high_liquidity_percentage']:.1f}% (${liquidity['high_liquidity_value']:,.2f})

Liquidity Breakdown:
"""
        for la in liquidity['liquidity_breakdown']:
            report += f"  {la['symbol']:8} {la['liquidity_category']:6} (score: {la['liquidity_score']}/10)\n"
        
        report += f"""
{'='*80}
4. CURRENCY & MARKET RISK
{'-'*80}
Currency Exposures:
"""
        for ce in currency['currency_exposures']:
            report += f"  {ce['currency']:10} {ce['exposure_pct']:5.1f}% (${ce['exposure_value']:,.2f})\n"
        
        report += f"\nNon-Fiat Exposure: {currency['non_fiat_exposure_pct']:.1f}%\n"
        
        report += f"""
{'='*80}
5. INDIVIDUAL ASSET PERFORMANCE
{'-'*80}
"""
        for ar in metrics['asset_returns']:
            report += f"  {ar['symbol']:8} {ar['return_pct']:+6.1f}% (${ar['gain_loss']:+,.2f})\n"
        
        report += f"""
{'='*80}
6. RISK MITIGATION RECOMMENDATIONS
{'-'*80}
"""
        
        # Generate recommendations based on risk assessment
        recommendations = []
        
        if concentration['largest_position_pct'] > 30:
            recommendations.append("• URGENT: Reduce concentration in largest position to below 25%")
        
        if volatility['portfolio_volatility'] > 25:
            recommendations.append("• Consider reducing exposure to high-volatility assets (crypto, commodities)")
        
        if liquidity['high_liquidity_percentage'] < 50:
            recommendations.append("• Increase allocation to highly liquid assets for emergency needs")
        
        if concentration['hhi_index'] > 2500:
            recommendations.append("• Improve diversification by adding more positions or rebalancing")
        
        if currency['non_fiat_exposure_pct'] > 20:
            recommendations.append("• Monitor non-fiat exposure (crypto/commodities) - currently elevated")
        
        if not recommendations:
            recommendations.append("• Portfolio risk levels appear acceptable - maintain regular monitoring")
        
        for rec in recommendations:
            report += rec + "\n"
        
        report += f"""
{'='*80}
7. RISK SCORE BREAKDOWN
{'-'*80}
"""
        for risk_type, score in risk_score['risk_scores'].items():
            report += f"  {risk_type:20} {score:5.1f}/100\n"
        
        report += f"\nOVERALL RISK SCORE: {risk_score['overall_risk_score']:.1f}/100 ({risk_score['risk_level']})\n"
        
        report += f"""
{'='*80}
DISCLAIMER: This assessment is based on current portfolio holdings and general
market assumptions. Actual risk may vary based on market conditions, correlation
between assets, and unforeseen events. Consider consulting with a financial
advisor for personalized advice.
"""
        
        return report

def main():
    """Run comprehensive risk assessment"""
    assessor = RiskAssessment()
    report = assessor.generate_comprehensive_report()
    
    print(report)
    
    # Save report
    report_file = Path("/Users/claudemini/Claude/Code/utils/portfolio_data") / f"risk_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\nRisk assessment saved to: {report_file}")

if __name__ == "__main__":
    main()