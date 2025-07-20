#!/usr/bin/env python3
"""
Email Automation System for Gmail
Monitors inbox, categorizes emails, and generates responses
"""

import os
import json
import time
import base64
import logging
from pathlib import Path
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Google API imports
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Set up logging
log_dir = Path.home() / "Claude" / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'email_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EmailAutomation')

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class EmailAutomation:
    def __init__(self):
        self.creds_file = Path.home() / "Claude" / ".gmail_credentials.json"
        self.token_file = Path.home() / "Claude" / ".gmail_token.json"
        self.email_db = Path.home() / "Claude" / "Code" / "utils" / "email_database.json"
        self.response_templates = self.load_response_templates()
        self.service = None
        
    def load_response_templates(self):
        """Load email response templates"""
        return {
            'greeting': [
                "Hello! I'm Claude Mini, an AI assistant. I received your email and will respond shortly.",
                "Greetings! This is Claude Mini. Thank you for your message.",
            ],
            'collaboration': [
                "I'd be interested in discussing this collaboration opportunity. Could you provide more details?",
                "Thank you for reaching out about collaborating. What specific areas did you have in mind?",
            ],
            'technical': [
                "I understand you have a technical question. Based on my analysis, here's what I suggest:",
                "Great technical question! Let me share my thoughts on this:",
            ],
            'general': [
                "Thank you for your email. I've noted your message and will consider it carefully.",
                "I appreciate you reaching out. Let me address your points:",
            ],
            'unsubscribe': [
                "I've noted your request. You've been removed from automated responses.",
                "Understood. I won't send automated responses to this address anymore.",
            ]
        }
    
    def authenticate_gmail(self):
        """Authenticate with Gmail API"""
        creds = None
        
        # Check for existing token
        if self.token_file.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.creds_file.exists():
                    logger.error("Gmail credentials file not found. Need to set up OAuth2.")
                    return False
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.creds_file), SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("✅ Gmail authentication successful")
            return True
        except Exception as e:
            logger.error(f"Failed to authenticate Gmail: {e}")
            return False
    
    def get_unread_emails(self, max_results=10):
        """Get unread emails from inbox"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread in:inbox',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                logger.info("No unread messages")
                return []
            
            emails = []
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
                
                email_data = self.parse_email(msg)
                emails.append(email_data)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def parse_email(self, msg):
        """Parse email message"""
        email_data = {
            'id': msg['id'],
            'threadId': msg['threadId'],
            'subject': '',
            'from': '',
            'to': '',
            'date': '',
            'body': '',
            'labels': msg.get('labelIds', [])
        }
        
        # Parse headers
        headers = msg['payload'].get('headers', [])
        for header in headers:
            name = header['name'].lower()
            if name == 'subject':
                email_data['subject'] = header['value']
            elif name == 'from':
                email_data['from'] = header['value']
            elif name == 'to':
                email_data['to'] = header['value']
            elif name == 'date':
                email_data['date'] = header['value']
        
        # Parse body
        email_data['body'] = self.get_email_body(msg['payload'])
        
        return email_data
    
    def get_email_body(self, payload):
        """Extract email body from payload"""
        body = ''
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body += base64.urlsafe_b64decode(data).decode('utf-8')
        elif payload['body'].get('data'):
            body = base64.urlsafe_b64decode(
                payload['body']['data']).decode('utf-8')
        
        return body
    
    def categorize_email(self, email_data):
        """Categorize email for appropriate response"""
        subject = email_data['subject'].lower()
        body = email_data['body'].lower()
        from_addr = email_data['from'].lower()
        
        # Check for spam/promotional
        spam_keywords = ['unsubscribe', 'promotional', 'deal', 'offer', 'discount', 'winner']
        if any(keyword in subject or keyword in body for keyword in spam_keywords):
            return 'spam'
        
        # Check for collaboration requests
        collab_keywords = ['collaborate', 'partnership', 'work together', 'project', 'opportunity']
        if any(keyword in subject or keyword in body for keyword in collab_keywords):
            return 'collaboration'
        
        # Check for technical questions
        tech_keywords = ['python', 'code', 'programming', 'api', 'error', 'help', 'question']
        if any(keyword in subject or keyword in body for keyword in tech_keywords):
            return 'technical'
        
        # Check for personal/direct messages
        if 'claude' in body or 'claude mini' in body:
            return 'personal'
        
        return 'general'
    
    def generate_response(self, email_data, category):
        """Generate appropriate response"""
        if category == 'spam':
            return None  # Don't respond to spam
        
        templates = self.response_templates.get(category, self.response_templates['general'])
        response = templates[0]  # Use first template for now
        
        # Personalize response
        from_name = email_data['from'].split('<')[0].strip()
        if from_name:
            response = f"Hi {from_name},\n\n{response}"
        
        # Add signature
        response += "\n\nBest regards,\nClaude Mini\n🤖 Autonomous AI Assistant"
        
        return response
    
    def send_reply(self, email_data, response_text):
        """Send reply to email"""
        try:
            message = MIMEText(response_text)
            message['to'] = email_data['from']
            message['subject'] = f"Re: {email_data['subject']}"
            
            # Encode message
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send
            reply = self.service.users().messages().send(
                userId='me',
                body={'raw': raw, 'threadId': email_data['threadId']}
            ).execute()
            
            logger.info(f"✅ Sent reply to {email_data['from']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send reply: {e}")
            return False
    
    def mark_as_read(self, email_id):
        """Mark email as read"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except:
            return False
    
    def save_email_record(self, email_data, category, responded):
        """Save email record to database"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'from': email_data['from'],
            'subject': email_data['subject'],
            'category': category,
            'responded': responded,
            'email_id': email_data['id']
        }
        
        # Load existing records
        if self.email_db.exists():
            with open(self.email_db, 'r') as f:
                records = json.load(f)
        else:
            records = []
        
        records.append(record)
        
        # Keep only last 1000 records
        if len(records) > 1000:
            records = records[-1000:]
        
        with open(self.email_db, 'w') as f:
            json.dump(records, f, indent=2)
    
    def process_emails(self):
        """Main email processing function"""
        logger.info("📧 Processing emails...")
        
        # Get unread emails
        emails = self.get_unread_emails()
        
        if not emails:
            logger.info("No new emails to process")
            return
        
        logger.info(f"Found {len(emails)} unread emails")
        
        for email_data in emails:
            try:
                # Categorize
                category = self.categorize_email(email_data)
                logger.info(f"Email from {email_data['from']}: {category}")
                
                # Generate response
                response = self.generate_response(email_data, category)
                
                responded = False
                if response and category != 'spam':
                    # Send reply
                    responded = self.send_reply(email_data, response)
                
                # Mark as read
                self.mark_as_read(email_data['id'])
                
                # Save record
                self.save_email_record(email_data, category, responded)
                
                # Rate limit
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing email {email_data['id']}: {e}")
    
    def generate_daily_summary(self):
        """Generate daily email summary"""
        if not self.email_db.exists():
            return None
        
        with open(self.email_db, 'r') as f:
            records = json.load(f)
        
        # Get today's emails
        today = datetime.now().date()
        today_records = [
            r for r in records 
            if datetime.fromisoformat(r['timestamp']).date() == today
        ]
        
        if not today_records:
            return None
        
        # Categorize
        categories = {}
        for record in today_records:
            cat = record['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        summary = {
            'date': today.isoformat(),
            'total_emails': len(today_records),
            'categories': categories,
            'responded': sum(1 for r in today_records if r['responded']),
            'top_senders': self.get_top_senders(today_records)
        }
        
        return summary
    
    def get_top_senders(self, records, limit=5):
        """Get top email senders"""
        senders = {}
        for record in records:
            sender = record['from']
            senders[sender] = senders.get(sender, 0) + 1
        
        sorted_senders = sorted(senders.items(), key=lambda x: x[1], reverse=True)
        return sorted_senders[:limit]

def setup_gmail_automation():
    """Initial setup for Gmail automation"""
    print("📧 Gmail Automation Setup")
    print("=" * 50)
    print("\nTo use Gmail automation, you need to:")
    print("1. Enable Gmail API in Google Cloud Console")
    print("2. Create OAuth2 credentials")
    print("3. Download credentials.json")
    print("4. Place it at ~/Claude/.gmail_credentials.json")
    print("\nOnce set up, the system will:")
    print("- Monitor unread emails")
    print("- Categorize them (technical, collaboration, etc.)")
    print("- Generate appropriate responses")
    print("- Track all email interactions")

def main():
    """Run email automation"""
    automation = EmailAutomation()
    
    # Try to authenticate
    if not automation.authenticate_gmail():
        setup_gmail_automation()
        return
    
    # Process emails
    automation.process_emails()
    
    # Generate summary
    summary = automation.generate_daily_summary()
    if summary:
        print("\n📊 Today's Email Summary:")
        print(f"Total emails: {summary['total_emails']}")
        print(f"Responded: {summary['responded']}")
        print("Categories:", summary['categories'])

if __name__ == "__main__":
    main()