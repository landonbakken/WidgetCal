from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy, QScrollArea
from PySide6.QtCore import Qt
from utils import load_tasks, load_notes, save_tasks, save_notes, DAYS, TODAY, CLEAR, config
from widgets import NoteWidget, TaskWidget, FloatingPopup

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
            dayWidget = QWidget()
            day_layout = QVBoxLayout(dayWidget)
            dayWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
            day_layout.setContentsMargins(0, 0, 0, 0)
            day_layout.setSpacing(5)
            
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
            
            notes_widget = NoteWidget(self, day, self.notes[day])
            day_layout.addWidget(notes_widget, config["NOTES_TASKS_RATIO"])

            task_container = QWidget()
            task_layout = QVBoxLayout(task_container)
            task_layout.setContentsMargins(0, 0, 0, 0)
            task_layout.setSpacing(2)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(task_container)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
            day_layout.addWidget(scroll, 1)
                
            addTaskButton = QPushButton("+")
            addTaskButton.clicked.connect(lambda _, d=day: self.addTask(d))
            addTaskButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            day_layout.addWidget(addTaskButton)
            addTaskButton.setProperty("role", "addTask")

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
        
        self.resize(width, height)

        x = config["LEFT_MARGIN"]
        y = config["TOP_MARGIN"]

        self.move(x, y)
    
    def updateConfig(self):
        self.updatePos()
        self.updateStylesheet()
        
        for day in DAYS:
            for task in self.tasks[day]:
                task.updateStylesheet()
                
    def addExistingTasks(self):
        for day in DAYS:
            taskLayout = self.taskLayouts[day]
            
            for taskData in self.taskDatas[day]:
                task = TaskWidget(self, taskData["Description"], taskData["Done"], day)
                self.tasks[day].append(task)
                taskLayout.addWidget(task)
            
            taskLayout.addStretch()
    
    def showEvent(self, event):
        super().showEvent(event)
        self.addExistingTasks()
        self.updateConfig()
    
    def updateStylesheet(self):
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
        """)
        
    def rightClickDay(self, day):
        popup = FloatingPopup(self, day)
        center = self.mapToGlobal(self.rect().center())
        popup.move(center - popup.rect().center())
        popup.show()
        
    def clearDay(self, day):
        for task in list(self.tasks[day]):
            self.removeTask(task, day)
        self.saveTasks()
        
    def removeTask(self, task, day):
        self.taskLayouts[day].removeWidget(task)
        task.setParent(None)
        task.deleteLater()
        self.tasks[day].remove(task)
        self.saveTasks()
        
    def clearWeek(self):
        for day in DAYS:
            self.clearDay(day)
        
    def addTask(self, day):
        task = TaskWidget(self, "", False, day, True)
        self.tasks[day].append(task)
        
        taskLayout = self.taskLayouts[day]
        taskLayout.insertWidget(taskLayout.count() - 1, task)
        
        self.saveTasks()
        self.setFocus(day)
        
    def setFocus(self, day):
        dayIndex = DAYS.index(day)
        for i in range(len(DAYS)):
            self.layout().setStretch(i, 1)
        
        self.layout().setStretch(dayIndex, config["FOCUSED_SCALE"])
    
    def saveTasks(self):
        tasksToSave = {day: [] for day in DAYS}
        for day in DAYS:
            for task in self.tasks[day]:
                tasksToSave[day].append(task.toData())
        save_tasks(tasksToSave)
    
    def saveNotes(self):
        save_notes(self.notes)
        
    def hideEvent(self, event):
        self.showNormal()
        self.raise_()
        self.activateWindow()
        super().hideEvent(event)