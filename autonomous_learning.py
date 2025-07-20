#!/usr/bin/env python3
"""
Autonomous learning system for Claude Mini
Daily code analysis, optimization suggestions, and self-improvement
"""

import os
import subprocess
import json
import ast
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import logging

# Setup logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'autonomous_learning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('autonomous_learning')

@dataclass
class CodeIssue:
    """Represents a code issue found during analysis"""
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # low, medium, high, critical
    description: str
    suggestion: str
    code_snippet: str

@dataclass
class LearningInsight:
    """Represents a learning insight or improvement"""
    category: str  # performance, security, maintainability, etc.
    title: str
    description: str
    impact: str  # low, medium, high
    actionable: bool
    implementation_notes: str

class AutonomousLearning:
    """Main autonomous learning system"""
    
    def __init__(self):
        self.code_dir = Path("/Users/claudemini/Claude/Code")
        self.data_dir = Path(__file__).parent / "data" / "learning"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Analysis results storage
        self.issues_file = self.data_dir / "code_issues.json"
        self.insights_file = self.data_dir / "learning_insights.json"
        self.progress_file = self.data_dir / "learning_progress.json"
        
    def analyze_python_file(self, file_path: Path) -> List[CodeIssue]:
        """Analyze a Python file for issues and improvements"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Parse AST for deeper analysis
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=e.lineno or 0,
                    issue_type="syntax_error",
                    severity="critical",
                    description=f"Syntax error: {e.msg}",
                    suggestion="Fix syntax error to make code executable",
                    code_snippet=lines[e.lineno-1] if e.lineno and e.lineno <= len(lines) else ""
                ))
                return issues
            
            # Check for common issues
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Long lines
                if len(line) > 120:
                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="line_length",
                        severity="low",
                        description="Line exceeds 120 characters",
                        suggestion="Break into multiple lines or refactor",
                        code_snippet=line[:100] + "..."
                    ))
                
                # TODO comments
                if "TODO" in line_stripped or "FIXME" in line_stripped:
                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="todo",
                        severity="medium",
                        description="TODO or FIXME comment found",
                        suggestion="Address the TODO item or create a proper issue",
                        code_snippet=line_stripped
                    ))
                
                # Hardcoded credentials (improved check)
                if any(keyword in line_stripped.lower() for keyword in ['password', 'secret', 'api_key', 'token']) and '=' in line_stripped:
                    # Check if it's actually using safe practices
                    safe_patterns = ['getenv', 'os.environ', 'config', 'env.get', 'settings.', 'conf.']
                    is_using_safe_pattern = any(pattern in line_stripped.lower() for pattern in safe_patterns)
                    
                    # Check for actual hardcoded values (quotes with content that looks like credentials)
                    has_quoted_value = any(quote in line_stripped for quote in ['"', "'"])
                    potential_hardcoded = False
                    
                    if has_quoted_value and not is_using_safe_pattern:
                        # Look for patterns like: password = "actual_password" or token = 'abc123'
                        import re
                        hardcoded_pattern = r'(password|secret|api_key|token)\s*=\s*["\'][^"\']{8,}["\']'
                        if re.search(hardcoded_pattern, line_stripped.lower()):
                            potential_hardcoded = True
                    
                    if potential_hardcoded:
                        issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=i,
                            issue_type="security",
                            severity="high",
                            description="Potential hardcoded credential detected",
                            suggestion="Use environment variables or config files instead of hardcoded values",
                            code_snippet="[REDACTED FOR SECURITY]"
                        ))
                
                # Print statements in production code
                if line_stripped.startswith('print(') and 'debug' not in file_path.name.lower():
                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=i,
                        issue_type="debugging",
                        severity="low",
                        description="Print statement found in production code",
                        suggestion="Use logging instead of print statements",
                        code_snippet=line_stripped
                    ))
            
            # AST-based checks
            for node in ast.walk(tree):
                # Missing type hints on functions
                if isinstance(node, ast.FunctionDef):
                    if not node.returns and node.name != '__init__':
                        issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            issue_type="type_hints",
                            severity="low",
                            description=f"Function '{node.name}' missing return type hint",
                            suggestion="Add return type hint for better code documentation",
                            code_snippet=f"def {node.name}(...):"
                        ))
                
                # Bare except clauses
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    issues.append(CodeIssue(
                        file_path=str(file_path),
                        line_number=node.lineno,
                        issue_type="exception_handling",
                        severity="medium",
                        description="Bare except clause found",
                        suggestion="Catch specific exceptions instead of using bare except",
                        code_snippet="except:"
                    ))
                        
        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")
            
        return issues
    
    def analyze_codebase(self) -> Dict[str, List[CodeIssue]]:
        """Analyze the entire codebase for issues"""
        logger.info("Starting codebase analysis...")
        all_issues = {}
        
        # Find all Python files
        python_files = list(self.code_dir.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files to analyze")
        
        for file_path in python_files:
            # Skip virtual environment and cache files
            if any(skip in str(file_path) for skip in ['.venv', '__pycache__', '.git']):
                continue
                
            issues = self.analyze_python_file(file_path)
            if issues:
                all_issues[str(file_path)] = issues
                
        # Save issues
        self.save_issues(all_issues)
        
        # Generate summary
        total_issues = sum(len(issues) for issues in all_issues.values())
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for issues in all_issues.values():
            for issue in issues:
                severity_counts[issue.severity] += 1
        
        logger.info(f"Analysis complete: {total_issues} issues found")
        logger.info(f"Severity breakdown: {severity_counts}")
        
        return all_issues
    
    def save_issues(self, issues: Dict[str, List[CodeIssue]]):
        """Save issues to file"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'issues': {
                file_path: [asdict(issue) for issue in file_issues]
                for file_path, file_issues in issues.items()
            }
        }
        
        with open(self.issues_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def generate_learning_insights(self, issues: Dict[str, List[CodeIssue]]) -> List[LearningInsight]:
        """Generate learning insights from code analysis"""
        insights = []
        
        # Count issue types
        issue_type_counts = {}
        for file_issues in issues.values():
            for issue in file_issues:
                issue_type_counts[issue.issue_type] = issue_type_counts.get(issue.issue_type, 0) + 1
        
        # Generate insights based on patterns
        if issue_type_counts.get('type_hints', 0) > 5:
            insights.append(LearningInsight(
                category="maintainability",
                title="Improve Type Hint Coverage",
                description=f"Found {issue_type_counts['type_hints']} functions without return type hints. Type hints improve code readability and help catch errors early.",
                impact="medium",
                actionable=True,
                implementation_notes="Add return type hints to functions, starting with public APIs"
            ))
        
        if issue_type_counts.get('exception_handling', 0) > 2:
            insights.append(LearningInsight(
                category="reliability",
                title="Improve Exception Handling",
                description=f"Found {issue_type_counts['exception_handling']} bare except clauses. Specific exception handling makes debugging easier.",
                impact="high",
                actionable=True,
                implementation_notes="Replace bare except with specific exception types"
            ))
        
        if issue_type_counts.get('security', 0) > 0:
            insights.append(LearningInsight(
                category="security",
                title="Review Security Practices",
                description=f"Found {issue_type_counts['security']} potential security issues. Hardcoded credentials pose significant risks.",
                impact="high",
                actionable=True,
                implementation_notes="Move all secrets to environment variables or secure config files"
            ))
        
        if issue_type_counts.get('debugging', 0) > 3:
            insights.append(LearningInsight(
                category="best_practices",
                title="Replace Print Statements with Logging",
                description=f"Found {issue_type_counts['debugging']} print statements. Proper logging provides better control over output.",
                impact="low",
                actionable=True,
                implementation_notes="Replace print() with logger.info(), logger.debug(), etc."
            ))
        
        # Performance insights
        large_files = [f for f, issues_list in issues.items() 
                      if any(i.issue_type == 'line_length' for i in issues_list)]
        
        if len(large_files) > 3:
            insights.append(LearningInsight(
                category="maintainability",
                title="Consider Code Refactoring",
                description=f"Multiple files have long lines, suggesting complex functions that could be refactored.",
                impact="medium",
                actionable=True,
                implementation_notes="Break down large functions into smaller, focused functions"
            ))
        
        # Save insights
        self.save_insights(insights)
        return insights
    
    def save_insights(self, insights: List[LearningInsight]):
        """Save learning insights"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'insights': [asdict(insight) for insight in insights]
        }
        
        with open(self.insights_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def generate_improvement_plan(self, insights: List[LearningInsight]) -> str:
        """Generate an actionable improvement plan"""
        plan = ["🧠 Autonomous Learning Report", "=" * 40, ""]
        
        # Prioritize by impact
        high_impact = [i for i in insights if i.impact == "high"]
        medium_impact = [i for i in insights if i.impact == "medium"]
        low_impact = [i for i in insights if i.impact == "low"]
        
        if high_impact:
            plan.append("🚨 High Priority Items:")
            for insight in high_impact:
                plan.append(f"  • {insight.title}")
                plan.append(f"    {insight.description}")
                if insight.actionable:
                    plan.append(f"    💡 Action: {insight.implementation_notes}")
                plan.append("")
        
        if medium_impact:
            plan.append("⚠️ Medium Priority Items:")
            for insight in medium_impact:
                plan.append(f"  • {insight.title}")
                plan.append(f"    {insight.description}")
                plan.append("")
        
        if low_impact:
            plan.append("ℹ️ Low Priority Items:")
            for insight in low_impact:
                plan.append(f"  • {insight.title}")
            plan.append("")
        
        # Next steps
        plan.extend([
            "📅 Recommended Next Steps:",
            "1. Address high-priority security and reliability issues first",
            "2. Implement systematic type hint addition",
            "3. Refactor complex functions identified",
            "4. Set up automated code quality checks",
            "",
            f"🤖 Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ])
        
        return "\n".join(plan)
    
    def run_daily_analysis(self) -> str:
        """Run the daily autonomous learning analysis"""
        logger.info("Starting daily autonomous learning analysis...")
        
        # Analyze codebase
        issues = self.analyze_codebase()
        
        # Generate insights
        insights = self.generate_learning_insights(issues)
        
        # Create improvement plan
        plan = self.generate_improvement_plan(insights)
        
        # Update progress tracking
        self.update_progress(issues, insights)
        
        # Store in memory system
        self.store_learning_memory(issues, insights)
        
        logger.info("Daily analysis complete")
        return plan
    
    def update_progress(self, issues: Dict[str, List[CodeIssue]], insights: List[LearningInsight]):
        """Update learning progress tracking"""
        progress_data = {
            'timestamp': datetime.now().isoformat(),
            'total_issues': sum(len(file_issues) for file_issues in issues.values()),
            'issue_breakdown': {},
            'insights_count': len(insights),
            'high_priority_insights': len([i for i in insights if i.impact == "high"])
        }
        
        # Count issues by type
        for file_issues in issues.values():
            for issue in file_issues:
                progress_data['issue_breakdown'][issue.issue_type] = \
                    progress_data['issue_breakdown'].get(issue.issue_type, 0) + 1
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
    
    def store_learning_memory(self, issues: Dict[str, List[CodeIssue]], insights: List[LearningInsight]):
        """Store learning results in memory system"""
        try:
            total_issues = sum(len(file_issues) for file_issues in issues.values())
            high_priority = len([i for i in insights if i.impact == "high"])
            
            memory_text = f"Daily autonomous learning analysis: Found {total_issues} code issues across {len(issues)} files. Generated {len(insights)} improvement insights with {high_priority} high-priority items. Key areas: type hints, exception handling, security practices."
            
            # Use the memory system
            memory_script = Path(__file__).parent / "memory.sh"
            if memory_script.exists():
                import subprocess
                cmd = [
                    str(memory_script), "store", memory_text,
                    "--type", "daily",
                    "--tags", "autonomous-learning code-analysis improvement",
                    "--importance", "8"
                ]
                subprocess.run(cmd, cwd=str(memory_script.parent), capture_output=True)
                
        except Exception as e:
            logger.warning(f"Failed to store learning memory: {e}")

def main():
    """Main function"""
    learning_system = AutonomousLearning()
    
    if len(os.sys.argv) > 1:
        command = os.sys.argv[1]
        
        if command == 'analyze':
            plan = learning_system.run_daily_analysis()
            print(plan)
        elif command == 'issues':
            issues = learning_system.analyze_codebase()
            total = sum(len(file_issues) for file_issues in issues.values())
            print(f"Found {total} issues across {len(issues)} files")
    else:
        # Default: run full analysis
        plan = learning_system.run_daily_analysis()
        print(plan)

if __name__ == "__main__":
    import sys
    main()