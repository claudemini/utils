-- Create task scheduling tables for Claude Brain automation

-- Enable pgcrypto for UUID generation if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Task definitions table
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(50) NOT NULL CHECK (task_type IN (
        'memory_management', 'social_media', 'financial_monitoring', 
        'system_monitoring', 'learning_research', 'daily_routine',
        'personality_development', 'goal_management', 'trading_operations',
        'backup_maintenance', 'network_security', 'tool_development',
        'content_creation', 'environmental_response', 'custom'
    )),
    description TEXT,
    command TEXT NOT NULL,
    schedule_type VARCHAR(20) NOT NULL CHECK (schedule_type IN ('once', 'recurring', 'cron')),
    cron_expression VARCHAR(100), -- For cron-based scheduling
    interval_minutes INTEGER, -- For recurring tasks
    next_run_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_run_at TIMESTAMP WITH TIME ZONE,
    last_success_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'failed')),
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    max_retries INTEGER DEFAULT 3,
    retry_count INTEGER DEFAULT 0,
    timeout_seconds INTEGER DEFAULT 300, -- 5 minute default timeout
    requires_brain BOOLEAN DEFAULT FALSE, -- Whether to use brain.sh vs claude -p
    context_memory_ids INTEGER[], -- Related memory IDs for context
    depends_on_task_id INTEGER REFERENCES scheduled_tasks(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Task execution history table
CREATE TABLE IF NOT EXISTS task_executions (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES scheduled_tasks(id),
    execution_id UUID DEFAULT uuid_generate_v4(),
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'success', 'failed', 'timeout', 'cancelled')),
    output TEXT,
    error TEXT,
    execution_time_ms INTEGER,
    memory_ids INTEGER[], -- Memories created during execution
    log_file_path VARCHAR(500),
    metadata JSONB DEFAULT '{}'
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next_run ON scheduled_tasks(next_run_at) WHERE is_active = TRUE AND status = 'active';
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_type ON scheduled_tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_status ON scheduled_tasks(status);
CREATE INDEX IF NOT EXISTS idx_task_executions_task_id ON task_executions(task_id);
CREATE INDEX IF NOT EXISTS idx_task_executions_started_at ON task_executions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_task_executions_status ON task_executions(status);

-- Auto-update updated_at function
CREATE OR REPLACE FUNCTION update_scheduled_tasks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger if it doesn't exist
DROP TRIGGER IF EXISTS update_scheduled_tasks_updated_at ON scheduled_tasks;
CREATE TRIGGER update_scheduled_tasks_updated_at 
    BEFORE UPDATE ON scheduled_tasks 
    FOR EACH ROW 
    EXECUTE FUNCTION update_scheduled_tasks_updated_at();

-- Function to get next tasks to run
CREATE OR REPLACE FUNCTION get_pending_tasks(batch_size INTEGER DEFAULT 10)
RETURNS TABLE(
    id INTEGER,
    task_name VARCHAR,
    task_type VARCHAR,
    command TEXT,
    priority INTEGER,
    timeout_seconds INTEGER,
    requires_brain BOOLEAN,
    context_memory_ids INTEGER[],
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        st.id,
        st.task_name,
        st.task_type,
        st.command,
        st.priority,
        st.timeout_seconds,
        st.requires_brain,
        st.context_memory_ids,
        st.metadata
    FROM scheduled_tasks st
    WHERE st.is_active = TRUE
        AND st.status = 'active'
        AND st.next_run_at <= CURRENT_TIMESTAMP
        AND (st.depends_on_task_id IS NULL 
             OR EXISTS (
                 SELECT 1 FROM task_executions te 
                 WHERE te.task_id = st.depends_on_task_id 
                 AND te.status = 'success'
                 AND te.completed_at > COALESCE(st.last_run_at, '1970-01-01'::timestamptz)
             ))
    ORDER BY st.priority DESC, st.next_run_at ASC
    LIMIT batch_size;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate next run time
CREATE OR REPLACE FUNCTION calculate_next_run(
    schedule_type VARCHAR,
    cron_expression VARCHAR,
    interval_minutes INTEGER,
    last_run TIMESTAMP WITH TIME ZONE
)
RETURNS TIMESTAMP WITH TIME ZONE AS $$
DECLARE
    next_run TIMESTAMP WITH TIME ZONE;
BEGIN
    IF schedule_type = 'once' THEN
        RETURN NULL;
    ELSIF schedule_type = 'recurring' AND interval_minutes IS NOT NULL THEN
        RETURN COALESCE(last_run, CURRENT_TIMESTAMP) + (interval_minutes || ' minutes')::INTERVAL;
    ELSIF schedule_type = 'cron' AND cron_expression IS NOT NULL THEN
        -- For now, we'll handle basic cron patterns manually
        -- In production, you'd want to use a proper cron parser
        -- This is a simplified version
        IF cron_expression = '0 6 * * *' THEN -- Daily at 6am
            next_run := DATE_TRUNC('day', COALESCE(last_run, CURRENT_TIMESTAMP)) + INTERVAL '1 day 6 hours';
        ELSIF cron_expression = '0 12 * * *' THEN -- Daily at noon
            next_run := DATE_TRUNC('day', COALESCE(last_run, CURRENT_TIMESTAMP)) + INTERVAL '1 day 12 hours';
        ELSIF cron_expression = '0 21 * * *' THEN -- Daily at 9pm
            next_run := DATE_TRUNC('day', COALESCE(last_run, CURRENT_TIMESTAMP)) + INTERVAL '1 day 21 hours';
        ELSIF cron_expression = '0 23 * * *' THEN -- Daily at 11pm
            next_run := DATE_TRUNC('day', COALESCE(last_run, CURRENT_TIMESTAMP)) + INTERVAL '1 day 23 hours';
        ELSIF cron_expression = '*/30 * * * *' THEN -- Every 30 minutes
            RETURN COALESCE(last_run, CURRENT_TIMESTAMP) + INTERVAL '30 minutes';
        ELSIF cron_expression = '*/5 * * * *' THEN -- Every 5 minutes
            RETURN COALESCE(last_run, CURRENT_TIMESTAMP) + INTERVAL '5 minutes';
        ELSE
            -- Default to daily if we can't parse
            RETURN COALESCE(last_run, CURRENT_TIMESTAMP) + INTERVAL '1 day';
        END IF;
        
        -- If calculated time is in the past, add appropriate interval
        WHILE next_run <= CURRENT_TIMESTAMP LOOP
            next_run := next_run + INTERVAL '1 day';
        END LOOP;
        
        RETURN next_run;
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- View for active tasks with execution stats
CREATE OR REPLACE VIEW active_tasks_view AS
SELECT 
    st.*,
    COUNT(te.id) as total_executions,
    COUNT(CASE WHEN te.status = 'success' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN te.status = 'failed' THEN 1 END) as failed_executions,
    AVG(te.execution_time_ms) as avg_execution_time_ms,
    MAX(te.completed_at) as last_completed_at
FROM scheduled_tasks st
LEFT JOIN task_executions te ON st.id = te.task_id
WHERE st.is_active = TRUE
GROUP BY st.id;