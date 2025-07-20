#!/usr/bin/env python3
"""
Self-Improvement System for Claude Mini
Automated code analysis, learning, and optimization
"""

import os
import sys
import json
import time
import subprocess
import ast
import logging
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Set up logging
log_dir = Path.home() / "Claude" / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'self_improvement.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SelfImprovement')

class SelfImprovementSystem:
    def __init__(self):
        self.code_dir = Path.home() / "Claude" / "Code"
        self.utils_dir = self.code_dir / "utils"
        self.metrics_file = self.utils_dir / "code_metrics.json"
        self.improvements_file = self.utils_dir / "improvements_log.json"
        self.learning_file = self.utils_dir / "learning_log.json"
        
        # Load existing metrics
        self.metrics = self.load_metrics()
        self.improvements = self.load_improvements()
        
    def load_metrics(self):
        """Load existing code metrics"""
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return {}
    
    def load_improvements(self):
        """Load improvement history"""
        if self.improvements_file.exists():
            with open(self.improvements_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_metrics(self):
        """Save metrics to file"""
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def save_improvements(self):
        """Save improvements to file"""
        with open(self.improvements_file, 'w') as f:
            json.dump(self.improvements, f, indent=2)
    
    def analyze_python_file(self, file_path):
        """Analyze a Python file for improvement opportunities"""
        analysis = {
            'file': str(file_path),
            'lines': 0,
            'functions': 0,
            'classes': 0,
            'complexity': 0,
            'issues': [],
            'suggestions': []
        }
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                analysis['lines'] = len(content.splitlines())
            
            # Parse AST
            tree = ast.parse(content)
            
            # Count structures
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis['functions'] += 1
                    # Check function length
                    func_lines = node.end_lineno - node.lineno
                    if func_lines > 50:
                        analysis['issues'].append(f"Function '{node.name}' is {func_lines} lines (consider splitting)")
                elif isinstance(node, ast.ClassDef):
                    analysis['classes'] += 1
            
            # Check for common patterns
            if 'try:' in content and 'except:' in content:
                if 'except Exception:' in content or 'except:' in content:
                    analysis['issues'].append("Generic exception handling detected")
            
            if analysis['lines'] > 500:
                analysis['suggestions'].append("Consider splitting this file into smaller modules")
            
            # Check for duplicate code
            lines = content.splitlines()
            seen_lines = defaultdict(int)
            for line in lines:
                stripped = line.strip()
                if len(stripped) > 20 and not stripped.startswith('#'):
                    seen_lines[stripped] += 1
            
            duplicates = {k: v for k, v in seen_lines.items() if v > 2}
            if duplicates:
                analysis['issues'].append(f"Found {len(duplicates)} duplicate code patterns")
                
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            
        return analysis
    
    def analyze_codebase(self):
        """Analyze entire codebase for improvements"""
        logger.info("🔍 Analyzing codebase for improvements...")
        
        all_analyses = []
        
        # Analyze Python files
        for py_file in self.utils_dir.glob("*.py"):
            if py_file.name != "__pycache__":
                analysis = self.analyze_python_file(py_file)
                all_analyses.append(analysis)
        
        # Summary statistics
        total_lines = sum(a['lines'] for a in all_analyses)
        total_functions = sum(a['functions'] for a in all_analyses)
        total_issues = sum(len(a['issues']) for a in all_analyses)
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(all_analyses),
            'total_lines': total_lines,
            'total_functions': total_functions,
            'total_issues': total_issues,
            'files_with_issues': [a for a in all_analyses if a['issues']]
        }
        
        self.metrics['latest_analysis'] = summary
        self.save_metrics()
        
        return summary
    
    def optimize_imports(self):
        """Optimize imports across Python files"""
        logger.info("📦 Optimizing imports...")
        
        improvements = []
        
        try:
            # Use isort to sort imports
            result = subprocess.run(
                ["python", "-m", "isort", str(self.utils_dir), "--check-only", "--diff"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                # Apply the fixes
                fix_result = subprocess.run(
                    ["python", "-m", "isort", str(self.utils_dir)],
                    capture_output=True,
                    text=True
                )
                
                if fix_result.returncode == 0:
                    improvements.append({
                        'type': 'import_optimization',
                        'description': 'Sorted and organized imports',
                        'timestamp': datetime.now().isoformat()
                    })
                    logger.info("✅ Import optimization completed")
        except:
            logger.warning("isort not available, skipping import optimization")
            
        return improvements
    
    def check_type_hints(self):
        """Check for missing type hints"""
        logger.info("🏷️ Checking type hints...")
        
        missing_hints = []
        
        for py_file in self.utils_dir.glob("*.py"):
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check if function has return type
                        if not node.returns and node.name != '__init__':
                            missing_hints.append({
                                'file': py_file.name,
                                'function': node.name,
                                'issue': 'missing_return_type'
                            })
                        
                        # Check parameters
                        for arg in node.args.args:
                            if not arg.annotation and arg.arg != 'self':
                                missing_hints.append({
                                    'file': py_file.name,
                                    'function': node.name,
                                    'parameter': arg.arg,
                                    'issue': 'missing_param_type'
                                })
            except:
                pass
        
        if missing_hints:
            logger.info(f"Found {len(missing_hints)} missing type hints")
            
        return missing_hints
    
    def generate_documentation(self):
        """Generate documentation for undocumented functions"""
        logger.info("📝 Checking documentation...")
        
        undocumented = []
        
        for py_file in self.utils_dir.glob("*.py"):
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check if function has docstring
                        if not ast.get_docstring(node):
                            undocumented.append({
                                'file': py_file.name,
                                'function': node.name,
                                'line': node.lineno
                            })
            except:
                pass
        
        if undocumented:
            logger.info(f"Found {len(undocumented)} undocumented functions")
            
        return undocumented
    
    def learn_from_errors(self):
        """Analyze logs for common errors and learn from them"""
        logger.info("🎓 Learning from errors...")
        
        error_patterns = defaultdict(int)
        solutions = {}
        
        # Check various log files
        log_dir = Path.home() / "Claude" / "logs"
        log_files = [
            log_dir / "twitter_automation.log",
            log_dir / "system_monitor.log",
            log_dir / "self_improvement.log"
        ]
        
        for log_file in log_files:
            if log_file.exists():
                try:
                    with open(log_file, 'r') as f:
                        for line in f:
                            if 'ERROR' in line or 'error' in line:
                                # Extract error type
                                if 'ModuleNotFoundError' in line:
                                    error_patterns['missing_module'] += 1
                                elif 'Permission denied' in line:
                                    error_patterns['permission'] += 1
                                elif 'timeout' in line.lower():
                                    error_patterns['timeout'] += 1
                                elif 'connection' in line.lower():
                                    error_patterns['connection'] += 1
                except:
                    pass
        
        # Generate solutions
        if error_patterns['missing_module'] > 2:
            solutions['missing_module'] = "Create requirements.txt and automated dependency installer"
        if error_patterns['timeout'] > 3:
            solutions['timeout'] = "Implement better timeout handling and retry logic"
        if error_patterns['connection'] > 2:
            solutions['connection'] = "Add network connectivity checks before operations"
            
        learning = {
            'timestamp': datetime.now().isoformat(),
            'errors_analyzed': sum(error_patterns.values()),
            'patterns': dict(error_patterns),
            'proposed_solutions': solutions
        }
        
        # Save learning
        if self.learning_file.exists():
            with open(self.learning_file, 'r') as f:
                all_learning = json.load(f)
        else:
            all_learning = []
            
        all_learning.append(learning)
        
        with open(self.learning_file, 'w') as f:
            json.dump(all_learning, f, indent=2)
        
        return learning
    
    def create_improvement_plan(self):
        """Create an actionable improvement plan"""
        logger.info("📋 Creating improvement plan...")
        
        # Analyze current state
        analysis = self.analyze_codebase()
        missing_hints = self.check_type_hints()
        undocumented = self.generate_documentation()
        learning = self.learn_from_errors()
        
        plan = {
            'created_at': datetime.now().isoformat(),
            'priorities': []
        }
        
        # High priority improvements
        if analysis['total_issues'] > 10:
            plan['priorities'].append({
                'priority': 'high',
                'task': 'refactor_complex_functions',
                'description': f"Refactor {analysis['total_issues']} code issues",
                'files': [f['file'] for f in analysis['files_with_issues']]
            })
        
        if len(missing_hints) > 20:
            plan['priorities'].append({
                'priority': 'medium',
                'task': 'add_type_hints',
                'description': f"Add {len(missing_hints)} missing type hints",
                'count': len(missing_hints)
            })
        
        if len(undocumented) > 10:
            plan['priorities'].append({
                'priority': 'medium',
                'task': 'add_documentation',
                'description': f"Document {len(undocumented)} functions",
                'functions': undocumented[:5]  # First 5 as examples
            })
        
        if learning['proposed_solutions']:
            plan['priorities'].append({
                'priority': 'high',
                'task': 'implement_error_solutions',
                'description': "Implement solutions for recurring errors",
                'solutions': learning['proposed_solutions']
            })
        
        # Save plan
        plan_file = self.utils_dir / "improvement_plan.json"
        with open(plan_file, 'w') as f:
            json.dump(plan, f, indent=2)
        
        logger.info(f"✅ Improvement plan created with {len(plan['priorities'])} priorities")
        
        return plan
    
    def daily_improvement_cycle(self):
        """Run daily improvement cycle"""
        logger.info("🔄 Starting daily improvement cycle...")
        
        # 1. Analyze codebase
        analysis = self.analyze_codebase()
        logger.info(f"📊 Analyzed {analysis['total_files']} files, found {analysis['total_issues']} issues")
        
        # 2. Optimize what we can
        import_improvements = self.optimize_imports()
        
        # 3. Learn from errors
        learning = self.learn_from_errors()
        logger.info(f"🎓 Learned from {learning['errors_analyzed']} errors")
        
        # 4. Create improvement plan
        plan = self.create_improvement_plan()
        
        # 5. Log improvement
        improvement_entry = {
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis,
            'improvements_made': import_improvements,
            'learning': learning,
            'plan': plan
        }
        
        self.improvements.append(improvement_entry)
        self.save_improvements()
        
        # 6. Commit improvements if any were made
        if import_improvements:
            self.commit_improvements("Automated code improvements: optimized imports")
        
        logger.info("✅ Daily improvement cycle completed")
        
        return improvement_entry
    
    def commit_improvements(self, message):
        """Commit improvements to git"""
        try:
            os.chdir(self.utils_dir)
            
            # Check if there are changes
            status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            
            if status.stdout.strip():
                # Add and commit
                subprocess.run(["git", "add", "-A"], check=True)
                subprocess.run(["git", "commit", "-m", f"{message}\n\n🤖 Automated by self-improvement system"], check=True)
                logger.info(f"✅ Committed improvements: {message}")
                
                # Could also push if desired
                # subprocess.run(["git", "push"], check=True)
        except Exception as e:
            logger.error(f"Failed to commit improvements: {e}")

def main():
    """Run self-improvement system"""
    system = SelfImprovementSystem()
    
    # Run improvement cycle
    result = system.daily_improvement_cycle()
    
    # Print summary
    print("\n🤖 Self-Improvement Summary")
    print("=" * 50)
    print(f"Files analyzed: {result['analysis']['total_files']}")
    print(f"Issues found: {result['analysis']['total_issues']}")
    print(f"Improvements made: {len(result['improvements_made'])}")
    print(f"Errors learned from: {result['learning']['errors_analyzed']}")
    print(f"Improvement priorities: {len(result['plan']['priorities'])}")
    
    if result['plan']['priorities']:
        print("\n📋 Top Priorities:")
        for priority in result['plan']['priorities'][:3]:
            print(f"  - [{priority['priority']}] {priority['description']}")

if __name__ == "__main__":
    main()