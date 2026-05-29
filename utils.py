import os
import sys
import json
import pickle
import psutil
from pathlib import Path
from datetime import datetime

# --- Constants & Paths ---
DATA_DIR = Path(os.getenv("APPDATA")) / "WidgetCal"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TASK_FILE = DATA_DIR / "tasks.json"
NOTE_FILE = DATA_DIR / "notes.json"
CONFIG_FILE = DATA_DIR / "config.json"

OLD_TASK_FILE = DATA_DIR / "tasks.pkl"
OLD_NOTE_FILE = DATA_DIR / "notes.pkl"

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
CLEAR = "0, 0, 0, 0"
TODAY = datetime.today().strftime("%a")

DEFAULT_CONFIG = {
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

# Global config dictionary mutated by loadConfig
config = {}

# --- Helper Functions ---
def updateInstanceOnly():
    current_pid = os.getpid()
    program_name = os.path.basename(sys.argv[0])

    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['pid'] != current_pid:
                if proc.info['name'] == program_name or (proc.info['exe'] and os.path.basename(proc.info['exe']) == program_name):
                    print(f"Found old instance (PID {proc.info['pid']}), terminating it...")
                    proc.terminate()
                    proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

def loadConfig():
    # create
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)

    # read and update global dict (prevents breaking imports)
    with open(CONFIG_FILE, "r") as file:
        loaded_config = json.load(file)
        config.clear()
        config.update(loaded_config)
        
    # add missing keys
    for key in DEFAULT_CONFIG.keys():
        if key not in config.keys():
            config[key] = DEFAULT_CONFIG[key]
            with open(CONFIG_FILE, "w") as file:
                json.dump(config, file, indent=4)
            print("Added", key, "to the config")
            
    # show unused keys
    keys = list(config.keys()).copy()
    if "unused" not in keys:
        config["unused"] = {}
    
    for key in keys:
        if key not in DEFAULT_CONFIG.keys() and key != "unused":
            config["unused"][key] = config[key]
            del config[key]
            with open(CONFIG_FILE, "w") as file:
                json.dump(config, file, indent=4)
            print("Removed", key, "from the config")

def load_tasks():
    if OLD_TASK_FILE.exists():
        with open(OLD_TASK_FILE, "rb") as f:
            data = pickle.load(f)
            save_tasks(data)
        os.remove(OLD_TASK_FILE)
    
    if TASK_FILE.exists():
        with open(TASK_FILE, "rb") as f:
            return json.load(f)
            
    return {day: [] for day in DAYS}

def load_notes():
    if OLD_NOTE_FILE.exists():
        with open(OLD_NOTE_FILE, "rb") as f:
            data = pickle.load(f)
            save_notes(data)
        os.remove(OLD_NOTE_FILE)
    
    if NOTE_FILE.exists():
        with open(NOTE_FILE, "rb") as f:
            return json.load(f)
            
    return {day: "" for day in DAYS}

def save_tasks(data):
    with open(TASK_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_notes(data):
    with open(NOTE_FILE, "w") as f:
        json.dump(data, f, indent=4)