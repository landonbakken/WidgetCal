import sys
from pathlib import Path
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QCheckBox, QPushButton, QSizePolicy, QScrollArea, 
    QLineEdit
)
from PySide6.QtCore import Qt, QTimer
import pickle
from datetime import datetime
import os
import shutil
import psutil

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

focusedStretch = 5
unfocusedStretch = 1

OLD_PATH = Path(os.getenv("APPDATA")) / "Cal"
OLD_DATA = OLD_PATH / "data.pkl"

DATA_DIR = Path(os.getenv("APPDATA")) / "WidgetCal" #Path("data.pkl")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / "data.pkl"

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

TODAY = datetime.today().strftime("%a")

BASE_COLOR = "150, 80, 70"
SECONDARY_COLOR = "230, 160, 150"
CLEAR = "0, 0, 0, 0"
BACKGROUND = BASE_COLOR + ", 50"
HIGHLIGHTED_WEAK = BASE_COLOR + ", 90"
HIGHLIGHTED_STRONG = BASE_COLOR + ", 150"
CHECKED = BASE_COLOR + ", 20"
POPUP_BACKGROUND = BASE_COLOR + ", 200"
POPUP_BUTTON = SECONDARY_COLOR + ", 50"
POPUP_BUTTON_HIGHLIGHT = SECONDARY_COLOR + ", 90"
CHECKED_TEXT = "gray"
UNCHECKED_TEXT = "white"
LABEL_TEXT = "black"

#load the tasks to a file
def load_tasks():
    #migrate
    if OLD_DATA.exists():
        shutil.move(OLD_DATA, DATA_FILE)
        os.rmdir(OLD_PATH)
    
    if DATA_FILE.exists():
        with open(DATA_FILE, "rb") as f:
            return pickle.load(f)
    return {day: [] for day in DAYS}

#save the tasks to a file
def save_tasks(data):
    with open(DATA_FILE, "wb") as f:
        pickle.dump(data, f)
        
class TaskWidget(QWidget):
    def __init__(self, parent, task, day):
        super().__init__()
        self.parent = parent
        self.task = task
        self.day = day
        
        task["Widget"] = self

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        #checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(task["Done"])
        self.checkbox.stateChanged.connect(self.updateChecked)
        layout.addWidget(self.checkbox)

        #editable part
        self.editor = QLineEdit(task["Description"])
        self.editor.setReadOnly(True)
        #self.editor.setCursorPosition(0)
        self.editor.setFrame(False)
        self.editor.editingFinished.connect(self.finishEdit)
        
        #click to edit
        self.editor.mousePressEvent = self.startEdit
        layout.addWidget(self.editor)

        self.updateStylesheet()
        
        if task["Description"] == "":
            QTimer.singleShot(0, self.startEdit)

    def startEdit(self, event=None):
        self.parent.setFocus(self.day)
        self.editor.setReadOnly(False)
        #self.editor.setCursorPosition(len(self.editor.text()))
        self.editor.setFocus()

    def finishEdit(self):
        self.editor.setReadOnly(True)
        #self.editor.setCursorPosition(0)
        
        if not self.editor.text().strip():
            #delete event since its empty
            self.parent.removeTask(self.task, self.day)
        else:
            self.task["Description"] = self.editor.text()
            self.parent.save()

    def updateChecked(self):
        self.task["Done"] = self.checkbox.isChecked()
        self.updateStylesheet()
        self.parent.save()

    def updateStylesheet(self):
        if self.checkbox.isChecked():
            self.setStyleSheet(f"""
                QLineEdit {{
                    color: {CHECKED_TEXT};
                    background: rgba({CHECKED});
                }}
                QCheckBox {{
                    color: {CHECKED_TEXT};
                    background: rgba({CHECKED});
                }}
            """)
        else:
            #just use the inharited one
            self.setStyleSheet("")


class WeeklyWidget(QWidget):
    def move_to_screen(self, index):
        screens = QGuiApplication.screens()
        index = min(index, len(screens) - 1)

        screen = screens[index]
        geo = screen.availableGeometry()

        # center on that monitor
        x = geo.x() + (geo.width() - self.width()) // 2
        y = geo.y() + (geo.height() - self.height()) // 2

        self.move(x, y)
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(1000, 400)
        self.taskLayouts = {}
        self.tasks = load_tasks()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowStaysOnBottomHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.move_to_screen(0)
        
        layout = QHBoxLayout(self)
        layout.setSpacing(5)

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
                dayLabel.setStyleSheet(f"""
                    QPushButton{{
                        font-weight: bold; 
                        background: rgba({HIGHLIGHTED_STRONG}); 
                        color: rgba({LABEL_TEXT});
                    }}
                """)
            else:
                dayLabel.setStyleSheet(f"""
                    QPushButton{{
                        font-weight: bold; 
                        background: rgba({BACKGROUND}); 
                        color: rgba({LABEL_TEXT});
                    }}
                """)
            dayLabel.clicked.connect(lambda _, d=day: self.setFocus(d))
            dayLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            dayLabel.setContextMenuPolicy(Qt.CustomContextMenu)
            dayLabel.customContextMenuRequested.connect(lambda _, d=day: self.rightClickDay(d))
            day_layout.addWidget(dayLabel)

            #scrollable task area
            task_container = QWidget()
            task_layout = QVBoxLayout(task_container)
            task_layout.setContentsMargins(0, 0, 0, 0)
            task_layout.setSpacing(2)
            
            #add tasks
            for task in self.tasks[day]:
                taskCheckbox = TaskWidget(self, task, day)
                task_layout.addWidget(taskCheckbox)
            
            #squish things to the top
            task_layout.addStretch()
            
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(task_container)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
            day_layout.addWidget(scroll)
                
            #button to add a task
            addTaskButton = QPushButton("+")
            addTaskButton.clicked.connect(lambda _, d=day: self.addTask(d))
            addTaskButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            day_layout.addWidget(addTaskButton)

            #reference for modifications
            self.taskLayouts[day] = task_layout
            
            layout.addWidget(dayWidget)
            
            self.setFocus(TODAY)
        
        self.setStyleSheet(f"""
            QWidget {{
                background: rgba({CLEAR});
                border-radius: 12px;
                padding: 5px;
            }}
            
            QPushButton:hover {{
                background: rgba({HIGHLIGHTED_WEAK});
            }}
            
            QPushButton {{
                background: rgba({BACKGROUND});
                color: rgba({LABEL_TEXT});
            }}
            
            QScrollArea{{
                background: rgba({BACKGROUND});
            }}
            QLineEdit {{
                color: {UNCHECKED_TEXT};
                background: rgba({CLEAR});
            }}
            QCheckBox {{
                color: {UNCHECKED_TEXT};
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
        
        self.save()
        
    def removeTask(self, task, day):
        #visually clear
        taskWidget = task["Widget"]
        self.taskLayouts[day].removeWidget(taskWidget)
        taskWidget.setParent(None)
        taskWidget.deleteLater()
        
        #clear data
        self.tasks[day] = []
        
    def clearWeek(self):
        for day in DAYS:
            self.clearDay(day)
        
    def addTask(self, day):
        dayTasks = self.tasks[day]
        dayTasks.append({
            "Description": "",
            "Done": False
        })
        
        taskCheckbox = TaskWidget(self, dayTasks[-1], day)
        taskLayout = self.taskLayouts[day]
        
        #put right above the stretch so it's at the top
        taskLayout.insertWidget(taskLayout.count() - 1, taskCheckbox)
        
        self.save()
        self.setFocus(day)
        
    def setFocus(self, day):
        dayIndex = DAYS.index(day)
        for i in range(len(DAYS)):
            self.layout().setStretch(i, unfocusedStretch)
        
        self.layout().setStretch(dayIndex, focusedStretch)
    
    def save(self):
        tasksToSave = {day: [] for day in DAYS}
        for day in DAYS:
            for task in self.tasks[day]:
                tasksToSave[day].append({
                    "Description": task["Description"],
                    "Done": task["Done"]
                })
        save_tasks(tasksToSave)
                

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
        self.setFixedSize(300, 50)
        
        #background
        bg = QWidget(self)
        bg.setGeometry(self.rect())
    
        layout = QHBoxLayout(bg)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        clearWeek = QPushButton("Clear Week")
        clearDay = QPushButton("Clear Day")
        cancel = QPushButton("Close")

        cancel.clicked.connect(self.close)
        clearWeek.clicked.connect(self.clearWeek)
        clearDay.clicked.connect(self.clearDay)

        layout.addWidget(clearWeek)
        layout.addWidget(clearDay)
        layout.addWidget(cancel)

        self.setStyleSheet(f"""
            QWidget{{
                background: rgba({POPUP_BACKGROUND});
                border-radius: 10px;
            }}
            QPushButton {{
                background: rgba({POPUP_BUTTON});
                border-radius: 8px;
                padding: 6px;
            }}
            QPushButton:hover {{
                background: rgba({POPUP_BUTTON_HIGHLIGHT});
            }}
        """)
        
    def clearWeek(self):
        self.parent.clearWeek()
        self.close()
        
    def clearDay(self):
        self.parent.clearDay(self.day)
        self.close()

updateInstanceOnly()
app = QApplication(sys.argv)
w = WeeklyWidget()
w.show()
sys.exit(app.exec())
