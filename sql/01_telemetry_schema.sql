-- ============================================================================
-- NextOmni Analytical Intelligence Engine
-- 01_telemetry_schema.sql: PostgreSQL DDL with Indexing, Constraints & Partitioning
-- ============================================================================

-- Ensure uuid-ossp extension is enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Schema namespace for analytics isolation
CREATE SCHEMA IF NOT EXISTS nextomni_telemetry;
SET search_path TO nextomni_telemetry, public;

-- ----------------------------------------------------------------------------
-- 1. Focus Sessions (Deep Work, Pomodoros, Interruptions)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS focus_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    session_date DATE NOT NULL,
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    time_block VARCHAR(16) NOT NULL CHECK (time_block IN ('morning', 'afternoon', 'evening', 'night')),
    course_id VARCHAR(32) NOT NULL,
    course_code VARCHAR(32) NOT NULL,
    planned_duration_min INTEGER NOT NULL CHECK (planned_duration_min > 0),
    actual_duration_min INTEGER NOT NULL CHECK (actual_duration_min > 0),
    interruption_count INTEGER NOT NULL DEFAULT 0 CHECK (interruption_count >= 0),
    flow_score NUMERIC(3, 1) NOT NULL CHECK (flow_score BETWEEN 1.0 AND 10.0),
    is_deep_work SMALLINT NOT NULL DEFAULT 0 CHECK (is_deep_work IN (0, 1)),
    completion_rate NUMERIC(3, 2) NOT NULL CHECK (completion_rate BETWEEN 0.00 AND 1.00),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexing for high-throughput temporal aggregations
CREATE INDEX IF NOT EXISTS idx_focus_user_date ON focus_sessions(user_id, session_date DESC);
CREATE INDEX IF NOT EXISTS idx_focus_course ON focus_sessions(course_id, session_date);
CREATE INDEX IF NOT EXISTS idx_focus_flow_deepwork ON focus_sessions(is_deep_work, flow_score);

-- ----------------------------------------------------------------------------
-- 2. Circadian Energy & Biometric Logs
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS circadian_energy_logs (
    log_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    log_date DATE NOT NULL,
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    time_block VARCHAR(16) NOT NULL CHECK (time_block IN ('morning', 'afternoon', 'evening', 'night')),
    start_hour SMALLINT NOT NULL CHECK (start_hour BETWEEN 0 AND 23),
    end_hour SMALLINT NOT NULL CHECK (end_hour BETWEEN 0 AND 24),
    energy_level NUMERIC(3, 1) NOT NULL CHECK (energy_level BETWEEN 1.0 AND 5.0),
    sleep_hours_prev_night NUMERIC(3, 1) NOT NULL CHECK (sleep_hours_prev_night >= 0.0),
    sleep_quality_score NUMERIC(3, 1) NOT NULL CHECK (sleep_quality_score BETWEEN 1.0 AND 5.0),
    caffeine_intake_mg NUMERIC(5, 1) NOT NULL DEFAULT 0.0,
    burnout_risk_proxy NUMERIC(4, 3) NOT NULL CHECK (burnout_risk_proxy BETWEEN 0.000 AND 1.000),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_user_date_block UNIQUE (user_id, log_date, time_block)
);

CREATE INDEX IF NOT EXISTS idx_circadian_date ON circadian_energy_logs(user_id, log_date DESC);

-- ----------------------------------------------------------------------------
-- 3. Habit Tracking & Streak Telemetry
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS habit_logs (
    log_id VARCHAR(128) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    habit_id VARCHAR(64) NOT NULL,
    habit_category VARCHAR(32) NOT NULL CHECK (habit_category IN ('deep_work', 'fitness', 'mind', 'wellness', 'academic')),
    log_date DATE NOT NULL,
    is_completed SMALLINT NOT NULL DEFAULT 0 CHECK (is_completed IN (0, 1)),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_habit_user_date UNIQUE (user_id, habit_id, log_date)
);

CREATE INDEX IF NOT EXISTS idx_habit_logs_temporal ON habit_logs(user_id, habit_id, log_date DESC);
CREATE INDEX IF NOT EXISTS idx_habit_category ON habit_logs(habit_category, is_completed);

-- ----------------------------------------------------------------------------
-- 4. Cognitive Reflection & Qualitative Debriefs
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS journal_entries (
    entry_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    entry_date DATE NOT NULL,
    mood_score INTEGER NOT NULL CHECK (mood_score BETWEEN 1 AND 5),
    energy_level NUMERIC(3, 1) NOT NULL CHECK (energy_level BETWEEN 1.0 AND 5.0),
    sentiment_ground_truth VARCHAR(16) NOT NULL CHECK (sentiment_ground_truth IN ('positive', 'neutral', 'negative')),
    burnout_label SMALLINT NOT NULL DEFAULT 0 CHECK (burnout_label IN (0, 1)),
    journal_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_journal_user_date ON journal_entries(user_id, entry_date DESC);
CREATE INDEX IF NOT EXISTS idx_journal_burnout ON journal_entries(burnout_label);

-- ----------------------------------------------------------------------------
-- 5. Academic Milestones & Task Deliverables
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS academic_tasks (
    task_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    course_id VARCHAR(32) NOT NULL,
    title VARCHAR(255) NOT NULL,
    weightage NUMERIC(5, 2) NOT NULL DEFAULT 10.00,
    priority VARCHAR(16) NOT NULL CHECK (priority IN ('urgent', 'high', 'medium', 'low')),
    estimated_hours NUMERIC(4, 1) NOT NULL,
    assigned_date DATE NOT NULL,
    due_date DATE NOT NULL,
    is_completed SMALLINT NOT NULL DEFAULT 0 CHECK (is_completed IN (0, 1)),
    completed_date DATE,
    procrastination_hours NUMERIC(6, 1) NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_academic_tasks_due ON academic_tasks(user_id, due_date ASC);
