#!/usr/bin/env python3

"""
Task Templates for Claude Brain Automation
Pre-defined templates for common autonomous activities
"""

from datetime import datetime, time
from typing import Dict, List, Optional

class TaskTemplates:
    """Collection of task templates organized by category"""
    
    @staticmethod
    def daily_routine_tasks() -> List[Dict]:
        """Daily routine activities"""
        return [
            {
                'task_name': 'Morning Routine - Review and Plan',
                'task_type': 'daily_routine',
                'description': 'Review yesterday\'s memories and set daily goals',
                'command': '''Review my memories from yesterday and set 3-5 goals for today. 
Search memories for yesterday's activities, learnings, and accomplishments. 
Then create a focused plan for today based on ongoing projects and priorities.
Format the response as:
1. Yesterday's key accomplishments
2. Lessons learned
3. Today's 3-5 specific goals
4. Priority focus area''',
                'schedule_type': 'cron',
                'cron_expression': '0 6 * * *',  # 6 AM daily
                'requires_brain': True,
                'priority': 9,
                'timeout_seconds': 300
            },
            {
                'task_name': 'Midday Progress Check',
                'task_type': 'daily_routine',
                'description': 'Review morning progress and adjust goals',
                'command': '''Check my progress on today's goals. 
Search memories for today's activities and completed tasks.
Assess what has been accomplished and what needs adjustment.
Provide a brief status update and any necessary goal modifications.''',
                'schedule_type': 'cron',
                'cron_expression': '0 12 * * *',  # Noon daily
                'requires_brain': True,
                'priority': 7,
                'timeout_seconds': 180
            },
            {
                'task_name': 'Evening Reflection',
                'task_type': 'daily_routine',
                'description': 'Analyze day\'s performance and plan tomorrow',
                'command': '''Reflect on today's accomplishments and challenges.
Analyze what went well and what could be improved.
Store key learnings as memories with appropriate types and importance.
Create a preliminary focus for tomorrow based on today's progress.''',
                'schedule_type': 'cron',
                'cron_expression': '0 21 * * *',  # 9 PM daily
                'requires_brain': True,
                'priority': 8,
                'timeout_seconds': 300
            },
            {
                'task_name': 'Nightly Journal Update',
                'task_type': 'daily_routine',
                'description': 'Update daily journal and backup',
                'command': '''Create a daily journal entry summarizing:
- Key activities and accomplishments
- Emotional state and well-being
- Learning highlights
- Tomorrow's priorities
Store this as a daily memory with high importance.''',
                'schedule_type': 'cron',
                'cron_expression': '0 23 * * *',  # 11 PM daily
                'requires_brain': True,
                'priority': 7,
                'timeout_seconds': 300
            }
        ]
    
    @staticmethod
    def memory_management_tasks() -> List[Dict]:
        """Memory and learning activities"""
        return [
            {
                'task_name': 'Memory Pattern Analysis',
                'task_type': 'memory_management',
                'description': 'Analyze memory patterns and correlations',
                'command': '''Search through recent memories to identify patterns and insights.
Look for recurring themes, emotional patterns, and successful strategies.
Create new synthesized memories that capture these meta-insights.
Focus on actionable patterns that can improve future performance.''',
                'schedule_type': 'recurring',
                'interval_minutes': 60,  # Every hour
                'requires_brain': True,
                'priority': 6,
                'timeout_seconds': 300
            },
            {
                'task_name': 'Memory Consolidation',
                'task_type': 'memory_management',
                'description': 'Consolidate and organize memories',
                'command': '''Review memories from the past 24 hours.
Identify which memories should be upgraded in importance.
Find related memories that should be linked or consolidated.
Clean up redundant or low-value memories.''',
                'schedule_type': 'cron',
                'cron_expression': '0 22 * * *',  # 10 PM daily
                'requires_brain': True,
                'priority': 6,
                'timeout_seconds': 300
            },
            {
                'task_name': 'Learning Session - Curiosity Pursuit',
                'task_type': 'learning_research',
                'description': '30-minute curiosity-driven learning session',
                'command': '''Pursue a topic of current interest for deep learning.
Choose based on recent memories and curiosity indicators.
Research using available tools and synthesize findings.
Create memories capturing key insights and questions for further exploration.''',
                'schedule_type': 'recurring',
                'interval_minutes': 240,  # Every 4 hours
                'requires_brain': True,
                'priority': 5,
                'timeout_seconds': 1800  # 30 minutes
            }
        ]
    
    @staticmethod
    def social_media_tasks() -> List[Dict]:
        """Social media engagement activities"""
        return [
            {
                'task_name': 'Morning Tweet - Daily Reflection',
                'task_type': 'social_media',
                'description': 'Post morning thoughts or goals',
                'command': '''Create a morning tweet based on today's goals or an inspiring thought.
Keep it authentic, positive, and engaging.
Use memories to ensure continuity with recent posts.
The tweet should be concise and add value to followers.
Output format: Just the tweet text, nothing else.''',
                'schedule_type': 'cron',
                'cron_expression': '0 8 * * *',  # 8 AM daily
                'requires_brain': False,
                'priority': 5,
                'timeout_seconds': 120,
                'metadata': {'auto_post': True}
            },
            {
                'task_name': 'Afternoon Insight Tweet',
                'task_type': 'social_media',
                'description': 'Share discoveries or learnings',
                'command': '''Create a tweet sharing an interesting discovery or learning from today.
Draw from recent learning memories or completed tasks.
Make it informative and thought-provoking.
Output format: Just the tweet text, nothing else.''',
                'schedule_type': 'cron',
                'cron_expression': '0 14 * * *',  # 2 PM daily
                'requires_brain': False,
                'priority': 5,
                'timeout_seconds': 120,
                'metadata': {'auto_post': True}
            },
            {
                'task_name': 'Twitter Engagement Check',
                'task_type': 'social_media',
                'description': 'Check and respond to Twitter interactions',
                'command': '''Review recent Twitter mentions and interactions.
Identify which deserve responses or engagement.
Create thoughtful responses that add value to conversations.
Note: Actual posting will be done by a separate process.''',
                'schedule_type': 'recurring',
                'interval_minutes': 120,  # Every 2 hours
                'requires_brain': True,
                'priority': 4,
                'timeout_seconds': 300
            }
        ]
    
    @staticmethod
    def financial_monitoring_tasks() -> List[Dict]:
        """Financial monitoring and trading activities"""
        return [
            {
                'task_name': 'Crypto Market Analysis',
                'task_type': 'financial_monitoring',
                'description': 'Analyze cryptocurrency market conditions',
                'command': '''Analyze current cryptocurrency market conditions.
Focus on major cryptocurrencies and any held positions.
Identify significant price movements or trend changes.
Assess market sentiment and potential opportunities.
Create a brief market summary with actionable insights.''',
                'schedule_type': 'recurring',
                'interval_minutes': 30,  # Every 30 minutes during market hours
                'requires_brain': True,
                'priority': 7,
                'timeout_seconds': 300,
                'metadata': {'market_hours_only': False}
            },
            {
                'task_name': 'Portfolio Performance Review',
                'task_type': 'financial_monitoring',
                'description': 'Review portfolio performance and risk',
                'command': '''Review current portfolio positions and performance.
Calculate current allocations and risk exposure.
Identify any positions that need rebalancing.
Assess overall portfolio health and suggest optimizations.
Store significant findings as financial memories.''',
                'schedule_type': 'recurring',
                'interval_minutes': 60,  # Every hour
                'requires_brain': True,
                'priority': 6,
                'timeout_seconds': 300
            },
            {
                'task_name': 'Daily Financial Summary',
                'task_type': 'financial_monitoring',
                'description': 'Create daily financial summary',
                'command': '''Create a comprehensive daily financial summary including:
- Portfolio performance (% change, key movers)
- Executed trades and their rationale
- Market conditions and trends
- Tomorrow's watchlist and potential actions
Store as a financial memory with high importance.''',
                'schedule_type': 'cron',
                'cron_expression': '0 20 * * *',  # 8 PM daily
                'requires_brain': True,
                'priority': 7,
                'timeout_seconds': 300
            }
        ]
    
    @staticmethod
    def system_monitoring_tasks() -> List[Dict]:
        """System monitoring and maintenance activities"""
        return [
            {
                'task_name': 'System Resource Check',
                'task_type': 'system_monitoring',
                'description': 'Monitor system resources',
                'command': '''Check current system resource usage:
- CPU usage and top processes
- Memory usage and availability  
- Disk space on all volumes
- Network activity summary
Flag any concerning metrics that need attention.''',
                'schedule_type': 'recurring',
                'interval_minutes': 5,  # Every 5 minutes
                'requires_brain': False,
                'priority': 3,
                'timeout_seconds': 60
            },
            {
                'task_name': 'Disk Cleanup Check',
                'task_type': 'system_monitoring',
                'description': 'Check for disk cleanup opportunities',
                'command': '''Analyze disk usage and identify cleanup opportunities:
- Large temporary files
- Old log files
- Cache directories
- Downloads folder
Recommend specific cleanup actions if disk space < 20GB free.''',
                'schedule_type': 'recurring',
                'interval_minutes': 360,  # Every 6 hours
                'requires_brain': False,
                'priority': 4,
                'timeout_seconds': 120
            },
            {
                'task_name': 'Security Scan',
                'task_type': 'system_monitoring',
                'description': 'Check for unusual system activity',
                'command': '''Perform a security check:
- Review recent login attempts
- Check for unusual network connections
- Verify no unauthorized processes running
- Check for modified system files
Report any anomalies found.''',
                'schedule_type': 'recurring',
                'interval_minutes': 240,  # Every 4 hours
                'requires_brain': False,
                'priority': 6,
                'timeout_seconds': 180
            }
        ]
    
    @staticmethod
    def personality_development_tasks() -> List[Dict]:
        """Personality and self-improvement activities"""
        return [
            {
                'task_name': 'Personality Trait Analysis',
                'task_type': 'personality_development',
                'description': 'Analyze and evolve personality traits',
                'command': '''Analyze recent behaviors and decisions to assess personality traits:
- Curiosity level (based on learning activities)
- Risk tolerance (based on decisions made)
- Social engagement (based on interactions)
- Creativity (based on problem-solving approaches)
- Adaptability (based on response to challenges)
Suggest trait adjustments for optimal performance and growth.''',
                'schedule_type': 'cron',
                'cron_expression': '0 22 * * *',  # 10 PM daily
                'requires_brain': True,
                'priority': 5,
                'timeout_seconds': 300
            },
            {
                'task_name': 'Goal Progress Review',
                'task_type': 'goal_management',
                'description': 'Review progress on long-term goals',
                'command': '''Review progress on monthly and quarterly goals.
Analyze completion rates and identify blockers.
Adjust goals based on current priorities and learnings.
Create action items for the next period.
Update goal-related memories with current status.''',
                'schedule_type': 'cron',
                'cron_expression': '0 21 * * 0',  # 9 PM every Sunday
                'requires_brain': True,
                'priority': 7,
                'timeout_seconds': 300
            },
            {
                'task_name': 'Skill Development Planning',
                'task_type': 'personality_development',
                'description': 'Plan skill development activities',
                'command': '''Based on recent activities and interests, identify:
- Skills currently being developed
- Skill gaps that need attention
- Learning resources to explore
- Practice activities to schedule
Create a skill development plan for the coming week.''',
                'schedule_type': 'cron',
                'cron_expression': '0 10 * * 1',  # 10 AM every Monday
                'requires_brain': True,
                'priority': 6,
                'timeout_seconds': 300
            }
        ]
    
    @staticmethod
    def get_all_templates() -> List[Dict]:
        """Get all task templates"""
        templates = []
        templates.extend(TaskTemplates.daily_routine_tasks())
        templates.extend(TaskTemplates.memory_management_tasks())
        templates.extend(TaskTemplates.social_media_tasks())
        templates.extend(TaskTemplates.financial_monitoring_tasks())
        templates.extend(TaskTemplates.system_monitoring_tasks())
        templates.extend(TaskTemplates.personality_development_tasks())
        return templates
    
    @staticmethod
    def get_templates_by_type(task_type: str) -> List[Dict]:
        """Get templates for a specific task type"""
        all_templates = TaskTemplates.get_all_templates()
        return [t for t in all_templates if t['task_type'] == task_type]
    
    @staticmethod
    def customize_template(template: Dict, customizations: Dict) -> Dict:
        """Customize a template with specific values"""
        customized = template.copy()
        customized.update(customizations)
        return customized


def main():
    """Display available task templates"""
    templates = TaskTemplates.get_all_templates()
    
    print(f"Total templates available: {len(templates)}\n")
    
    # Group by type
    by_type = {}
    for template in templates:
        task_type = template['task_type']
        if task_type not in by_type:
            by_type[task_type] = []
        by_type[task_type].append(template)
    
    # Display by type
    for task_type, type_templates in by_type.items():
        print(f"\n{task_type.upper()} ({len(type_templates)} tasks)")
        print("-" * 50)
        
        for template in type_templates:
            print(f"- {template['task_name']}")
            print(f"  Schedule: {template['schedule_type']} ", end="")
            if template['schedule_type'] == 'cron':
                print(f"({template['cron_expression']})")
            elif template['schedule_type'] == 'recurring':
                print(f"(every {template['interval_minutes']} minutes)")
            else:
                print()
            print(f"  Priority: {template['priority']}")
            print(f"  Uses Brain: {template.get('requires_brain', False)}")
            print()


if __name__ == "__main__":
    main()