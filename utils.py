import os
import sys
import json
import psutil
from pathlib import Path
from datetime import datetime

# --- Constants & Paths ---
DATA_DIR = Path(os.getenv("APPDATA", ".")) / "WidgetCal"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TASK_FILE = DATA_DIR / "tasks.json"
NOTE_FILE = DATA_DIR / "notes.json"
CONFIG_FILE = DATA_DIR / "config.json"

DEFAULT_COLUMNS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
CLEAR = "0, 0, 0, 0"
TODAY = datetime.today().strftime("%a")

DEFAULT_CONFIG = {
    "COLUMNS": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "BACKGROUND": "224, 123, 201, 75",
    "HIGHLIGHT": "224, 123, 201, 120",
    "CHECKED_TEXT": "30, 30, 30, 255",
    "UNCHECKED_TEXT": "0, 0, 0, 255",
    "UNCHECKED_BACKGROUND": "224, 123, 201, 75",
    "CHECKED_BACKGROUND": "224, 123, 201, 20",
    "DAY_LABEL_TODAY_BACKGROUND": "230, 160, 150, 75",
    "DAY_LABEL_TEXT": "0, 0, 0, 255",
    "ADD_TASK_TEXT": "0, 0, 0, 255",
    "NOTES_TEXT": "0, 0, 0, 255",
    "POPUP_BACKGROUND": "200, 130, 120, 255",
    "POPUP_BUTTON": "230, 160, 150, 75",
    "POPUP_BUTTON_HIGHLIGHT": "230, 160, 150, 130",
    "LEFT_MARGIN": 30,
    "RIGHT_MARGIN": 300,
    "TOP_MARGIN": 30,
    "BOTTOM_MARGIN": 600,
    "FOCUSED_SCALE": 2,
    "NOTES_TASKS_RATIO": 1,
    "DEFAULT_SCREEN": 0
}

config = {}

# --- Helper Functions ---
def updateInstanceOnly():
    current_pid = os.getpid()
    program_name = os.path.basename(sys.argv[0])
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['pid'] != current_pid:
                if proc.info['name'] == program_name or (proc.info['exe'] and os.path.basename(proc.info['exe']) == program_name):
                    proc.terminate()
                    proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

def loadConfig():
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)

    with open(CONFIG_FILE, "r") as file:
        loaded_config = json.load(file)
        config.clear()
        config.update(loaded_config)
    
    # NEW FIX: Explicitly pull COLUMNS out of 'unused' if it got trapped
    if "unused" in config and "COLUMNS" in config["unused"]:
        config["COLUMNS"] = config["unused"].pop("COLUMNS")
    
    # Migration: ACTIVE_DAYS to COLUMNS
    if "ACTIVE_DAYS" in config:
        config["COLUMNS"] = config.pop("ACTIVE_DAYS")
        saveConfig()
        
    for key in DEFAULT_CONFIG.keys():
        if key not in config.keys():
            config[key] = DEFAULT_CONFIG[key]
            saveConfig()
            
    # Clean up 'unused'
    if "unused" in config and not config["unused"]:
        del config["unused"]
        saveConfig()

def saveConfig():
    # Ensure COLUMNS is moved out of unused if it somehow got there
    if "unused" in config and "COLUMNS" in config["unused"]:
        config["COLUMNS"] = config["unused"].pop("COLUMNS")
    
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

def load_tasks():
    if TASK_FILE.exists():
        with open(TASK_FILE, "r") as f:
            return json.load(f)
    return {}

def load_notes():
    if NOTE_FILE.exists():
        with open(NOTE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_tasks(data):
    with open(TASK_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_notes(data):
    with open(NOTE_FILE, "w") as f:
        json.dump(data, f, indent=4)