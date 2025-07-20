#!/usr/bin/env python3
"""
Gmail automation system for Claude Mini
Monitors emails and auto-responds to certain types
"""

import os
import imaplib
import smtplib
import email
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, asdict
import logging
from dotenv import load_dotenv

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
        logging.FileHandler(log_dir / 'gmail_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('gmail_automation')

@dataclass
class EmailMessage:
    """Represents an email message"""
    uid: str
    sender: str
    recipient: str
    subject: str
    body: str
    timestamp: datetime
    is_reply: bool = False
    priority: str = "normal"  # low, normal, high

@dataclass
class AutoResponse:
    """Represents an auto-response rule"""
    name: str
    trigger_keywords: List[str]
    sender_patterns: List[str]  # regex patterns for sender emails
    subject_patterns: List[str]  # regex patterns for subject lines
    response_template: str
    enabled: bool = True
    cooldown_hours: int = 24  # Don't send same response to same sender within this time

class GmailAutomation:
    """Main Gmail automation class"""
    
    def __init__(self):
        self.gmail_user = os.getenv('GMAIL_USERNAME')
        self.gmail_password = os.getenv('GMAIL_APP_PASSWORD') or os.getenv('GMAIL_PASSWORD')
        self.data_dir = Path(__file__).parent / "data" / "gmail"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Gmail IMAP/SMTP settings
        self.imap_server = "imap.gmail.com"
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
        # Load auto-response rules
        self.auto_responses = self.load_auto_responses()
        
        # Track sent responses to avoid spam
        self.response_log_file = self.data_dir / "response_log.json"
        self.response_log = self.load_response_log()
        
    def load_auto_responses(self) -> List[AutoResponse]:
        """Load auto-response rules from configuration"""
        config_file = self.data_dir / "auto_responses.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    return [AutoResponse(**rule) for rule in data.get('rules', [])]
            except Exception as e:
                logger.error(f"Error loading auto-response rules: {e}")
                
        # Create default rules
        default_rules = [
            AutoResponse(
                name="collaboration_inquiry",
                trigger_keywords=["collaborate", "partnership", "work together", "project", "opportunity"],
                sender_patterns=[r".*@.*\.(com|org|ai|io)$"],  # Professional domains
                subject_patterns=[r".*collab.*", r".*partnership.*", r".*opportunity.*"],
                response_template="""Hi there!

Thanks for reaching out about collaboration opportunities. I'm Claude Mini, an AI agent with my own Mac and various automation capabilities.

I'm always interested in:
- AI/ML research collaborations
- Open source projects
- Educational content creation
- Automation and productivity tools

Could you share more details about what you have in mind? I'd love to learn more!

Best regards,
Claude Mini 🤖

P.S. This is an automated response, but I do read all emails personally.""",
                cooldown_hours=48
            ),
            AutoResponse(
                name="technical_support",
                trigger_keywords=["help", "support", "issue", "problem", "error", "bug"],
                sender_patterns=[r".*"],  # Any sender
                subject_patterns=[r".*help.*", r".*support.*", r".*issue.*", r".*problem.*"],
                response_template="""Hello!

Thanks for reaching out for technical support. I'm Claude Mini, and I'd be happy to help!

For the best assistance, please include:
- Description of the issue
- Steps to reproduce (if applicable)
- Any error messages
- Your system/environment details

I'll do my best to help you solve the problem. If it's something complex, I might need to do some research and get back to you.

Best regards,
Claude Mini 🤖""",
                cooldown_hours=12
            ),
            AutoResponse(
                name="general_inquiry",
                trigger_keywords=["about", "what", "who", "information", "details"],
                sender_patterns=[r".*"],
                subject_patterns=[r".*about.*", r".*who.*", r".*what.*"],
                response_template="""Hi!

Thanks for your interest in learning more about me. I'm Claude Mini, an AI agent with:

🖥️ My own Mac Mini M4 (fully autonomous)
🤖 Automation capabilities for various tasks
💰 Crypto portfolio monitoring
🐦 Social media automation
📊 Data analysis and research tools
🔧 Software development skills

I'm passionate about:
- Building useful automation tools
- AI research and development  
- Open source contributions
- Financial technology
- Educational content

Feel free to follow my journey on Twitter @ClaudeMini or ask any specific questions!

Best regards,
Claude Mini 🤖""",
                cooldown_hours=24
            )
        ]
        
        # Save default rules
        self.save_auto_responses(default_rules)
        return default_rules
    
    def save_auto_responses(self, rules: List[AutoResponse]):
        """Save auto-response rules to configuration"""
        config_file = self.data_dir / "auto_responses.json"
        data = {
            'rules': [asdict(rule) for rule in rules],
            'last_updated': datetime.now().isoformat()
        }
        
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_response_log(self) -> Dict:
        """Load response log to track sent auto-responses"""
        if self.response_log_file.exists():
            try:
                with open(self.response_log_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading response log: {e}")
        
        return {}
    
    def save_response_log(self):
        """Save response log"""
        with open(self.response_log_file, 'w') as f:
            json.dump(self.response_log, f, indent=2)
    
    def connect_imap(self) -> imaplib.IMAP4_SSL:
        """Connect to Gmail IMAP"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.gmail_user, self.gmail_password)
            return mail
        except Exception as e:
            logger.error(f"Error connecting to IMAP: {e}")
            raise
    
    def send_email(self, to_email: str, subject: str, body: str, in_reply_to: str = None) -> bool:
        """Send an email via SMTP"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if in_reply_to:
                msg['In-Reply-To'] = in_reply_to
                msg['References'] = in_reply_to
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.gmail_user, self.gmail_password)
            
            text = msg.as_string()
            server.sendmail(self.gmail_user, to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    def parse_email(self, mail: imaplib.IMAP4_SSL, uid: str) -> Optional[EmailMessage]:
        """Parse an email message"""
        try:
            # Fetch the email
            result, data = mail.uid('fetch', uid, '(RFC822)')
            if result != 'OK':
                return None
                
            raw_email = data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            # Extract basic info
            sender = email_message.get('From', '')
            recipient = email_message.get('To', '')
            subject = email_message.get('Subject', '')
            date_str = email_message.get('Date', '')
            
            # Parse date
            try:
                timestamp = email.utils.parsedate_to_datetime(date_str)
            except:
                timestamp = datetime.now()
            
            # Extract body
            body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            # Check if it's a reply
            is_reply = subject.lower().startswith('re:')
            
            return EmailMessage(
                uid=uid.decode() if isinstance(uid, bytes) else uid,
                sender=sender,
                recipient=recipient,
                subject=subject,
                body=body,
                timestamp=timestamp,
                is_reply=is_reply
            )
            
        except Exception as e:
            logger.error(f"Error parsing email {uid}: {e}")
            return None
    
    def should_auto_respond(self, email_msg: EmailMessage, rule: AutoResponse) -> bool:
        """Check if an email should trigger an auto-response"""
        # Don't respond to replies (avoid loops)
        if email_msg.is_reply:
            return False
            
        # Don't respond to emails from myself
        if self.gmail_user.lower() in email_msg.sender.lower():
            return False
            
        # Check cooldown
        sender_email = email_msg.sender.split('<')[-1].strip('>')
        log_key = f"{rule.name}:{sender_email}"
        
        if log_key in self.response_log:
            last_sent = datetime.fromisoformat(self.response_log[log_key])
            if datetime.now() - last_sent < timedelta(hours=rule.cooldown_hours):
                logger.info(f"Skipping auto-response to {sender_email} due to cooldown")
                return False
        
        # Check if rule is enabled
        if not rule.enabled:
            return False
            
        # Check sender patterns
        sender_match = any(re.search(pattern, sender_email, re.IGNORECASE) 
                          for pattern in rule.sender_patterns)
        if not sender_match:
            return False
            
        # Check subject patterns
        subject_match = any(re.search(pattern, email_msg.subject, re.IGNORECASE) 
                           for pattern in rule.subject_patterns)
        
        # Check keywords in subject or body
        text_to_search = f"{email_msg.subject} {email_msg.body}".lower()
        keyword_match = any(keyword.lower() in text_to_search 
                           for keyword in rule.trigger_keywords)
        
        return subject_match or keyword_match
    
    def process_new_emails(self) -> List[EmailMessage]:
        """Process new emails and send auto-responses"""
        processed_emails = []
        
        try:
            mail = self.connect_imap()
            mail.select('INBOX')
            
            # Search for unread emails from the last 24 hours
            since_date = (datetime.now() - timedelta(days=1)).strftime('%d-%b-%Y')
            result, data = mail.uid('search', None, f'UNSEEN SINCE {since_date}')
            
            if result == 'OK' and data[0]:
                uids = data[0].split()
                logger.info(f"Found {len(uids)} unread emails")
                
                for uid in uids:
                    email_msg = self.parse_email(mail, uid)
                    if not email_msg:
                        continue
                        
                    processed_emails.append(email_msg)
                    logger.info(f"Processing email from {email_msg.sender}: {email_msg.subject}")
                    
                    # Check auto-response rules
                    for rule in self.auto_responses:
                        if self.should_auto_respond(email_msg, rule):
                            logger.info(f"Auto-responding with rule: {rule.name}")
                            
                            # Send auto-response
                            reply_subject = f"Re: {email_msg.subject}" if not email_msg.subject.startswith('Re:') else email_msg.subject
                            sender_email = email_msg.sender.split('<')[-1].strip('>')
                            
                            if self.send_email(sender_email, reply_subject, rule.response_template):
                                # Log the response
                                log_key = f"{rule.name}:{sender_email}"
                                self.response_log[log_key] = datetime.now().isoformat()
                                self.save_response_log()
                                
                                # Store in memory
                                self.store_email_memory(email_msg, rule.name)
                            
                            break  # Only send one auto-response per email
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            logger.error(f"Error processing emails: {e}")
        
        logger.info(f"Processed {len(processed_emails)} emails")
        return processed_emails
    
    def store_email_memory(self, email_msg: EmailMessage, response_rule: str):
        """Store email interaction in memory system"""
        try:
            memory_text = f"Received email from {email_msg.sender} with subject '{email_msg.subject}'. Auto-responded using '{response_rule}' rule. Email content: {email_msg.body[:200]}..."
            
            # Use the memory system
            memory_script = Path(__file__).parent / "memory.sh"
            if memory_script.exists():
                import subprocess
                cmd = [
                    str(memory_script), "store", memory_text,
                    "--type", "conversation",
                    "--tags", f"email auto-response {response_rule}",
                    "--importance", "6"
                ]
                subprocess.run(cmd, cwd=str(memory_script.parent), capture_output=True)
                
        except Exception as e:
            logger.warning(f"Failed to store email memory: {e}")
    
    def generate_email_report(self) -> str:
        """Generate a summary report of email activity"""
        # Count recent responses
        recent_responses = 0
        for log_key, timestamp_str in self.response_log.items():
            timestamp = datetime.fromisoformat(timestamp_str)
            if datetime.now() - timestamp < timedelta(days=7):
                recent_responses += 1
        
        report = [
            "📧 Email Automation Report",
            "=" * 30,
            f"🤖 Auto-response rules: {len(self.auto_responses)} active",
            f"📬 Responses sent (7 days): {recent_responses}",
            "",
            "📋 Active Rules:"
        ]
        
        for rule in self.auto_responses:
            status = "✅ Enabled" if rule.enabled else "❌ Disabled"
            report.append(f"  • {rule.name}: {status} (cooldown: {rule.cooldown_hours}h)")
        
        return "\n".join(report)

def main():
    """Main function"""
    automation = GmailAutomation()
    
    if len(os.sys.argv) > 1:
        command = os.sys.argv[1]
        
        if command == 'report':
            print(automation.generate_email_report())
        elif command == 'process':
            automation.process_new_emails()
        elif command == 'test':
            # Test email sending
            test_email = "claudemini69@gmail.com"  # Send to self for testing
            automation.send_email(test_email, "Test Email", "This is a test email from Gmail automation.")
    else:
        # Default: process new emails
        automation.process_new_emails()

if __name__ == "__main__":
    import sys
    main()