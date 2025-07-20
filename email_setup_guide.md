# Gmail Automation Setup Guide

## Required Setup Steps

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password** for Gmail automation:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail" application
   - Update `.env` file with app password

3. **Enable IMAP** in Gmail:
   - Gmail Settings → Forwarding and POP/IMAP
   - Enable IMAP access

## Environment Variables

Update `/Users/claudemini/Claude/.env`:

```
GMAIL_USERNAME=claudemini69@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # 16-character app password
```

## Testing

```bash
# Test email sending
uv run python gmail_automation.py test

# Process new emails
uv run python gmail_automation.py process

# Generate report
uv run python gmail_automation.py report
```

## Auto-Response Rules

The system includes 3 default rules:
1. **Collaboration Inquiry** - Responds to partnership/collaboration emails
2. **Technical Support** - Responds to help/support requests  
3. **General Inquiry** - Responds to "about me" type questions

Each rule has a cooldown period to prevent spam.