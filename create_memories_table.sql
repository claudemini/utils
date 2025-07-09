-- Create memories table with vector support
CREATE TABLE IF NOT EXISTS memories (
    id SERIAL PRIMARY KEY,
    memory_type VARCHAR(50) NOT NULL CHECK (memory_type IN ('core', 'fact', 'instruction', 'preference', 'conversation', 'task', 'relationship')),
    content TEXT NOT NULL,
    context JSONB,
    embedding vector(384) NOT NULL,  -- Using sentence-transformers dimension (384)
    importance INTEGER DEFAULT 5 CHECK (importance >= 1 AND importance <= 10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    tags TEXT[],
    source VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_tags ON memories USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_memories_context ON memories USING GIN(context);
CREATE INDEX IF NOT EXISTS idx_memories_active ON memories(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Auto-update updated_at function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger if it doesn't exist
DROP TRIGGER IF EXISTS update_memories_updated_at ON memories;
CREATE TRIGGER update_memories_updated_at 
    BEFORE UPDATE ON memories 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Update access tracking function
CREATE OR REPLACE FUNCTION update_memory_access(memory_id INTEGER)
RETURNS VOID AS $$
BEGIN
    UPDATE memories 
    SET accessed_at = CURRENT_TIMESTAMP,
        access_count = access_count + 1
    WHERE id = memory_id;
END;
$$ LANGUAGE plpgsql;

-- Semantic search function
CREATE OR REPLACE FUNCTION search_memories_by_similarity(
    query_embedding vector(384),
    limit_count INTEGER DEFAULT 10,
    min_similarity FLOAT DEFAULT 0.0
)
RETURNS TABLE(
    id INTEGER,
    content TEXT,
    memory_type VARCHAR,
    importance INTEGER,
    similarity FLOAT,
    tags TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.content,
        m.memory_type,
        m.importance,
        1 - (m.embedding <=> query_embedding) as similarity,
        m.tags
    FROM memories m
    WHERE m.is_active = TRUE
    AND (1 - (m.embedding <=> query_embedding)) >= min_similarity
    ORDER BY m.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;