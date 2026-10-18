"""
NextOmni Analytics Intelligence - Master CLI Runner
Automates seed generation, model retraining, automated test execution, and FastAPI microservice startup.
"""

import sys
import subprocess
import os
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_step(description, command):
    print(f"\n==========================================")
    print(f"[*] {description}")
    print(f"==========================================")
    result = subprocess.run(command, cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"[!] Step failed with code {result.returncode}")
        sys.exit(result.returncode)

def main():
    parser = argparse.ArgumentParser(description="NextOmni Analytics Intelligence CLI Controller")
    parser.add_argument("--test", action="store_true", help="Run automated regression test suite")
    parser.add_argument("--train-only", action="store_true", help="Generate seeds and train ML pipeline without starting server")
    parser.add_argument("--serve-only", action="store_true", help="Start FastAPI microservice immediately")
    parser.add_argument("--verify-all", action="store_true", help="Run end-to-end telemetry generation, ML training, and unit tests")
    parser.add_argument("--port", type=int, default=8000, help="Port to run FastAPI service on (default: 8000)")
    args = parser.parse_args()

    print("""
    +-----------------------------------------------------------+
    |       NEXTOMNI ANALYTICS INTELLIGENCE ENGINE              |
    |   Predictive Telemetry, Circadian ML & GenAI Synthesis    |
    +-----------------------------------------------------------+
    """)

    if args.test:
        run_step("Running Automated Regression Test Suite", [sys.executable, "-m", "unittest", "discover", "tests"])
        return

    if args.serve_only:
        print(f"\n[*] Launching FastAPI Microservice on http://127.0.0.1:{args.port} ...")
        subprocess.run([sys.executable, "-m", "uvicorn", "python_ml.llm_cognitive_service:app", "--host", "127.0.0.1", "--port", str(args.port), "--reload"], cwd=BASE_DIR)
        return

    # Telemetry generation & ML training
    run_step("1. Generating 180-Day Quantified-Self Telemetry Seeds", [sys.executable, os.path.join("data", "seed_telemetry_generator.py")])
    run_step("2. Training Gradient Boosting Burnout Model & Evaluating CV", [sys.executable, os.path.join("python_ml", "ml_pipeline.py")])

    if args.verify_all:
        run_step("3. Running Automated Regression Tests", [sys.executable, "-m", "unittest", "discover", "tests"])
        print("\n[OK] All verification checks passed successfully!")
        return

    if args.train_only:
        print("\n[OK] Seed generation and model training completed successfully.")
        return

    # Default flow: launch server after training
    print(f"\n[*] 3. Launching FastAPI Microservice on http://127.0.0.1:{args.port} ...")
    subprocess.run([sys.executable, "-m", "uvicorn", "python_ml.llm_cognitive_service:app", "--host", "127.0.0.1", "--port", str(args.port), "--reload"], cwd=BASE_DIR)

if __name__ == "__main__":
    main()
