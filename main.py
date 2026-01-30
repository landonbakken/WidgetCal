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

DATA_FILE = Path("data.pkl")
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

TODAY = datetime.today().strftime("%a")

#load the tasks to a file
def load_tasks():
    if DATA_FILE.exists():
        with open("data.pkl", "rb") as f:
            return pickle.load(f)
    return {day: [] for day in DAYS}

#save the tasks to a file
def save_tasks(data):
    with open("data.pkl", "wb") as f:
        pickle.dump(data, f)

class WeeklyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(600)
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
            label.setStyleSheet("font-weight: bold;")
            if day == TODAY:
                label.setStyleSheet("font-weight: bold; background: rgba(255, 182, 193, 200);")
            label.clicked.connect(lambda _, d=day: self.setFocus(d))
            label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            day_layout.addWidget(label)

            #scrollable task area
            task_container = QWidget()
            task_layout = QVBoxLayout(task_container)
            task_layout.setContentsMargins(0, 0, 0, 0)
            task_layout.setSpacing(2)
            
            #add tasks
            for task in self.tasks[day]:
                taskCheckbox = QCheckBox(task["Description"])
                taskCheckbox.setChecked(False)
                taskCheckbox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                task_layout.addWidget(taskCheckbox)
                task["Widget"] = taskCheckbox
            
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

        self.setStyleSheet("""
            QWidget {
                background: rgba(255, 182, 193, 25);
                color: white;
                border-radius: 12px;
                padding: 10px;
            }
        """)
        
    def addTask(self, day):
        taskLayout = self.taskLayouts[day]
        taskCheckbox = QCheckBox("New Task")
        taskCheckbox.setChecked(False)
        taskLayout.addWidget(taskCheckbox)
        
        self.tasks[day].append({
            "Description": "New Task",
            "Done": False,
            "Widget": taskCheckbox
        })
        self.save()
        self.setFocus(day)
        
    def setFocus(self, day):
        dayIndex = DAYS.index(day)
        for i in range(len(DAYS)):
            self.layout().setStretch(i, 1)
        
        self.layout().setStretch(dayIndex, 4)
    
    def save(self):
        for dayTasks in self.tasks.values():
            for task in dayTasks:
                task.pop("Widget", None)
        save_tasks(self.tasks)
                

app = QApplication(sys.argv)
w = WeeklyWidget()
w.show()
sys.exit(app.exec())
