#!/usr/bin/env python3

"""
Response Parser for Claude Brain
Cleans and extracts Claude's responses from tmux log files
"""

import re
import os
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import json

class ResponseParser:
    def __init__(self):
        # ANSI escape sequence patterns
        self.ansi_pattern = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
        self.cursor_pattern = re.compile(r'\x1b\[[0-9]*[ABCDEFGJKST]')
        self.clear_pattern = re.compile(r'\x1b\[[0-9]*[JK]')
        
        # Tmux specific patterns
        self.tmux_timestamp_pattern = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\s*')
        
        # Claude response patterns
        self.claude_start_patterns = [
            r'^\[Claude\]',
            r'^Claude:',
            r'^Assistant:',
            r'^claude>',
        ]
        
        # Shell prompt patterns
        self.prompt_patterns = [
            r'^\$\s*$',
            r'^[^@]+@[^:]+:[^$]+\$\s*$',  # user@host:path$
            r'^>\s*$',
            r'^%\s*$',
        ]
        
    def strip_ansi_codes(self, text: str) -> str:
        """Remove all ANSI escape sequences from text"""
        # Remove ANSI color codes
        text = self.ansi_pattern.sub('', text)
        # Remove cursor movement codes
        text = self.cursor_pattern.sub('', text)
        # Remove clear codes
        text = self.clear_pattern.sub('', text)
        # Remove other escape sequences
        text = re.sub(r'\x1b\]0;[^\x07]*\x07', '', text)  # Terminal title
        text = re.sub(r'\x1b[>=\?]?[0-9;]*[a-zA-Z]', '', text)  # Other sequences
        return text
    
    def remove_tmux_artifacts(self, lines: List[str]) -> List[str]:
        """Remove tmux-specific artifacts from log lines"""
        cleaned_lines = []
        for line in lines:
            # Remove tmux timestamps
            line = self.tmux_timestamp_pattern.sub('', line)
            # Skip empty lines resulting from removal
            if line.strip():
                cleaned_lines.append(line)
        return cleaned_lines
    
    def is_prompt_line(self, line: str) -> bool:
        """Check if a line is a shell prompt"""
        stripped = line.strip()
        for pattern in self.prompt_patterns:
            if re.match(pattern, stripped):
                return True
        return False
    
    def is_claude_start(self, line: str) -> bool:
        """Check if a line marks the start of Claude's response"""
        for pattern in self.claude_start_patterns:
            if re.match(pattern, line.strip()):
                return True
        return False
    
    def extract_command(self, lines: List[str], start_index: int = 0) -> Tuple[Optional[str], int]:
        """Extract the command that was sent to Claude"""
        for i in range(start_index, len(lines)):
            line = lines[i].strip()
            # Look for command after a prompt
            if i > 0 and self.is_prompt_line(lines[i-1]):
                if line and not self.is_prompt_line(line):
                    return line, i
        return None, start_index
    
    def extract_response(self, lines: List[str], start_index: int = 0) -> Tuple[Optional[str], int]:
        """Extract Claude's response from log lines"""
        response_lines = []
        in_response = False
        end_index = start_index
        
        for i in range(start_index, len(lines)):
            line = lines[i]
            stripped = line.strip()
            
            # Start collecting when we find Claude's response marker
            if not in_response and self.is_claude_start(line):
                in_response = True
                # Sometimes the response starts on the same line
                content = re.sub(r'^\[Claude\]|^Claude:|^Assistant:|^claude>', '', line).strip()
                if content:
                    response_lines.append(content)
                continue
            
            # Stop collecting when we hit a new prompt
            if in_response and self.is_prompt_line(line):
                end_index = i
                break
            
            # Collect response lines
            if in_response and stripped:
                response_lines.append(line.rstrip())
        
        if response_lines:
            return '\n'.join(response_lines), end_index
        return None, start_index
    
    def parse_log_file(self, log_path: str, last_n_lines: Optional[int] = None) -> List[Dict]:
        """Parse a tmux log file and extract command-response pairs"""
        if not os.path.exists(log_path):
            return []
        
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Clean lines
        lines = [self.strip_ansi_codes(line) for line in lines]
        lines = self.remove_tmux_artifacts(lines)
        
        # If requested, only process last N lines
        if last_n_lines:
            lines = lines[-last_n_lines:]
        
        interactions = []
        i = 0
        
        while i < len(lines):
            # Try to find a command
            command, cmd_index = self.extract_command(lines, i)
            if command:
                # Try to find the response
                response, resp_index = self.extract_response(lines, cmd_index + 1)
                if response:
                    interactions.append({
                        'command': command,
                        'response': response,
                        'line_start': i,
                        'line_end': resp_index
                    })
                    i = resp_index + 1
                else:
                    i = cmd_index + 1
            else:
                i += 1
        
        return interactions
    
    def get_latest_response(self, log_path: str) -> Optional[str]:
        """Get the most recent response from a log file"""
        interactions = self.parse_log_file(log_path, last_n_lines=100)
        if interactions:
            return interactions[-1]['response']
        return None
    
    def extract_json_from_response(self, response: str) -> Optional[Dict]:
        """Extract JSON object from Claude's response if present"""
        # Look for JSON blocks
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find raw JSON
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    pass
        
        return None
    
    def extract_code_blocks(self, response: str) -> List[Dict[str, str]]:
        """Extract code blocks from Claude's response"""
        code_blocks = []
        
        # Pattern for code blocks with language
        pattern = r'```(\w+)?\s*(.*?)\s*```'
        matches = re.finditer(pattern, response, re.DOTALL)
        
        for match in matches:
            language = match.group(1) or 'text'
            code = match.group(2).strip()
            code_blocks.append({
                'language': language,
                'code': code
            })
        
        return code_blocks
    
    def clean_response(self, response: str) -> str:
        """Clean up a response for storage or display"""
        # Remove any remaining ANSI codes
        response = self.strip_ansi_codes(response)
        
        # Remove excessive whitespace
        lines = response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove trailing whitespace
            line = line.rstrip()
            # Skip multiple consecutive empty lines
            if line or (cleaned_lines and cleaned_lines[-1]):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()


def main():
    """Test the parser with a sample log file"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python response_parser.py <log_file_path> [last_n_lines]")
        return
    
    log_path = sys.argv[1]
    last_n_lines = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    parser = ResponseParser()
    
    # Parse the log file
    interactions = parser.parse_log_file(log_path, last_n_lines)
    
    print(f"Found {len(interactions)} interactions\n")
    
    for i, interaction in enumerate(interactions, 1):
        print(f"=== Interaction {i} ===")
        print(f"Command: {interaction['command']}")
        print(f"Response:\n{interaction['response']}")
        print()
    
    # Test getting latest response
    latest = parser.get_latest_response(log_path)
    if latest:
        print("\n=== Latest Response ===")
        print(latest)


if __name__ == "__main__":
    main()