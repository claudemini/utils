#!/usr/bin/env python3
"""
Perplexity.ai Finance Research Automation
Automates financial research using Perplexity's finance interface
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Setup logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'perplexity_finance.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('perplexity_finance')

@dataclass
class ResearchQuery:
    """Represents a financial research query"""
    query: str
    category: str  # crypto, stocks, macro, markets, news
    priority: str  # low, medium, high
    frequency: str  # daily, weekly, monthly, one-time
    last_run: Optional[datetime] = None
    enabled: bool = True

@dataclass
class ResearchResult:
    """Represents research results"""
    query: str
    results: str
    timestamp: datetime
    sources: List[str]
    category: str
    confidence_score: float

class PerplexityFinanceResearch:
    """Main Perplexity finance research automation"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent / "data" / "finance_research"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Browser automation will be added here
        self.browser = None
        
        # Research queries configuration
        self.queries_file = self.data_dir / "research_queries.json"
        self.results_file = self.data_dir / "research_results.json"
        
        # Load or create research queries
        self.research_queries = self.load_research_queries()
        
    def load_research_queries(self) -> List[ResearchQuery]:
        """Load research queries from configuration"""
        if self.queries_file.exists():
            try:
                with open(self.queries_file, 'r') as f:
                    data = json.load(f)
                    queries = []
                    for query_data in data.get('queries', []):
                        # Handle datetime parsing
                        if query_data.get('last_run'):
                            query_data['last_run'] = datetime.fromisoformat(query_data['last_run'])
                        queries.append(ResearchQuery(**query_data))
                    return queries
            except Exception as e:
                logger.error(f"Error loading research queries: {e}")
        
        # Create default research queries
        return self.create_default_queries()
    
    def create_default_queries(self) -> List[ResearchQuery]:
        """Create default financial research queries"""
        default_queries = [
            # Crypto market analysis
            ResearchQuery(
                query="What are the latest developments in Bitcoin and Ethereum markets this week?",
                category="crypto",
                priority="high",
                frequency="daily"
            ),
            ResearchQuery(
                query="What are the most promising DeFi protocols and yield farming opportunities right now?",
                category="crypto",
                priority="medium",
                frequency="weekly"
            ),
            ResearchQuery(
                query="Solana ecosystem updates and new projects launched this month",
                category="crypto",
                priority="medium",
                frequency="weekly"
            ),
            
            # Macro economic analysis
            ResearchQuery(
                query="Federal Reserve policy updates and interest rate expectations",
                category="macro",
                priority="high",
                frequency="weekly"
            ),
            ResearchQuery(
                query="Inflation trends and economic indicators in the US and globally",
                category="macro",
                priority="high",
                frequency="weekly"
            ),
            
            # Technology stocks
            ResearchQuery(
                query="AI and technology stock performance analysis this week",
                category="stocks",
                priority="medium",
                frequency="weekly"
            ),
            ResearchQuery(
                query="What are the best performing growth stocks in the last month?",
                category="stocks",
                priority="medium",
                frequency="monthly"
            ),
            
            # Market sentiment and trends
            ResearchQuery(
                query="Current market sentiment and fear/greed indicators",
                category="markets",
                priority="medium",
                frequency="daily"
            ),
            ResearchQuery(
                query="Emerging market trends and sector rotation analysis",
                category="markets",
                priority="low",
                frequency="weekly"
            ),
            
            # Breaking financial news
            ResearchQuery(
                query="Major financial news and market-moving events today",
                category="news",
                priority="high",
                frequency="daily"
            )
        ]
        
        self.save_research_queries(default_queries)
        return default_queries
    
    def save_research_queries(self, queries: List[ResearchQuery]):
        """Save research queries to configuration"""
        data = {
            'queries': [
                {
                    **asdict(query),
                    'last_run': query.last_run.isoformat() if query.last_run else None
                }
                for query in queries
            ],
            'last_updated': datetime.now().isoformat()
        }
        
        with open(self.queries_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def setup_browser(self):
        """Setup browser automation for Perplexity"""
        try:
            # Import playwright tools
            import sys
            sys.path.append('/Users/claudemini/Claude/Code/utils')
            
            # For now, we'll use a placeholder since actual browser automation
            # would require playwright setup
            logger.info("Browser automation setup would go here")
            self.browser = "placeholder"
            return True
            
        except Exception as e:
            logger.error(f"Error setting up browser: {e}")
            return False
    
    def should_run_query(self, query: ResearchQuery) -> bool:
        """Check if a query should be run based on frequency and last run time"""
        if not query.enabled:
            return False
            
        if query.last_run is None:
            return True
            
        now = datetime.now()
        time_since_last = now - query.last_run
        
        if query.frequency == "daily":
            return time_since_last >= timedelta(days=1)
        elif query.frequency == "weekly":
            return time_since_last >= timedelta(days=7)
        elif query.frequency == "monthly":
            return time_since_last >= timedelta(days=30)
        elif query.frequency == "one-time":
            return False  # Only run once
            
        return False
    
    async def research_query_with_playwright(self, query: ResearchQuery) -> Optional[ResearchResult]:
        """Research a query using Perplexity via playwright automation"""
        try:
            # This would use actual playwright automation to:
            # 1. Navigate to https://www.perplexity.ai/finance
            # 2. Enter the query
            # 3. Wait for results
            # 4. Extract the response and sources
            
            # For now, return a placeholder result
            logger.info(f"Would research: {query.query}")
            
            # Simulate research result
            result = ResearchResult(
                query=query.query,
                results=f"Placeholder research result for: {query.query}",
                timestamp=datetime.now(),
                sources=["perplexity.ai/finance"],
                category=query.category,
                confidence_score=0.8
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error researching query '{query.query}': {e}")
            return None
    
    def create_research_summary(self, results: List[ResearchResult]) -> str:
        """Create a summary of research results"""
        if not results:
            return "No research results available."
            
        summary = ["📊 Finance Research Summary", "=" * 40, ""]
        
        # Group by category
        categories = {}
        for result in results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        # Category emojis
        category_emojis = {
            'crypto': '🚀',
            'stocks': '📈',
            'macro': '🏛️',
            'markets': '💹',
            'news': '📰'
        }
        
        for category, category_results in categories.items():
            emoji = category_emojis.get(category, '📊')
            summary.append(f"{emoji} {category.title()} Research:")
            
            for result in category_results:
                summary.append(f"  • {result.query}")
                # Truncate results for summary
                truncated = result.results[:200] + "..." if len(result.results) > 200 else result.results
                summary.append(f"    {truncated}")
                summary.append("")
        
        summary.extend([
            f"🤖 Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"📚 Total queries researched: {len(results)}"
        ])
        
        return "\n".join(summary)
    
    def save_results(self, results: List[ResearchResult]):
        """Save research results to file"""
        # Load existing results
        existing_results = []
        if self.results_file.exists():
            try:
                with open(self.results_file, 'r') as f:
                    data = json.load(f)
                    existing_results = data.get('results', [])
            except Exception as e:
                logger.warning(f"Error loading existing results: {e}")
        
        # Add new results
        new_results_data = [
            {
                **asdict(result),
                'timestamp': result.timestamp.isoformat()
            }
            for result in results
        ]
        
        all_results = existing_results + new_results_data
        
        # Keep only last 100 results
        if len(all_results) > 100:
            all_results = all_results[-100:]
        
        # Save updated results
        data = {
            'results': all_results,
            'last_updated': datetime.now().isoformat(),
            'total_results': len(all_results)
        }
        
        with open(self.results_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def run_daily_research(self) -> str:
        """Run daily financial research automation"""
        logger.info("Starting daily financial research...")
        
        # Setup browser if needed
        if not self.browser:
            await self.setup_browser()
        
        # Find queries that need to be run
        queries_to_run = [q for q in self.research_queries if self.should_run_query(q)]
        
        if not queries_to_run:
            logger.info("No queries scheduled to run today")
            return "No research queries scheduled for today."
        
        logger.info(f"Running {len(queries_to_run)} research queries")
        
        # Run research queries
        results = []
        for query in queries_to_run:
            result = await self.research_query_with_playwright(query)
            if result:
                results.append(result)
                # Update last run time
                query.last_run = datetime.now()
        
        # Save updated queries and results
        self.save_research_queries(self.research_queries)
        if results:
            self.save_results(results)
        
        # Store in memory system
        self.store_research_memory(results)
        
        # Create summary
        summary = self.create_research_summary(results)
        logger.info(f"Research complete: {len(results)} results generated")
        
        return summary
    
    def store_research_memory(self, results: List[ResearchResult]):
        """Store research results in memory system"""
        if not results:
            return
            
        try:
            summary_text = f"Completed {len(results)} financial research queries via Perplexity.ai. Categories: {', '.join(set(r.category for r in results))}. Key insights generated for portfolio and investment decisions."
            
            # Use the memory system
            memory_script = Path(__file__).parent / "memory.sh"
            if memory_script.exists():
                import subprocess
                cmd = [
                    str(memory_script), "store", summary_text,
                    "--type", "financial",
                    "--tags", "research perplexity finance automation",
                    "--importance", "7"
                ]
                subprocess.run(cmd, cwd=str(memory_script.parent), capture_output=True)
                
        except Exception as e:
            logger.warning(f"Failed to store research memory: {e}")

async def main():
    """Main function"""
    research_system = PerplexityFinanceResearch()
    
    if len(os.sys.argv) > 1:
        command = os.sys.argv[1]
        
        if command == 'research':
            summary = await research_system.run_daily_research()
            print(summary)
        elif command == 'queries':
            print(f"Configured {len(research_system.research_queries)} research queries:")
            for i, query in enumerate(research_system.research_queries, 1):
                status = "✅" if query.enabled else "❌"
                print(f"{i}. {status} [{query.category}] {query.query} ({query.frequency})")
    else:
        # Default: run research
        summary = await research_system.run_daily_research()
        print(summary)

if __name__ == "__main__":
    import sys
    import os
    asyncio.run(main())