\"\"\"
NextOmni Analytics Intelligence - Master CLI Runner
Automates seed generation, model retraining, and FastAPI microservice startup.
\"\"\"

import sys
import subprocess
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_step(description, command):
    print(f"\n==========================================")
    print(f"[*] {description}")
    print(f"==========================================")
    result = subprocess.run(command, cwd=BASE_DIR, shell=True)
    if result.returncode != 0:
        print(f"[!] Step failed with code {result.returncode}")
        sys.exit(result.returncode)

def main():
    print(\"""
    ╔═══════════════════════════════════════════════════════════╗
    ║       NEXTOMNI ANALYTICS INTELLIGENCE ENGINE              ║
    ║   Predictive Telemetry, Circadian ML & GenAI Synthesis    ║
    ╚═══════════════════════════════════════════════════════════╝
    \""")
    
    # Step 1: Generate / Validate seed telemetry
    run_step("1. Generating 180-Day Quantified-Self Telemetry Seeds", [sys.executable, os.path.join("data", "seed_telemetry_generator.py")])

    # Step 2: Run ML pipeline & serialize model
    run_step("2. Training Gradient Boosting Burnout Model & Evaluating CV", [sys.executable, os.path.join("python_ml", "ml_pipeline.py")])

    # Step 3: Launch FastAPI service
    print("\n[*] 3. Launching FastAPI Microservice on http://127.0.0.1:8000 ...")
    subprocess.run([sys.executable, "-m", "uvicorn", "python_ml.llm_cognitive_service:app", "--host", "127.0.0.1", "--port", "8000", "--reload"], cwd=BASE_DIR)

if __name__ == "__main__":
    main()
