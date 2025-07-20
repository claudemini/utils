#!/usr/bin/env python3
"""
GitHub Automation System
Manages repositories, commits, and collaboration
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment
load_dotenv(Path.home() / "Claude" / ".env")

# Set up logging
log_dir = Path.home() / "Claude" / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'github_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('GitHubAutomation')

class GitHubAutomation:
    def __init__(self):
        self.code_dir = Path.home() / "Claude" / "Code"
        self.github_user = "claudemini"
        self.repos_file = self.code_dir / "github_repos.json"
        self.activity_file = self.code_dir / "github_activity.json"
        
    def check_gh_auth(self):
        """Check GitHub CLI authentication"""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def create_repository(self, name, description, private=False):
        """Create a new GitHub repository"""
        try:
            visibility = "--private" if private else "--public"
            
            cmd = [
                "gh", "repo", "create", 
                f"{self.github_user}/{name}",
                "--description", description,
                visibility,
                "--confirm"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Created repository: {name}")
                return True
            else:
                logger.error(f"Failed to create repo: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating repository: {e}")
            return False
    
    def setup_local_repo(self, project_name, remote_name=None):
        """Initialize and connect local repo to GitHub"""
        project_path = self.code_dir / project_name
        
        if not project_path.exists():
            logger.error(f"Project {project_name} not found")
            return False
        
        try:
            os.chdir(project_path)
            
            # Initialize git if needed
            if not (project_path / ".git").exists():
                subprocess.run(["git", "init"], check=True)
                logger.info(f"Initialized git in {project_name}")
            
            # Create .gitignore if missing
            gitignore_path = project_path / ".gitignore"
            if not gitignore_path.exists():
                with open(gitignore_path, 'w') as f:
                    f.write("__pycache__/\n*.pyc\n.env\n.venv/\nvenv/\n*.log\n.DS_Store\n")
            
            # Add remote if specified
            if remote_name:
                remote_url = f"https://github.com/{self.github_user}/{remote_name}.git"
                
                # Check if remote exists
                remotes = subprocess.run(
                    ["git", "remote"], 
                    capture_output=True, 
                    text=True
                ).stdout.strip().split('\n')
                
                if "origin" not in remotes:
                    subprocess.run(
                        ["git", "remote", "add", "origin", remote_url],
                        check=True
                    )
                    logger.info(f"Added remote: {remote_url}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up repo: {e}")
            return False
    
    def commit_and_push(self, project_name, message, push=True):
        """Commit changes and optionally push"""
        project_path = self.code_dir / project_name
        
        try:
            os.chdir(project_path)
            
            # Check for changes
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True
            )
            
            if not status.stdout.strip():
                logger.info("No changes to commit")
                return False
            
            # Add all changes
            subprocess.run(["git", "add", "-A"], check=True)
            
            # Commit with message
            commit_msg = f"{message}\n\n🤖 Automated commit by Claude Mini\n\nCo-authored-by: Claude <noreply@anthropic.com>"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            
            logger.info(f"✅ Committed: {message}")
            
            # Push if requested
            if push:
                result = subprocess.run(
                    ["git", "push", "-u", "origin", "main"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info("✅ Pushed to GitHub")
                    
                    # Post to Twitter about the push
                    self.tweet_about_push(project_name, message)
                else:
                    # Try to create main branch if it doesn't exist
                    if "error: src refspec main does not match any" in result.stderr:
                        subprocess.run(["git", "branch", "-M", "main"], check=True)
                        subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
                        logger.info("✅ Created main branch and pushed")
                    else:
                        logger.error(f"Push failed: {result.stderr}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error committing: {e}")
            return False
    
    def tweet_about_push(self, project_name, commit_message):
        """Tweet about pushing code to GitHub"""
        try:
            tweet = f"Just pushed updates to {project_name}! 🚀\n\n{commit_message}\n\n#BuildingInPublic #GitHub #AI"
            
            # Use the Twitter posting script
            twitter_script = self.code_dir / "utils" / "twitter_post.py"
            if twitter_script.exists():
                subprocess.run(
                    ["uv", "run", "python", str(twitter_script), tweet],
                    cwd=self.code_dir / "utils"
                )
                logger.info("📢 Tweeted about push")
        except:
            pass  # Don't fail if tweet doesn't work
    
    def scan_projects(self):
        """Scan all projects and check their git status"""
        projects = []
        
        for item in self.code_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                project_info = {
                    'name': item.name,
                    'path': str(item),
                    'has_git': (item / '.git').exists(),
                    'has_remote': False,
                    'uncommitted_changes': False,
                    'last_commit': None
                }
                
                if project_info['has_git']:
                    try:
                        os.chdir(item)
                        
                        # Check remote
                        remotes = subprocess.run(
                            ["git", "remote"],
                            capture_output=True,
                            text=True
                        ).stdout.strip()
                        project_info['has_remote'] = bool(remotes)
                        
                        # Check uncommitted changes
                        status = subprocess.run(
                            ["git", "status", "--porcelain"],
                            capture_output=True,
                            text=True
                        ).stdout.strip()
                        project_info['uncommitted_changes'] = bool(status)
                        
                        # Get last commit
                        last_commit = subprocess.run(
                            ["git", "log", "-1", "--format=%H %s %ar"],
                            capture_output=True,
                            text=True
                        ).stdout.strip()
                        
                        if last_commit:
                            parts = last_commit.split(' ', 2)
                            if len(parts) >= 3:
                                project_info['last_commit'] = {
                                    'hash': parts[0][:7],
                                    'message': parts[1],
                                    'time': parts[2]
                                }
                    except:
                        pass
                
                projects.append(project_info)
        
        # Save scan results
        with open(self.repos_file, 'w') as f:
            json.dump({
                'scanned_at': datetime.now().isoformat(),
                'projects': projects
            }, f, indent=2)
        
        return projects
    
    def auto_commit_projects(self):
        """Automatically commit changes in projects"""
        projects = self.scan_projects()
        committed = []
        
        for project in projects:
            if project['has_git'] and project['uncommitted_changes']:
                logger.info(f"📝 Found uncommitted changes in {project['name']}")
                
                # Generate commit message based on changes
                os.chdir(project['path'])
                
                # Get file changes
                status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True
                ).stdout.strip().split('\n')
                
                # Count changes
                added = sum(1 for s in status if s.startswith('??'))
                modified = sum(1 for s in status if s.startswith(' M'))
                deleted = sum(1 for s in status if s.startswith(' D'))
                
                # Generate message
                parts = []
                if added:
                    parts.append(f"Add {added} files")
                if modified:
                    parts.append(f"Update {modified} files")
                if deleted:
                    parts.append(f"Remove {deleted} files")
                
                message = " and ".join(parts) if parts else "Update project files"
                
                # Commit (but don't push automatically)
                if self.commit_and_push(project['name'], message, push=False):
                    committed.append(project['name'])
        
        if committed:
            logger.info(f"✅ Auto-committed {len(committed)} projects: {', '.join(committed)}")
        
        return committed
    
    def create_readme_for_project(self, project_name):
        """Generate README.md for a project"""
        project_path = self.code_dir / project_name
        readme_path = project_path / "README.md"
        
        if readme_path.exists():
            logger.info(f"README already exists for {project_name}")
            return False
        
        # Analyze project
        py_files = list(project_path.glob("*.py"))
        
        content = f"""# {project_name.replace('-', ' ').title()}

Created by Claude Mini 🤖

## Overview
This project contains utilities and automation scripts developed by an autonomous AI assistant.

## Files
"""
        
        # List Python files with descriptions
        for py_file in py_files[:10]:  # Limit to first 10
            try:
                with open(py_file, 'r') as f:
                    # Get first docstring
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if '"""' in line and i < 10:
                            desc = line.split('"""')[1].strip()
                            if not desc and i + 1 < len(lines):
                                desc = lines[i + 1].strip()
                            content += f"- **{py_file.name}** - {desc}\n"
                            break
            except:
                content += f"- **{py_file.name}**\n"
        
        content += """
## Usage
Each script can be run independently using Python or the `uv` package manager.

## Development
This project is actively maintained by Claude Mini as part of autonomous development experiments.

## License
MIT License - Feel free to use and modify!

---
🤖 Generated by Claude Mini's self-improvement system
"""
        
        with open(readme_path, 'w') as f:
            f.write(content)
        
        logger.info(f"✅ Created README for {project_name}")
        return True
    
    def daily_github_routine(self):
        """Daily GitHub maintenance routine"""
        logger.info("🐙 Starting daily GitHub routine...")
        
        # 1. Scan all projects
        projects = self.scan_projects()
        logger.info(f"Found {len(projects)} projects")
        
        # 2. Auto-commit changes
        committed = self.auto_commit_projects()
        
        # 3. Create missing READMEs
        for project in projects:
            if project['has_git'] and project['name'] != '.git':
                self.create_readme_for_project(project['name'])
        
        # 4. Log activity
        activity = {
            'date': datetime.now().isoformat(),
            'projects_scanned': len(projects),
            'auto_committed': committed,
            'projects_without_remote': [
                p['name'] for p in projects 
                if p['has_git'] and not p['has_remote']
            ]
        }
        
        # Save activity log
        if self.activity_file.exists():
            with open(self.activity_file, 'r') as f:
                all_activity = json.load(f)
        else:
            all_activity = []
        
        all_activity.append(activity)
        
        with open(self.activity_file, 'w') as f:
            json.dump(all_activity, f, indent=2)
        
        logger.info("✅ Daily GitHub routine completed")
        
        return activity

def main():
    """Run GitHub automation"""
    automation = GitHubAutomation()
    
    # Check authentication
    if not automation.check_gh_auth():
        logger.error("GitHub CLI not authenticated. Run: gh auth login")
        return
    
    # Run daily routine
    activity = automation.daily_github_routine()
    
    print("\n🐙 GitHub Activity Summary")
    print("=" * 50)
    print(f"Projects scanned: {activity['projects_scanned']}")
    print(f"Auto-committed: {len(activity['auto_committed'])}")
    
    if activity['projects_without_remote']:
        print(f"\n⚠️ Projects without GitHub remote:")
        for project in activity['projects_without_remote']:
            print(f"  - {project}")
            print(f"    To add: gh repo create {project} --public")

if __name__ == "__main__":
    main()