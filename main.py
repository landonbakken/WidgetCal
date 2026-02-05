import sys
from pathlib import Path
from PySide6.QtGui import QGuiApplication, QTextOption
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QCheckBox, QPushButton, QSizePolicy, QScrollArea, 
    QLineEdit, QTextEdit, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, QFileSystemWatcher
import pickle
from datetime import datetime
import os
import shutil
import psutil
import json

def updateInstanceOnly():
    current_pid = os.getpid()
    program_name = os.path.basename(sys.argv[0])

    # Look for other running instances
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            # Check if it's the same program but not this process
            if proc.info['pid'] != current_pid:
                if proc.info['name'] == program_name or (proc.info['exe'] and os.path.basename(proc.info['exe']) == program_name):
                    print(f"Found old instance (PID {proc.info['pid']}), terminating it...")
                    proc.terminate()
                    proc.wait(timeout=5)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

focusedStretch = 2
unfocusedStretch = 1

#data paths
DATA_DIR = Path(os.getenv("APPDATA")) / "WidgetCal"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TASK_FILE = DATA_DIR / "tasks.json"
NOTE_FILE = DATA_DIR / "notes.json"
CONFIG_FILE = DATA_DIR / "config.json"

#things to migrate from
OLD_TASK_FILE = DATA_DIR / "tasks.pkl"
OLD_NOTE_FILE = DATA_DIR / "notes.pkl"

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
CLEAR = "0, 0, 0, 0"

TODAY = datetime.today().strftime("%a")

def loadConfig():
    global config
    
    if not CONFIG_FILE.exists():
        defualtConfig = {
                "BACKGROUND": "224, 123, 201, 75",
                "HIGHLIGHT": "224, 123, 201, 120",
                
                "CHECKED_TEXT": "30, 30, 30, 255",
                "UNCHECKED_TEXT": "0, 0, 0, 255",
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

                "DEFAULT_SCREEN": 0
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(defualtConfig, f, indent=4)

    with open(CONFIG_FILE, "r") as file:
        config = json.load(file)

#load the tasks to a file
def load_tasks():
    #migrate
    if OLD_TASK_FILE.exists():
        with open(OLD_TASK_FILE, "rb") as f:
            data = pickle.load(f)
            save_tasks(data)
        os.remove(OLD_TASK_FILE)
    
    #parse data
    if TASK_FILE.exists():
        with open(TASK_FILE, "rb") as f:
            return json.load(f)
        
    #nothing exists
    return {day: [] for day in DAYS}

def load_notes():
    #migrate
    if OLD_NOTE_FILE.exists():
        with open(OLD_NOTE_FILE, "rb") as f:
            data = pickle.load(f)
            save_notes(data)
        os.remove(OLD_NOTE_FILE)
    
    if NOTE_FILE.exists():
        with open(NOTE_FILE, "rb") as f:
            return json.load(f)
    return {day: "" for day in DAYS}

#saveTasks the tasks to a file
def save_tasks(data):
    with open(TASK_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_notes(data):
    with open(NOTE_FILE, "w") as f:
        json.dump(data, f, indent=4)
        
class NoteWidget(QWidget):
    def __init__(self, parent, day, text):
        super().__init__()

        self.parent = parent
        self.day = day
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.editor = QTextEdit()
        self.editor.setAcceptRichText(False)   # plain text only
        self.editor.setWordWrapMode(QTextOption.WordWrap)
        self.editor.setLineWrapMode(QTextEdit.WidgetWidth)
        self.editor.setPlainText(text)
        
        self.editor.focusInEvent = self.startEditing
        self.editor.focusOutEvent = self.endEditing

        layout.addWidget(self.editor)
        
    def startEditing(self, event):
        self.parent.setFocus(self.day)
        QTextEdit.focusInEvent(self.editor, event)
        
    def endEditing(self, event):
        self.parent.notes[self.day] = self.editor.toPlainText()
        self.parent.saveNotes()
        QTextEdit.focusOutEvent(self.editor, event)
        
class TaskWidget(QWidget):
    def __init__(self, parent, description, done, day, new=False):
        super().__init__()
        self.parent = parent
        self.description = description
        self.done = done
        
        self.day = day

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        #checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.done)
        self.checkbox.stateChanged.connect(self.updateChecked)
        layout.addWidget(self.checkbox)

        #editable part
        self.editor = QLineEdit(self.description)
        self.editor.setReadOnly(True)
        self.editor.setCursorPosition(0)
        self.editor.setFrame(False)
        self.editor.editingFinished.connect(self.finishEdit)
        
        #click to edit
        self.editor.mousePressEvent = self.startEdit
        layout.addWidget(self.editor)
        
        self.deleteButton = QPushButton("X")
        self.deleteButton.clicked.connect(self.deleteTask)
        layout.addWidget(self.deleteButton)

        self.updateStylesheet()
        
        if new:
            QTimer.singleShot(0, self.startEdit)

    def startEdit(self, event=None):
        self.parent.setFocus(self.day)
        self.editor.setReadOnly(False)
        self.editor.setCursorPosition(len(self.editor.text()))
        self.editor.setFocus()

    def finishEdit(self):
        self.editor.setReadOnly(True)
        self.editor.setCursorPosition(0)
        self.description = self.editor.text()
        self.parent.saveTasks()
    
    def deleteTask(self):
        self.parent.removeTask(self, self.day)

    def updateChecked(self):
        self.task["Done"] = self.checkbox.isChecked()
        self.updateStylesheet()
        self.parent.saveTasks()

    def updateStylesheet(self):
        if self.checkbox.isChecked():
            self.setStyleSheet(f"""
                QLineEdit {{
                    color: rgba({config["CHECKED_TEXT"]});
                    background: rgba({config["CHECKED_BACKGROUND"]});
                }}
                QCheckBox {{
                    color: rgba({config["CHECKED_TEXT"]});
                    background: rgba({config["CHECKED_BACKGROUND"]});
                }}
            """)
        else:
            #just use the inharited one
            self.setStyleSheet("")
            
    def toData(self):
        data = {
            "Description": self.description,
            "Done": self.done
        }
        
        return data


class WeeklyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.taskLayouts = {}
        self.taskDatas = load_tasks()
        self.notes = load_notes()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowStaysOnBottomHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QHBoxLayout(self)
        layout.setSpacing(5)

        self.tasks = {day: [] for day in DAYS}
        for day in DAYS:
            #vbox for each day
            dayWidget = QWidget()
            day_layout = QVBoxLayout(dayWidget)
            dayWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
            day_layout.setContentsMargins(0, 0, 0, 0)
            day_layout.setSpacing(5)
            
            #day label
            dayLabel = QPushButton(day)
            if day == TODAY:
                dayLabel.setProperty("role", "dayLabel_today")
            else:
                dayLabel.setProperty("role", "dayLabel")
            dayLabel.clicked.connect(lambda _, d=day: self.setFocus(d))
            dayLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            dayLabel.setContextMenuPolicy(Qt.CustomContextMenu)
            dayLabel.customContextMenuRequested.connect(lambda _, d=day: self.rightClickDay(d))
            day_layout.addWidget(dayLabel)
            
            
            notes = NoteWidget(self, day, self.notes[day])
            day_layout.addWidget(notes, 1)

            #scrollable task area
            task_container = QWidget()
            task_layout = QVBoxLayout(task_container)
            task_layout.setContentsMargins(0, 0, 0, 0)
            task_layout.setSpacing(2)
            
            #add tasks
            for taskData in self.taskDatas[day]:
                task = TaskWidget(self, taskData["Description"], taskData["Done"], day)
                self.tasks[day].append(task)
                task_layout.addWidget(task)
            
            #squish things to the top
            task_layout.addStretch()
            
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(task_container)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
            day_layout.addWidget(scroll, 1)
                
            #button to add a task
            addTaskButton = QPushButton("+")
            addTaskButton.clicked.connect(lambda _, d=day: self.addTask(d))
            addTaskButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            day_layout.addWidget(addTaskButton)
            addTaskButton.setProperty("role", "addTask")

            #reference for modifications
            self.taskLayouts[day] = task_layout
            
            layout.addWidget(dayWidget)
            
            self.setFocus(TODAY)
            
    def updatePos(self):
        screens = QGuiApplication.screens()
        screenIndex = min(config["DEFAULT_SCREEN"], len(screens) - 1)

        screen = screens[screenIndex]
        geo = screen.availableGeometry()
        
        height = geo.height() - config["TOP_MARGIN"] - config["BOTTOM_MARGIN"]
        width = geo.width() - config["LEFT_MARGIN"] - config["RIGHT_MARGIN"]
        
        #size
        self.resize(width, height)

        # center on screen
        x = config["LEFT_MARGIN"]
        y = config["TOP_MARGIN"]

        self.move(x, y)
    
    def updateConfig(self):
        #screenPos
        self.updatePos()
        self.updateStylesheet()
        
        for day in DAYS:
            for task in self.tasks[day]:
                task.updateStylesheet()
    
    def showEvent(self, event):
        super().showEvent(event)
        self.updateConfig()
    
    def updateStylesheet(self):
        #actual stylesheet
        self.setStyleSheet(f"""
            QWidget {{
                background: rgba({CLEAR});
                border-radius: 12px;
                padding: 5px;
            }}
            
            QTextEdit{{
                background: rgba({config["BACKGROUND"]});
                color: rgba({config["NOTES_TEXT"]});
            }}
            
            QPushButton:hover {{
                background: rgba({config["HIGHLIGHT"]});
            }}
            
            QPushButton[role="addTask"] {{
                background: rgba({config["BACKGROUND"]});
                color: rgba({config["ADD_TASK_TEXT"]});
                font-weight: bold;
            }}
            
            QPushButton[role="dayLabel"]{{
                font-weight: bold;
                color: rgba({config["DAY_LABEL_TEXT"]});
                background: rgba({config["BACKGROUND"]})
            }}
            
            QPushButton[role="dayLabel_today"]{{
                font-weight: bold;
                color: rgba({config["DAY_LABEL_TEXT"]});
                background: rgba({config["DAY_LABEL_TODAY_BACKGROUND"]})
            }}
            
            QScrollArea{{
                background: rgba({config["BACKGROUND"]});
            }}
            
            QLineEdit {{
                color: rgba({config["UNCHECKED_TEXT"]});
                background: rgba({CLEAR});
            }}
            
            QCheckBox {{
                color: {config["UNCHECKED_TEXT"]};
                background: rgba({CLEAR});
                spacing: 0px;
                padding: 1px;
                margin: 0px;
            }}
            
            QCheckBox::indicator {{
                margin: 0px;
                padding: 0px;
            }}
        """)
        
    def rightClickDay(self, day):
        popup = FloatingPopup(self, day)

        # center popup over main widget
        center = self.mapToGlobal(self.rect().center())
        popup.move(center - popup.rect().center())

        popup.show()
        
    def clearDay(self, day):
        for task in self.tasks[day]:
            self.removeTask(task, day)
        
        self.saveTasks()
        
    def removeTask(self, task, day):
        #visually clear
        self.taskLayouts[day].removeWidget(task)
        task.setParent(None)
        task.deleteLater()
        
        #clear data
        self.tasks[day].remove(task)
        
        self.saveTasks()
        
    def clearWeek(self):
        for day in DAYS:
            self.clearDay(day)
        
    def addTask(self, day):
        task = TaskWidget(self, "", False, day, True)
        self.tasks[day].append(task)
        
        #put right above the stretch so it's at the top
        taskLayout = self.taskLayouts[day]
        taskLayout.insertWidget(taskLayout.count() - 1, task)
        
        #update
        self.saveTasks()
        self.setFocus(day)
        
    def setFocus(self, day):
        dayIndex = DAYS.index(day)
        for i in range(len(DAYS)):
            self.layout().setStretch(i, unfocusedStretch)
        
        self.layout().setStretch(dayIndex, focusedStretch)
    
    def saveTasks(self):
        tasksToSave = {day: [] for day in DAYS}
        for day in DAYS:
            for task in self.tasks[day]:
                data = task.toData()
                tasksToSave[day].append(data)
        save_tasks(tasksToSave)
    
    def saveNotes(self):
        save_notes(self.notes)

class FloatingPopup(QWidget):
    def __init__(self, parent, day):
        super().__init__(parent)
        self.parent = parent
        self.day = day

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(300, 125)
        
        #background
        bg = QWidget(self)
        bg.setGeometry(self.rect())
    
        layout = QGridLayout(bg)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        clearWeek = QPushButton("Clear Week")
        clearDay = QPushButton("Clear Day")
        updateConfig = QPushButton("Update Config")
        cancel = QPushButton("Close")

        cancel.clicked.connect(self.close)
        clearWeek.clicked.connect(self.clearWeek)
        clearDay.clicked.connect(self.clearDay)

        layout.addWidget(clearWeek, 0, 0)
        layout.addWidget(clearDay, 0, 1)
        layout.addWidget(cancel, 1, 0)
    
        self.setStyleSheet(f"""
            QWidget{{
                background: rgba({config["POPUP_BACKGROUND"]});
                border-radius: 10px;
            }}
            QPushButton {{
                background: rgba({config["POPUP_BUTTON"]});
                border-radius: 8px;
                padding: 6px;
            }}
            QPushButton:hover {{
                background: rgba({config["POPUP_BUTTON_HIGHLIGHT"]});
            }}
        """)
        
    def clearWeek(self):
        self.parent.clearWeek()
        self.close()
        
    def clearDay(self):
        self.parent.clearDay(self.day)
        self.close()

updateInstanceOnly()
loadConfig()

watcher = QFileSystemWatcher()
watcher.addPath(str(CONFIG_FILE))
def on_config_changed(path):
    loadConfig()
    w.updateConfig()
watcher.fileChanged.connect(on_config_changed)

app = QApplication(sys.argv)
w = WeeklyWidget()
w.show()
sys.exit(app.exec())
