-- ============================================================================
-- NextOmni Analytical Intelligence Engine
-- 02_feature_engineering_etl.sql: Advanced Analytics, CTEs & Feature Store ETL
-- ============================================================================

SET search_path TO nextomni_telemetry, public;

-- ----------------------------------------------------------------------------
-- 1. FOCUS SESSION TEMPORAL AGGREGATIONS & ROLLING WINDOW FEATURES
-- Demonstrates: CTEs, Window Functions (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW),
-- Cumulative partitions, and Lag-based inter-session interval analysis.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_daily_focus_metrics AS
WITH daily_session_rollup AS (
    SELECT
        user_id,
        session_date,
        COUNT(session_id) AS total_sessions_count,
        SUM(actual_duration_min) AS total_focus_min,
        SUM(CASE WHEN is_deep_work = 1 THEN actual_duration_min ELSE 0 END) AS deep_work_min,
        ROUND(AVG(flow_score), 2) AS avg_flow_score,
        SUM(interruption_count) AS total_interruptions,
        ROUND(AVG(completion_rate), 3) AS avg_completion_rate
    FROM focus_sessions
    GROUP BY user_id, session_date
)
SELECT
    user_id,
    session_date,
    total_sessions_count,
    total_focus_min,
    deep_work_min,
    avg_flow_score,
    total_interruptions,
    avg_completion_rate,
    -- 7-Day Rolling Average Focus Minutes
    ROUND(
        AVG(total_focus_min) OVER (
            PARTITION BY user_id
            ORDER BY session_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 1
    ) AS rolling_7d_avg_focus_min,
    -- 7-Day Rolling Average Flow Score
    ROUND(
        AVG(avg_flow_score) OVER (
            PARTITION BY user_id
            ORDER BY session_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 2
    ) AS rolling_7d_avg_flow_score,
    -- 14-Day Rolling Sum of Interruptions
    SUM(total_interruptions) OVER (
        PARTITION BY user_id
        ORDER BY session_date
        ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
    ) AS rolling_14d_interruptions,
    -- Prior Day Focus Duration (Lag for Delta Velocity)
    LAG(total_focus_min, 1) OVER (
        PARTITION BY user_id
        ORDER BY session_date
    ) AS prev_day_focus_min
FROM daily_session_rollup;


-- ----------------------------------------------------------------------------
-- 2. GAPS-AND-ISLANDS HABIT STREAK ANALYTICS
-- Calculates historical and active consecutive streaks per habit using 
-- date math and ROW_NUMBER() differences.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_habit_streak_analytics AS
WITH streak_groups AS (
    SELECT
        user_id,
        habit_id,
        habit_category,
        log_date,
        is_completed,
        -- The Island identifier: log_date minus sequential rank
        (log_date - (ROW_NUMBER() OVER (
            PARTITION BY user_id, habit_id
            ORDER BY log_date
        ) * INTERVAL '1 day'))::DATE AS island_group_id
    FROM habit_logs
    WHERE is_completed = 1
),
island_aggregates AS (
    SELECT
        user_id,
        habit_id,
        habit_category,
        island_group_id,
        MIN(log_date) AS streak_start_date,
        MAX(log_date) AS streak_end_date,
        COUNT(*) AS streak_length_days
    FROM streak_groups
    GROUP BY user_id, habit_id, habit_category, island_group_id
)
SELECT
    user_id,
    habit_id,
    habit_category,
    island_group_id,
    streak_start_date,
    streak_end_date,
    streak_length_days,
    -- Maximum historic streak achieved up to this island
    MAX(streak_length_days) OVER (
        PARTITION BY user_id, habit_id
    ) AS all_time_max_streak,
    -- Check if this streak is currently active (ended within last 2 days)
    CASE 
        WHEN streak_end_date >= (CURRENT_DATE - INTERVAL '1 day') THEN 1 
        ELSE 0 
    END AS is_currently_active_streak
FROM island_aggregates;


-- ----------------------------------------------------------------------------
-- 3. CIRCADIAN CHRONOTYPE MISALIGNMENT INDEX (CMI)
-- Compares when the user studied versus their recorded circadian peak energy.
-- Misalignment occurs when intensive deep work is forced during postprandial 
-- or night troughs.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_circadian_misalignment AS
WITH daily_circadian_peaks AS (
    SELECT
        user_id,
        log_date,
        MAX(sleep_hours_prev_night) AS sleep_hours,
        MAX(sleep_quality_score) AS sleep_quality,
        MAX(caffeine_intake_mg) AS caffeine_intake_mg,
        ROUND(AVG(energy_level), 2) AS avg_daily_energy,
        -- Identify block with peak energy
        (ARRAY_AGG(time_block ORDER BY energy_level DESC))[1] AS peak_energy_block
    FROM circadian_energy_logs
    GROUP BY user_id, log_date
),
focus_by_block AS (
    SELECT
        user_id,
        session_date,
        time_block,
        SUM(actual_duration_min) AS block_focus_min,
        SUM(is_deep_work) AS block_deep_work_count
    FROM focus_sessions
    GROUP BY user_id, session_date, time_block
)
SELECT
    cp.user_id,
    cp.log_date,
    cp.sleep_hours,
    cp.sleep_quality,
    cp.caffeine_intake_mg,
    cp.avg_daily_energy,
    cp.peak_energy_block,
    COALESCE(fb.block_focus_min, 0) AS peak_block_focus_min,
    COALESCE(fn.night_focus_min, 0) AS night_strain_focus_min,
    -- Chronotype Misalignment Index (CMI): % of focus work pushed into sub-optimal night/fatigue blocks
    ROUND(
        (COALESCE(fn.night_focus_min, 0)::NUMERIC / NULLIF(dfm.total_focus_min, 0)::NUMERIC) * 100.0, 
        2
    ) AS chronotype_misalignment_index_pct
FROM daily_circadian_peaks cp
LEFT JOIN focus_by_block fb 
    ON cp.user_id = fb.user_id 
    AND cp.log_date = fb.session_date 
    AND cp.peak_energy_block = fb.time_block
LEFT JOIN (
    SELECT user_id, session_date, SUM(actual_duration_min) AS night_focus_min
    FROM focus_sessions
    WHERE time_block = 'night'
    GROUP BY user_id, session_date
) fn ON cp.user_id = fn.user_id AND cp.log_date = fn.session_date
LEFT JOIN v_daily_focus_metrics dfm 
    ON cp.user_id = dfm.user_id 
    AND cp.log_date = dfm.session_date;


-- ----------------------------------------------------------------------------
-- 4. MACHINE LEARNING FEATURE STORE: DAILY INTEGRATED ANALYTIC BASE (ABT)
-- Merges Focus, Circadian, Habits, Tasks, and Journal Labels into a single
-- ML-ready analytical base table for burnout classification & time-series modeling.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ml_feature_store_daily AS
SELECT
    f.user_id,
    f.session_date AS record_date,
    EXTRACT(ISODOW FROM f.session_date) AS day_of_week,
    -- Focus metrics
    COALESCE(f.total_sessions_count, 0) AS total_sessions,
    COALESCE(f.total_focus_min, 0) AS total_focus_min,
    COALESCE(f.deep_work_min, 0) AS deep_work_min,
    COALESCE(f.avg_flow_score, 5.0) AS avg_flow_score,
    COALESCE(f.total_interruptions, 0) AS total_interruptions,
    COALESCE(f.rolling_7d_avg_focus_min, 0.0) AS rolling_7d_focus_min,
    COALESCE(f.rolling_7d_avg_flow_score, 5.0) AS rolling_7d_flow_score,
    COALESCE(f.rolling_14d_interruptions, 0) AS rolling_14d_interruptions,
    -- Circadian & biometric telemetry
    COALESCE(c.sleep_hours, 7.0) AS sleep_hours,
    COALESCE(c.sleep_quality, 3.5) AS sleep_quality,
    COALESCE(c.caffeine_intake_mg, 150.0) AS caffeine_intake_mg,
    COALESCE(c.avg_daily_energy, 3.5) AS avg_daily_energy,
    COALESCE(c.chronotype_misalignment_index_pct, 0.0) AS chronotype_misalignment_pct,
    -- Habit adherence rate (completed / target across active habits today)
    COALESCE(h.daily_habit_completion_rate, 0.0) AS daily_habit_completion_rate,
    COALESCE(h.rolling_7d_habit_rate, 0.0) AS rolling_7d_habit_rate,
    -- Academic pressure (pending high priority tasks in next 3 days)
    COALESCE(t.urgent_tasks_due_next_72h, 0) AS urgent_tasks_due_next_72h,
    -- Ground Truth Target for ML (Burnout Risk flag from next 7 days or journal debrief)
    COALESCE(j.burnout_label, 0) AS target_burnout_flag
FROM v_daily_focus_metrics f
LEFT JOIN v_circadian_misalignment c 
    ON f.user_id = c.user_id AND f.session_date = c.log_date
LEFT JOIN (
    SELECT
        user_id,
        log_date,
        ROUND(AVG(is_completed::NUMERIC), 3) AS daily_habit_completion_rate,
        ROUND(AVG(AVG(is_completed::NUMERIC)) OVER (
            PARTITION BY user_id
            ORDER BY log_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 3) AS rolling_7d_habit_rate
    FROM habit_logs
    GROUP BY user_id, log_date
) h ON f.user_id = h.user_id AND f.session_date = h.log_date
LEFT JOIN (
    SELECT
        user_id,
        assigned_date,
        COUNT(CASE WHEN priority IN ('urgent', 'high') AND is_completed = 0 THEN 1 END) AS urgent_tasks_due_next_72h
    FROM academic_tasks
    GROUP BY user_id, assigned_date
) t ON f.user_id = t.user_id AND f.session_date = t.assigned_date
LEFT JOIN journal_entries j
    ON f.user_id = j.user_id AND f.session_date = j.entry_date;

CREATE UNIQUE INDEX IF NOT EXISTS idx_ml_feat_store ON ml_feature_store_daily(user_id, record_date);
