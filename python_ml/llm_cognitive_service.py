"""
NextOmni Analytics Intelligence Engine - FastAPI Service & LLM Synthesis
Provides REST API endpoints for:
1. /api/v1/predict/burnout-risk: Real-time inference using trained Gradient Boosting model.
2. /api/v1/cognitive/debrief: GenAI journal reflection, sentiment, and cognitive distortion analysis.
3. /api/v1/telemetry/digest: Executive Natural-Language weekly brief synthesis.
"""

import os
import json
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import joblib
import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "..", ".env"))

app = FastAPI(
    title="NextOmni Telemetry Intelligence & GenAI Service",
    version="1.0.0",
    description="Principal Analytics Microservice bridging ML prediction with LLM cognitive synthesis."
)

MODEL_PATH = os.path.join(BASE_DIR, "models", "burnout_risk_model.joblib")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# In-memory model cache
model_artifact = None

def get_model():
    global model_artifact
    if model_artifact is None:
        if os.path.exists(MODEL_PATH):
            model_artifact = joblib.load(MODEL_PATH)
        else:
            return None
    return model_artifact

def call_gemini_api(prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
    """Invokes Google Gemini API if GEMINI_API_KEY is configured, else returns None."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        
        response = requests.post(url, json=payload, timeout=8)
        if response.status_code == 200:
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        pass
    return None

# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------
class TelemetryFeaturesInput(BaseModel):
    user_id: str
    total_focus_min: float = Field(..., ge=0, description="Total focus minutes logged today")
    deep_work_min: float = Field(..., ge=0, description="Deep work duration in minutes")
    avg_flow_score: float = Field(..., ge=1.0, le=10.0, description="Subjective flow score (1-10)")
    total_interruptions: int = Field(..., ge=0, description="Number of interruptions logged")
    rolling_7d_focus_min: float = Field(..., ge=0)
    rolling_7d_flow_score: float = Field(..., ge=1.0, le=10.0)
    rolling_14d_interruptions: int = Field(..., ge=0)
    sleep_hours: float = Field(..., ge=0, le=24)
    sleep_quality: float = Field(..., ge=1.0, le=5.0)
    caffeine_intake_mg: float = Field(..., ge=0)
    avg_daily_energy: float = Field(..., ge=1.0, le=5.0)
    habit_adherence_rate: float = Field(..., ge=0.0, le=1.0)
    rolling_7d_habit_rate: float = Field(..., ge=0.0, le=1.0)

class BurnoutPredictionResponse(BaseModel):
    user_id: str
    burnout_probability: float
    risk_tier: str # 'LOW' | 'MODERATE' | 'CRITICAL'
    alert_triggered: bool
    top_driving_factors: List[Dict[str, Any]]
    prescriptive_action: str

class JournalDebriefInput(BaseModel):
    user_id: str
    journal_text: str
    mood_score: int = Field(..., ge=1, le=5)
    energy_level: float = Field(..., ge=1.0, le=5.0)

class CognitiveDistortionAnalysis(BaseModel):
    distortion_type: str
    evidence_snippet: str
    cognitive_reframe: str

class JournalDebriefResponse(BaseModel):
    user_id: str
    sentiment_polarity: str # 'positive' | 'neutral' | 'negative'
    cognitive_load_index: float # 0.0 to 1.0
    detected_distortions: List[CognitiveDistortionAnalysis]
    mentorship_feedback: str

class WeeklyDigestRequest(BaseModel):
    user_id: str
    week_start_date: str
    total_focus_hours: float
    deep_work_percentage: float
    habit_completion_rate: float
    urgent_tasks_completed: int
    urgent_tasks_missed: int

class WeeklyDigestResponse(BaseModel):
    user_id: str
    executive_summary: str
    key_achievements: List[str]
    vulnerabilities_detected: List[str]
    prescriptive_sprint_adjustments: List[str]

# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.get("/health", tags=["System"])
def health_check():
    model_loaded = os.path.exists(MODEL_PATH)
    return {
        "status": "healthy",
        "service": "NextOmni Analytics Intelligence",
        "model_loaded": model_loaded
    }

@app.post("/api/v1/predict/burnout-risk", response_model=BurnoutPredictionResponse, tags=["Inference"])
def predict_burnout(features: TelemetryFeaturesInput):
    artifact = get_model()
    
    # Calculate derived interaction terms
    fatigue_ratio = features.total_interruptions / max(features.sleep_hours, 3.0)
    energy_deficit = max(0, 4.0 - features.avg_daily_energy) * (features.total_focus_min / 60.0)

    feature_dict = {
        "total_focus_min": features.total_focus_min,
        "deep_work_min": features.deep_work_min,
        "avg_flow_score": features.avg_flow_score,
        "total_interruptions": features.total_interruptions,
        "rolling_7d_focus_min": features.rolling_7d_focus_min,
        "rolling_7d_flow_score": features.rolling_7d_flow_score,
        "rolling_14d_interruptions": features.rolling_14d_interruptions,
        "sleep_hours": features.sleep_hours,
        "sleep_quality": features.sleep_quality,
        "caffeine_intake_mg": features.caffeine_intake_mg,
        "avg_daily_energy": features.avg_daily_energy,
        "habit_adherence_rate": features.habit_adherence_rate,
        "rolling_7d_habit_rate": features.rolling_7d_habit_rate,
        "fatigue_ratio": fatigue_ratio,
        "energy_deficit": energy_deficit
    }
    feature_df = pd.DataFrame([feature_dict])

    if artifact:
        model = artifact["model"]
        prob = float(model.predict_proba(feature_df)[0, 1])
    else:
        # Heuristic fallback if model not pre-trained
        prob = min(0.95, max(0.05, (
            (7.5 - features.sleep_hours) * 0.12 +
            (features.total_interruptions * 0.08) +
            (1.0 - features.rolling_7d_habit_rate) * 0.35 +
            (5.0 - features.avg_daily_energy) * 0.10
        )))

    risk_tier = "CRITICAL" if prob >= 0.65 else ("MODERATE" if prob >= 0.35 else "LOW")
    
    # Identify top contributors
    drivers = []
    if features.sleep_hours < 6.0:
        drivers.append({"factor": "Sleep Deprivation", "impact": "High", "metric": f"{features.sleep_hours}h"})
    if features.total_interruptions >= 4:
        drivers.append({"factor": "High Context Switching", "impact": "High", "metric": f"{features.total_interruptions} interruptions"})
    if features.rolling_7d_habit_rate < 0.60:
        drivers.append({"factor": "Habit Adherence Decay", "impact": "Moderate", "metric": f"{features.rolling_7d_habit_rate:.0%}"})
    if not drivers:
        drivers.append({"factor": "Balanced Telemetry", "impact": "Low", "metric": "Nominal circadian reserve"})

    # Prescriptive recommendations
    if risk_tier == "CRITICAL":
        rx = "Initiate Emergency Cognitive Deload: Enforce hard stop at 21:00, cap next day focus sessions to 60m maximum, reschedule low-priority tasks."
    elif risk_tier == "MODERATE":
        rx = "Implement Micro-Recovery: Increase inter-session buffer to 20 minutes; shift afternoon deep work to morning peak block."
    else:
        rx = "Maintain Flow Rhythm: System state nominal. Recommended to tackle highest cognitive difficulty problem sets today."

    return BurnoutPredictionResponse(
        user_id=features.user_id,
        burnout_probability=round(prob, 4),
        risk_tier=risk_tier,
        alert_triggered=(prob >= 0.65),
        top_driving_factors=drivers,
        prescriptive_action=rx
    )

@app.post("/api/v1/cognitive/debrief", response_model=JournalDebriefResponse, tags=["LLM & Qualitative"])
def debrief_journal_reflection(debrief: JournalDebriefInput):
    """
    Analyzes student/user debrief text using LLM synthesis patterns.
    Extracts cognitive distortions (CBT) and sentiment.
    """
    text = debrief.journal_text.lower()
    distortions = []

    # Cognitive Distortion Extraction Rules
    if any(k in text for k in ["impossible", "never", "ruined", "total failure", "disaster"]):
        distortions.append(CognitiveDistortionAnalysis(
            distortion_type="Catastrophizing & All-or-Nothing",
            evidence_snippet=debrief.journal_text,
            cognitive_reframe="Reframe absolute outcome: Progress is non-linear; single session struggle does not determine academic trajectory."
        ))

    if any(k in text for k in ["impostor", "not good enough", "everyone else is ahead"]):
        distortions.append(CognitiveDistortionAnalysis(
            distortion_type="Social Comparison & Impostor Distortion",
            evidence_snippet=debrief.journal_text,
            cognitive_reframe="Anchor on objective milestone metrics and 7-day focus progression rather than external perceptions."
        ))

    # Sentiment derivation
    if debrief.mood_score <= 2 or len(distortions) > 0:
        sentiment = "negative"
        cog_load = 0.82
        mentor_note = "High cognitive exhaustion detected. Prioritize nervous system down-regulation before returning to distributed systems proofs."
    elif debrief.mood_score >= 4:
        sentiment = "positive"
        cog_load = 0.25
        mentor_note = "Strong self-efficacy and flow resonance. Optimal day to push deeper into challenging conceptual models."
    else:
        sentiment = "neutral"
        cog_load = 0.50
        mentor_note = "Consistent baseline performance. Keep monitoring mid-afternoon energy levels to sustain consistency."

    # Try Gemini LLM cognitive synthesis if API key is configured
    gemini_reframe = call_gemini_api(
        prompt=f"Analyze this student learning journal reflection: '{debrief.journal_text}'. User mood score: {debrief.mood_score}/5, energy: {debrief.energy_level}/5. Provide a constructive, psychologically grounded 2-sentence cognitive reframe and actionable suggestion.",
        system_prompt="You are a Principal Cognitive Systems and Learning Scientist. Provide empathetic, evidence-based cognitive reframing for knowledge workers and computer science students."
    )

    return JournalDebriefResponse(
        user_id=debrief.user_id,
        sentiment_polarity=sentiment,
        cognitive_load_index=cog_load,
        detected_distortions=distortions,
        mentorship_feedback=gemini_reframe if gemini_reframe else mentor_note
    )

@app.post("/api/v1/telemetry/digest", response_model=WeeklyDigestResponse, tags=["LLM & Synthesis"])
def synthesize_weekly_digest(req: WeeklyDigestRequest):
    """Generates an executive natural-language briefing for NextOmni weekly review."""
    summary = (
        f"Weekly Cognitive Audit for {req.user_id}: Completed {req.total_focus_hours:.1f} total hours "
        f"with a {req.deep_work_percentage:.1f}% Deep Work allocation. Habit sustainability averaged "
        f"{req.habit_completion_rate:.1f}%, resolving {req.urgent_tasks_completed} critical academic deliverables."
    )

    achievements = [
        f"Protected {req.total_focus_hours * (req.deep_work_percentage / 100):.1f} hours of zero-distraction deep work.",
        f"Delivered {req.urgent_tasks_completed} high-weight course milestones."
    ]

    vulnerabilities = []
    if req.deep_work_percentage < 55.0:
        vulnerabilities.append("Deep work ratio fell below the 55% target; high fragmentation observed.")
    if req.urgent_tasks_missed > 0:
        vulnerabilities.append(f"{req.urgent_tasks_missed} tasks breached scheduled deadlines.")
    if req.habit_completion_rate < 75.0:
        vulnerabilities.append("Habit decay detected in evening wellness and meditation routines.")

    sprint_actions = [
        "Block 09:00 - 11:30 daily for deep work before checking email or chat.",
        "Implement 10-minute buffer after 14:00 to blunt postprandial circadian dip."
    ]

    return WeeklyDigestResponse(
        user_id=req.user_id,
        executive_summary=summary,
        key_achievements=achievements,
        vulnerabilities_detected=vulnerabilities,
        prescriptive_sprint_adjustments=sprint_actions
    )
