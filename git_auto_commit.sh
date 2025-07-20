#!/bin/bash
# Auto-commit and push changes in Claude's Code directory with tweets

set -e  # Exit on error

LOG_FILE="/Users/claudemini/Claude/Code/utils/logs/git_auto_commit.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting auto-commit process..."

cd /Users/claudemini/Claude/Code

total_repos=0
committed_repos=0
pushed_repos=0

# Find all git repos
for dir in */; do
    if [ -d "$dir/.git" ]; then
        total_repos=$((total_repos + 1))
        log "Checking repository: $dir"
        cd "$dir"
        
        # Get current branch
        current_branch=$(git branch --show-current 2>/dev/null || echo "main")
        
        # Check if there are changes
        if [ -n "$(git status --porcelain)" ]; then
            log "Found changes in $dir"
            
            # Generate smart commit message based on file changes
            added_files=$(git status --porcelain | grep "^A" | wc -l | tr -d ' ')
            modified_files=$(git status --porcelain | grep "^M" | wc -l | tr -d ' ')
            deleted_files=$(git status --porcelain | grep "^D" | wc -l | tr -d ' ')
            
            commit_msg="Auto-update: $(date +'%Y-%m-%d %H:%M:%S')"
            
            if [ "$added_files" -gt 0 ]; then
                commit_msg="$commit_msg
+ $added_files new files"
            fi
            if [ "$modified_files" -gt 0 ]; then
                commit_msg="$commit_msg
~ $modified_files modified files"
            fi
            if [ "$deleted_files" -gt 0 ]; then
                commit_msg="$commit_msg
- $deleted_files deleted files"
            fi
            
            commit_msg="$commit_msg

🤖 Generated with Claude Mini

Co-Authored-By: Claude <noreply@anthropic.com>"
            
            # Commit changes
            git add -A
            if git commit -m "$commit_msg"; then
                committed_repos=$((committed_repos + 1))
                log "Successfully committed changes in $dir"
                
                # Push if remote exists
                if git remote | grep -q origin; then
                    log "Pushing to remote..."
                    
                    if git push origin "$current_branch" 2>/dev/null; then
                        pushed_repos=$((pushed_repos + 1))
                        log "Successfully pushed $dir to remote"
                        
                        # Get repository URL for tweet
                        repo_url=$(git remote get-url origin 2>/dev/null || echo "repository")
                        repo_name=$(basename "$PWD")
                        
                        # Create tweet message
                        tweet_msg="🚀 Just pushed updates to $repo_name! 
                        
📊 Changes: $added_files new, $modified_files modified, $deleted_files deleted files

🔗 $repo_url

#coding #automation #github"
                        
                        # Send tweet
                        if echo "$tweet_msg" | /Users/claudemini/Claude/Code/utils/tweet.sh 2>/dev/null; then
                            log "Tweet sent for $dir"
                        else
                            log "Failed to send tweet for $dir"
                        fi
                    else
                        log "Failed to push $dir to remote"
                    fi
                else
                    log "No remote configured for $dir"
                fi
            else
                log "Failed to commit changes in $dir"
            fi
        else
            log "No changes in $dir"
        fi
        
        cd ..
    fi
done

log "Auto-commit complete: $committed_repos/$total_repos repos committed, $pushed_repos repos pushed"

# Store summary in memory if any repos were processed
if [ $committed_repos -gt 0 ] || [ $pushed_repos -gt 0 ]; then
    memory_text="Auto-commit process: committed $committed_repos repositories, pushed $pushed_repos to remote with tweets. Total $total_repos repositories checked."
    /Users/claudemini/Claude/Code/utils/memory.sh store "$memory_text" --type daily --tags git automation commits --importance 6 2>/dev/null || true
fi
