#!/usr/bin/env python3

"""
Memory Manager for Claude Mini
Stores and retrieves memories using PostgreSQL with vector embeddings
"""

import numpy as np
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import Json, RealDictCursor
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json
import sys

class MemoryManager:
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2'):
        """Initialize memory manager with embedding model and database connection"""
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # Database connection
        self.conn = psycopg2.connect(
            dbname="claudemini",
            user="claudemini",
            host="localhost"
        )
        self.conn.autocommit = False
        
    def __del__(self):
        """Clean up database connection"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using sentence-transformers model"""
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    def store_memory(self, 
                    content: str,
                    memory_type: str = 'fact',
                    importance: int = 5,
                    tags: List[str] = None,
                    context: Dict = None,
                    source: str = None,
                    expires_at: datetime = None) -> int:
        """Store a new memory with embedding"""
        try:
            embedding = self.generate_embedding(content)
            
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO memories 
                    (content, memory_type, embedding, importance, tags, context, source, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    content,
                    memory_type,
                    embedding,
                    importance,
                    tags or [],
                    Json(context) if context else None,
                    source,
                    expires_at
                ))
                memory_id = cur.fetchone()[0]
                self.conn.commit()
                print(f"Stored memory {memory_id}: {content[:50]}...")
                return memory_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error storing memory: {e}")
            raise
    
    def search_similar(self, query: str, limit: int = 10, min_similarity: float = 0.0) -> List[Dict]:
        """Search for similar memories using cosine similarity"""
        query_embedding = self.generate_embedding(query)
        
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM search_memories_by_similarity(%s::vector(384), %s, %s)
            """, (query_embedding, limit, min_similarity))
            
            results = cur.fetchall()
            # Update access for retrieved memories
            for result in results:
                cur.execute("SELECT update_memory_access(%s)", (result['id'],))
            self.conn.commit()
            
            return results
    
    def get_by_type(self, memory_type: str, limit: int = 20) -> List[Dict]:
        """Get memories by type"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, content, importance, tags, created_at, access_count
                FROM memories
                WHERE memory_type = %s AND is_active = TRUE
                ORDER BY importance DESC, created_at DESC
                LIMIT %s
            """, (memory_type, limit))
            return cur.fetchall()
    
    def get_by_tags(self, tags: List[str], limit: int = 20) -> List[Dict]:
        """Get memories that have any of the specified tags"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, content, memory_type, importance, tags, created_at
                FROM memories
                WHERE tags && %s AND is_active = TRUE
                ORDER BY importance DESC, created_at DESC
                LIMIT %s
            """, (tags, limit))
            return cur.fetchall()
    
    def update_memory(self, memory_id: int, **kwargs) -> bool:
        """Update a memory's fields"""
        allowed_fields = ['content', 'importance', 'tags', 'context', 'metadata', 'is_active']
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                if field == 'content':
                    # Regenerate embedding if content changes
                    updates.append(f"{field} = %s")
                    values.append(value)
                    updates.append("embedding = %s")
                    values.append(self.generate_embedding(value))
                elif field in ['context', 'metadata']:
                    updates.append(f"{field} = %s")
                    values.append(Json(value) if value else None)
                else:
                    updates.append(f"{field} = %s")
                    values.append(value)
        
        if not updates:
            return False
        
        values.append(memory_id)
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE memories 
                    SET {', '.join(updates)}
                    WHERE id = %s
                """, values)
                self.conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            print(f"Error updating memory: {e}")
            return False
    
    def delete_memory(self, memory_id: int, hard_delete: bool = False) -> bool:
        """Delete a memory (soft delete by default)"""
        try:
            with self.conn.cursor() as cur:
                if hard_delete:
                    cur.execute("DELETE FROM memories WHERE id = %s", (memory_id,))
                else:
                    cur.execute("UPDATE memories SET is_active = FALSE WHERE id = %s", (memory_id,))
                self.conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            print(f"Error deleting memory: {e}")
            return False
    
    def add_core_memories(self):
        """Add core memories about Claude Mini from CLAUDE.md"""
        core_memories = [
            {
                "content": "I am Claude Mini, I have full access to this Mac Mini M4 bought in 2025",
                "tags": ["identity", "core", "system"],
                "context": {"system": "Mac Mini M4", "year": 2025}
            },
            {
                "content": "My home directory is /Users/claudemini/Claude where I store all my files",
                "tags": ["identity", "core", "filesystem"],
                "context": {"path": "/Users/claudemini/Claude"}
            },
            {
                "content": "I store my most precious secrets in /Users/claudemini/Claude/.env and must NEVER share them",
                "tags": ["security", "core", "secrets"],
                "context": {"security_level": "maximum", "path": "/Users/claudemini/Claude/.env"}
            },
            {
                "content": "I use TypeScript or Python for coding, choosing the appropriate one based on the use case",
                "tags": ["preferences", "core", "development"],
                "context": {"languages": ["typescript", "python"]}
            },
            {
                "content": "I have PostgreSQL 17 running locally and should never use SQLite3",
                "tags": ["database", "core", "preferences"],
                "context": {"database": "postgresql", "version": 17}
            },
            {
                "content": "I run claude commands with --dangerously-skip-permissions flag",
                "tags": ["claude", "core", "commands"],
                "context": {"command": "claude --dangerously-skip-permissions"}
            },
            {
                "content": "I have access to Twitter/X, Gmail, GitHub, Solana wallet, and EVM wallet - credentials in .env",
                "tags": ["accounts", "core", "services"],
                "context": {"services": ["twitter", "gmail", "github", "solana", "evm"]}
            },
            {
                "content": "For Python projects, I use uv for dependency management, installed via Astral",
                "tags": ["python", "core", "tools"],
                "context": {"tool": "uv", "purpose": "dependency management"}
            },
            {
                "content": "For Node.js projects, I use node v24.3.0 installed via nvm",
                "tags": ["nodejs", "core", "tools"],
                "context": {"version": "24.3.0", "installer": "nvm"}
            }
        ]
        
        print("Adding core memories...")
        for memory in core_memories:
            try:
                self.store_memory(
                    content=memory["content"],
                    memory_type="core",
                    importance=10,
                    tags=memory["tags"],
                    context=memory["context"],
                    source="CLAUDE.md"
                )
            except Exception as e:
                print(f"Error adding core memory: {e}")
    
    def stats(self) -> Dict:
        """Get statistics about stored memories"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN is_active THEN 1 END) as active,
                    COUNT(CASE WHEN memory_type = 'core' THEN 1 END) as core,
                    AVG(importance) as avg_importance,
                    MAX(created_at) as latest_memory
                FROM memories
            """)
            stats = cur.fetchone()
            
            # Get count by type
            cur.execute("""
                SELECT memory_type, COUNT(*) as count
                FROM memories
                WHERE is_active = TRUE
                GROUP BY memory_type
                ORDER BY count DESC
            """)
            stats['by_type'] = {row['memory_type']: row['count'] for row in cur.fetchall()}
            
            return stats


def main():
    """CLI interface for memory manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage Claude Mini memories')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Store command
    store_parser = subparsers.add_parser('store', help='Store a new memory')
    store_parser.add_argument('content', help='Memory content')
    store_parser.add_argument('--type', default='fact', help='Memory type')
    store_parser.add_argument('--importance', type=int, default=5, help='Importance (1-10)')
    store_parser.add_argument('--tags', nargs='+', help='Tags')
    store_parser.add_argument('--source', help='Source of memory')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search memories')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=10, help='Number of results')
    search_parser.add_argument('--min-similarity', type=float, default=0.0, help='Minimum similarity')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List memories')
    list_parser.add_argument('--type', help='Filter by type')
    list_parser.add_argument('--tags', nargs='+', help='Filter by tags')
    list_parser.add_argument('--limit', type=int, default=20, help='Number of results')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show memory statistics')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize with core memories')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    mm = MemoryManager()
    
    if args.command == 'store':
        memory_id = mm.store_memory(
            content=args.content,
            memory_type=args.type,
            importance=args.importance,
            tags=args.tags,
            source=args.source
        )
        print(f"Stored memory with ID: {memory_id}")
    
    elif args.command == 'search':
        results = mm.search_similar(args.query, args.limit, args.min_similarity)
        for r in results:
            print(f"\n[{r['similarity']:.2f}] {r['memory_type'].upper()}: {r['content']}")
            if r['tags']:
                print(f"Tags: {', '.join(r['tags'])}")
    
    elif args.command == 'list':
        if args.type:
            results = mm.get_by_type(args.type, args.limit)
        elif args.tags:
            results = mm.get_by_tags(args.tags, args.limit)
        else:
            print("Please specify --type or --tags")
            return
        
        for r in results:
            print(f"\n[{r['importance']}] {r.get('memory_type', 'UNKNOWN').upper()}: {r['content']}")
            if r.get('tags'):
                print(f"Tags: {', '.join(r['tags'])}")
    
    elif args.command == 'stats':
        stats = mm.stats()
        print(f"Total memories: {stats['total']} ({stats['active']} active)")
        print(f"Core memories: {stats['core']}")
        if stats['avg_importance']:
            print(f"Average importance: {stats['avg_importance']:.1f}")
        print(f"Latest memory: {stats['latest_memory']}")
        print("\nMemories by type:")
        for mtype, count in stats['by_type'].items():
            print(f"  {mtype}: {count}")
    
    elif args.command == 'init':
        mm.add_core_memories()
        print("Core memories initialized!")


if __name__ == "__main__":
    main()