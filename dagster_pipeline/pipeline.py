import subprocess
import os
import sys
from dagster import op, job, Definitions, ScheduleDefinition

# --- PATH CONFIGURATION ---
# This points to the medical-telegram-warehouse directory (root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@op(description="Runs the Telegram scraper to fetch new messages and images.")
def scrape_telegram_data():
    """Operation 1: Scrape raw data from Telegram."""
    # Correct path to scraper.py relative to the root
    script_path = os.path.join(BASE_DIR, "scripts", "scraper.py")
    
    # We run the command from the BASE_DIR so that .env and src/ are found correctly
    subprocess.run(
        [sys.executable, script_path, "--path", "data", "--limit", "100"], 
        cwd=BASE_DIR, 
        check=True
    )
    return "Scrape Complete"

@op(description="Loads scraped JSON/CSV data into the PostgreSQL raw schema.")
def load_raw_to_postgres(wait_for_scrape):
    """Operation 2: Load text data to Database."""
    script_path = os.path.join(BASE_DIR, "scripts", "load_raw_data.py")
    subprocess.run(
        [sys.executable, script_path], 
        cwd=BASE_DIR, 
        check=True
    )
    return "Ingestion Complete"

@op(description="Runs YOLOv8 object detection on retrieved images.")
def run_yolo_enrichment(wait_for_scrape):
    """Operation 3: AI Object Detection & Loading."""
    yolo_script = os.path.join(BASE_DIR, "src", "yolo_detect.py")
    load_yolo_script = os.path.join(BASE_DIR, "scripts", "load_yolo_postgres.py")

    # 1. Run Detection
    subprocess.run([sys.executable, yolo_script], cwd=BASE_DIR, check=True)
    # 2. Load Detections to Postgres
    subprocess.run([sys.executable, load_yolo_script], cwd=BASE_DIR, check=True)
    return "YOLO Enrichment Complete"

@op(description="Executes dbt models to transform raw data into cleaned marts.")
def run_dbt_transformations(wait_for_ingestion, wait_for_yolo):
    """Operation 4: dbt Transformation."""
    # dbt project is in the /medical_warehouse directory
    dbt_dir = os.path.join(BASE_DIR, "medical_warehouse")
    
    # We execute dbt from the medical_warehouse directory where dbt_project.yml exists
    subprocess.run(["dbt", "run"], cwd=dbt_dir, check=True)
    return "Transformations Complete"

# --- JOB GRAPH ---

@job
def medical_warehouse_pipeline():
    # Define dependencies strictly
    scraped = scrape_telegram_data()
    
    # Ingestion and YOLO run after scraping
    raw_loaded = load_raw_to_postgres(scraped)
    yolo_done = run_yolo_enrichment(scraped)
    
    # Final dbt transformations wait for both database loads to finish
    run_dbt_transformations(raw_loaded, yolo_done)

# --- DEFINITIONS ---

defs = Definitions(
    jobs=[medical_warehouse_pipeline],
    schedules=[
        ScheduleDefinition(
            job=medical_warehouse_pipeline,
            cron_schedule="0 0 * * *",  # Daily at midnight
        )
    ],
)