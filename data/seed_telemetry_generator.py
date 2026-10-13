"""
NextOmni Analytics Intelligence - Synthetic Telemetry Seed Generator
Generates realistic, longitudinal multi-table telemetry for 180 days across:
- Focus Sessions (Pomodoros, deep work, interruptions, flow score)
- Circadian Energy Logs (chronotype alignment, sleep, caffeine)
- Habits & Habit Logs (streaks, drop-offs, recovery patterns)
- Academic Progress (courses, tasks, deadlines, completion)
- Cognitive Debriefs (journal text, mood scores, cognitive fatigue)
"""

import os
import json
import random
import datetime
import math
import csv

# Set deterministic seed for reproducibility
random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "seeds")
os.makedirs(OUTPUT_DIR, exist_ok=True)

START_DATE = datetime.date(2026, 4, 1)
DAYS_COUNT = 180
USER_ID = "usr_01h8nextomni99x7alpha"

COURSES = [
    {"id": "crs_cs301", "name": "Distributed Systems", "code": "CS-301", "credits": 4, "difficulty": 0.85},
    {"id": "crs_stat410", "name": "Applied Bayesian Statistics", "code": "STAT-410", "credits": 3, "difficulty": 0.75},
    {"id": "crs_ml420", "name": "Deep Learning & Neural Architectures", "code": "CS-420", "credits": 4, "difficulty": 0.90},
    {"id": "crs_cog205", "name": "Cognitive Psychology & Ergonomics", "code": "PSYC-205", "credits": 3, "difficulty": 0.50},
]

HABITS = [
    {"id": "hbt_deepwork", "title": "Morning 90m Deep Work Block", "category": "deep_work", "target_days_week": 6, "base_prob": 0.82},
    {"id": "hbt_workout", "title": "Zone-2 Cardio or Strength", "category": "fitness", "target_days_week": 5, "base_prob": 0.70},
    {"id": "hbt_mindful", "title": "Evening 15m Vipassana Meditation", "category": "mind", "target_days_week": 7, "base_prob": 0.65},
    {"id": "hbt_sleep", "title": "Lights Out by 23:15", "category": "wellness", "target_days_week": 7, "base_prob": 0.60},
    {"id": "hbt_review", "title": "Spaced Repetition Flashcard Drill", "category": "academic", "target_days_week": 6, "base_prob": 0.78},
]

JOURNAL_PROMPTS_POOL = {
    "high_energy": [
        "Incredible focus session today on distributed consensus algorithm proofs. Entered effortless flow state.",
        "Energy peaked after morning workout; crushed 3 modules of Bayesian inference before noon. Highly clarity-driven.",
        "Deep momentum established early. Zero context switching, clean architecture design achieved for the ML lab.",
        "Felt fully synchronized with circadian rhythms. High motivation, sharp mental retention and high flow."
    ],
    "neutral": [
        "Steady progress through regular coursework. Completed scheduled tasks with average mental effort.",
        "Moderate cognitive load today. Took scheduled breaks, stayed relatively on track without standout friction.",
        "Routine study day. Solved expected problem sets, attended lectures, pace was sustainable.",
        "Decent day overall; minor distractions in the afternoon but recovered evening focus session."
    ],
    "low_energy_fatigue": [
        "Struggled with brain fog following insufficient REM sleep. Distractions kept derailing flow state.",
        "Felt overwhelming cognitive friction during deep learning debugging. Procrastinated for 2 hours.",
        "Severe afternoon crash after heavy caffeine spike. Mental fatigue and burnout warning signs present.",
        "Missed morning habit streak due to exhaustion. Experiencing impostor syndrome and deadline panic."
    ]
}

def generate_telemetry():
    focus_sessions = []
    circadian_logs = []
    habit_logs = []
    journal_entries = []
    tasks = []
    
    # Pre-generate 40 Academic Tasks throughout the 180 days
    task_counter = 1
    for day_offset in range(1, DAYS_COUNT, 4):
        assigned_date = START_DATE + datetime.timedelta(days=day_offset)
        course = random.choice(COURSES)
        due_date = assigned_date + datetime.timedelta(days=random.randint(3, 10))
        tasks.append({
            "task_id": f"tsk_{task_counter:04d}",
            "user_id": USER_ID,
            "course_id": course["id"],
            "title": f"{course['code']} Milestone {task_counter}: Problem Set & Lab Assignment",
            "weightage": round(random.uniform(5.0, 20.0), 1),
            "priority": random.choice(["high", "urgent", "medium"]),
            "estimated_hours": round(random.uniform(2.5, 8.0), 1),
            "assigned_date": str(assigned_date),
            "due_date": str(due_date),
            "is_completed": None, # Will resolve dynamically
            "completed_date": None,
            "procrastination_hours": 0.0
        })
        task_counter += 1

    # Simulate Day-by-Day Telemetry with Autoregressive Dynamics & Stress Cycles
    base_burnout_factor = 0.15 # 0.0 (fresh) to 1.0 (severe burnout)
    caffeine_tolerance = 1.0

    for day_i in range(DAYS_COUNT):
        curr_date = START_DATE + datetime.timedelta(days=day_i)
        day_of_week = curr_date.weekday() # 0 = Monday, 6 = Sunday
        is_weekend = day_of_week >= 5

        # Academic semester mid-term and final stress wave injection (around day 45-60, and day 135-155)
        is_exam_season = (45 <= day_i <= 65) or (135 <= day_i <= 155)
        stress_modifier = 0.25 if is_exam_season else 0.0

        # Circadian & Sleep Simulation
        sleep_hours = round(random.gauss(7.2 - (stress_modifier * 1.5), 0.9), 1)
        sleep_hours = max(4.0, min(9.5, sleep_hours))
        sleep_quality = round(max(1.0, min(5.0, (sleep_hours / 8.0) * 4.5 + random.uniform(-0.5, 0.5))), 1)

        caffeine_mg = round(random.gauss(150 + (stress_modifier * 120), 40), 0)
        caffeine_mg = max(0.0, min(450.0, caffeine_mg))

        # Update burnout factor with mean-reverting decay and stress surges
        recovery_bonus = 0.12 if sleep_hours >= 7.5 else 0.04
        daily_strain = (0.22 if is_exam_season else 0.04) + (0.08 if sleep_hours < 6.0 else 0.0)
        base_burnout_factor = max(0.08, min(0.85, (base_burnout_factor * 0.75) + daily_strain - (recovery_bonus if is_weekend else 0.0)))

        # Circadian Energy logs across 4 blocks: Morning (08-12), Afternoon (12-17), Evening (17-21), Night (21-01)
        blocks = [
            ("morning", 9, 12, 4.2 - (base_burnout_factor * 1.8)),
            ("afternoon", 13, 17, 3.4 - (base_burnout_factor * 1.5) - (0.5 if caffeine_mg > 250 else 0)), # Postprandial dip
            ("evening", 17, 21, 3.8 - (base_burnout_factor * 1.2)),
            ("night", 21, 24, 2.5 - (base_burnout_factor * 2.0))
        ]

        for block_name, s_hr, e_hr, baseline_energy in blocks:
            energy_score = round(max(1.0, min(5.0, baseline_energy + random.gauss(0, 0.4))), 1)
            circadian_logs.append({
                "log_id": f"cir_{day_i:03d}_{block_name}",
                "user_id": USER_ID,
                "log_date": str(curr_date),
                "day_of_week": day_of_week,
                "time_block": block_name,
                "start_hour": s_hr,
                "end_hour": e_hr,
                "energy_level": energy_score,
                "sleep_hours_prev_night": sleep_hours,
                "sleep_quality_score": sleep_quality,
                "caffeine_intake_mg": caffeine_mg,
                "burnout_risk_proxy": round(base_burnout_factor, 3)
            })

        # Focus Sessions (1 to 4 sessions per day)
        num_sessions = 1 if is_weekend else (random.randint(2, 4) if not is_exam_season else random.randint(3, 5))
        for s_idx in range(num_sessions):
            session_duration = random.choice([25, 45, 50, 60, 90, 110])
            # Interruption probability correlates directly with burnout and phone proximity
            interruptions = max(0, int(random.gauss(base_burnout_factor * 4.5, 1.2)))
            
            # Flow state score (1 to 10): penalised by interruptions and burnout, boosted by sleep
            flow_score = round(max(1.0, min(10.0, 8.5 - (interruptions * 1.1) - (base_burnout_factor * 4.0) + (sleep_quality * 0.4))), 1)
            
            active_course = random.choice(COURSES)
            session_block = random.choice(["morning", "afternoon", "evening", "night"])
            
            focus_sessions.append({
                "session_id": f"fcs_{day_i:03d}_{s_idx:02d}",
                "user_id": USER_ID,
                "session_date": str(curr_date),
                "day_of_week": day_of_week,
                "time_block": session_block,
                "course_id": active_course["id"],
                "course_code": active_course["code"],
                "planned_duration_min": session_duration,
                "actual_duration_min": max(15, session_duration - (interruptions * 4) + random.randint(-5, 5)),
                "interruption_count": interruptions,
                "flow_score": flow_score,
                "is_deep_work": 1 if session_duration >= 45 and interruptions <= 1 and flow_score >= 7.0 else 0,
                "completion_rate": round(min(1.0, max(0.4, (flow_score / 10.0) + random.uniform(-0.1, 0.1))), 2)
            })

        # Habits Simulation with survival decay
        for h in HABITS:
            # Completion probability penalized by burnout factor
            dropoff_penalty = base_burnout_factor * 0.45
            day_prob = max(0.15, h["base_prob"] - dropoff_penalty)
            
            completed = 1 if random.random() <= day_prob else 0
            habit_logs.append({
                "log_id": f"hlog_{curr_date}_{h['id']}",
                "user_id": USER_ID,
                "habit_id": h["id"],
                "habit_category": h["category"],
                "log_date": str(curr_date),
                "is_completed": completed
            })

        # Cognitive Debrief / Journal Generation (Every 1-2 days)
        if random.random() <= 0.85:
            if base_burnout_factor > 0.55 or sleep_hours < 5.5:
                sentiment_class = "negative"
                mood_score = random.randint(1, 2)
                content = random.choice(JOURNAL_PROMPTS_POOL["low_energy_fatigue"])
            elif base_burnout_factor < 0.25 and sleep_hours >= 7.2:
                sentiment_class = "positive"
                mood_score = random.randint(4, 5)
                content = random.choice(JOURNAL_PROMPTS_POOL["high_energy"])
            else:
                sentiment_class = "neutral"
                mood_score = 3
                content = random.choice(JOURNAL_PROMPTS_POOL["neutral"])

            journal_entries.append({
                "entry_id": f"jrn_{day_i:03d}",
                "user_id": USER_ID,
                "entry_date": str(curr_date),
                "mood_score": mood_score,
                "energy_level": round(3.5 - (base_burnout_factor * 2.0) + random.uniform(-0.3, 0.3), 1),
                "sentiment_ground_truth": sentiment_class,
                "burnout_label": 1 if base_burnout_factor >= 0.50 else 0,
                "journal_text": content
            })

    # Resolve Task completions against generated dates
    for t in tasks:
        due = datetime.datetime.strptime(t["due_date"], "%Y-%m-%d").date()
        # High burnout increases late submission or incomplete rate
        status_roll = random.random()
        if status_roll > 0.10:
            t["is_completed"] = 1
            # Did they finish early, on time, or late?
            delay_days = random.choices([-2, -1, 0, 1, 2, 4], weights=[0.2, 0.3, 0.3, 0.1, 0.07, 0.03])[0]
            completed_dt = due + datetime.timedelta(days=delay_days)
            t["completed_date"] = str(completed_dt)
            t["procrastination_hours"] = max(0.0, delay_days * 24.0)
        else:
            t["is_completed"] = 0
            t["completed_date"] = None
            t["procrastination_hours"] = 72.0

    # Write CSVs
    def write_csv(filename, fieldnames, rows):
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Generated {filepath} ({len(rows)} rows)")

    write_csv("focus_sessions.csv", list(focus_sessions[0].keys()), focus_sessions)
    write_csv("circadian_energy_logs.csv", list(circadian_logs[0].keys()), circadian_logs)
    write_csv("habit_logs.csv", list(habit_logs[0].keys()), habit_logs)
    write_csv("journal_entries.csv", list(journal_entries[0].keys()), journal_entries)
    write_csv("academic_tasks.csv", list(tasks[0].keys()), tasks)

if __name__ == "__main__":
    generate_telemetry()
