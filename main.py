import sys
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QCheckBox, QPushButton, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt
import pickle
from datetime import datetime
import os
import copy

focusedStretch = 10
unfocusedStretch = 1

DATA_DIR = Path(os.getenv("APPDATA")) / "Cal" #Path("data.pkl")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / "data.pkl"

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

TODAY = datetime.today().strftime("%a")

#load the tasks to a file
def load_tasks():
    if DATA_FILE.exists():
        with open(DATA_FILE, "rb") as f:
            return pickle.load(f)
    return {day: [] for day in DAYS}

#save the tasks to a file
def save_tasks(data):
    with open(DATA_FILE, "wb") as f:
        pickle.dump(data, f)

class WeeklyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(800, 400)
        self.taskLayouts = {}
        self.tasks = load_tasks()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowStaysOnBottomHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
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
            label = QPushButton(day)
            if day == TODAY:
                label.setStyleSheet("font-weight: bold; background: rgba(255, 182, 193, 200);")
            else:
                label.setStyleSheet("font-weight: bold;")
            label.clicked.connect(lambda _, d=day: self.setFocus(d))
            label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            label.setContextMenuPolicy(Qt.CustomContextMenu)
            label.customContextMenuRequested.connect(lambda _, d=day: self.rightClickDay(d))
            day_layout.addWidget(label)

            #scrollable task area
            task_container = QWidget()
            task_layout = QVBoxLayout(task_container)
            task_layout.setContentsMargins(0, 0, 0, 0)
            task_layout.setSpacing(2)
            
            #add tasks
            for task in self.tasks[day]:
                taskCheckbox = QCheckBox(task["Description"])
                taskCheckbox.setChecked(task["Done"])
                self.updateCheckboxColors(taskCheckbox)
                taskCheckbox.stateChanged.connect(lambda _, cb=taskCheckbox: self.updateChecked(cb))
                taskCheckbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                task_layout.addWidget(taskCheckbox)
                task["Widget"] = taskCheckbox
            
            task_layout.addStretch()
            
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(task_container)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
            #scroll.setFixedWidth(150)  # fixed width for each day column
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

        self.setStyleSheet("""
            QWidget {
                background: rgba(255, 182, 193, 25);
                color: white;
                border-radius: 12px;
                padding: 10px;
            }
            
            QPushButton:hover {
                background: rgba(255, 182, 193, 60);
            }
        """)
        
    def rightClickDay(self, day):
        popup = FloatingPopup(self, day)

        # center popup over main widget
        center = self.mapToGlobal(self.rect().center())
        popup.move(center - popup.rect().center())

        popup.show()
        
    def clearDay(self, day):
        print("Clear " + day)
        for task in self.tasks[day]:
            #visually clear
            taskWidget = task["Widget"]
            self.taskLayouts[day].removeWidget(taskWidget)
            taskWidget.setParent(None)
            taskWidget.deleteLater()
            
            #clear data
            self.tasks[day] = []
        
        self.save()
        
    def clearWeek(self):
        print("Clear week")
        for day in DAYS:
            self.clearDay(day)

        
    def updateChecked(self, checkbox):
        for day in DAYS:
            for task in self.tasks[day]:
                if task["Widget"] == checkbox:
                    task["Done"] = checkbox.isChecked()
                    
        self.updateCheckboxColors(checkbox)
        self.save()
    
    def updateCheckboxColors(self, checkbox):
        if checkbox.isChecked():
            checkbox.setStyleSheet("""
                background: rgba(255, 182, 193, 5);
                color: gray;
            }
            """)
        else:
            checkbox.setStyleSheet("""
                background: rgba(255, 182, 193, 25);
                color: white;
            }
            """)
        
    def addTask(self, day):
        taskLayout = self.taskLayouts[day]
        taskCheckbox = QCheckBox("New Task")
        taskCheckbox.setChecked(False)
        taskLayout.insertWidget(taskLayout.count() - 1, taskCheckbox)
        
        self.tasks[day].append({
            "Description": "New Task",
            "Done": False,
            "Widget": taskCheckbox
        })
        self
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
        
        # This is the "background" widget
        bg = QWidget(self)
        bg.setGeometry(self.rect())  # Fill the whole popup
    
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

        self.setStyleSheet("""
            QWidget{
                background: rgba(100, 60, 70, 255);
                border-radius: 14px;
            }
            QPushButton {
                background: rgba(255, 182, 193, 160);
                border-radius: 8px;
                padding: 6px;
            }
            QPushButton:hover {
                background: rgba(255, 182, 193, 220);
            }
        """)
        
    def clearWeek(self):
        self.parent.clearWeek()
        self.close()
        
    def clearDay(self):
        self.parent.clearDay(self.day)
        self.close()


app = QApplication(sys.argv)
w = WeeklyWidget()
w.show()
sys.exit(app.exec())
