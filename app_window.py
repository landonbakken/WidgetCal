from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy, QScrollArea
from PySide6.QtCore import Qt
from utils import load_tasks, load_notes, save_tasks, save_notes, TODAY, CLEAR, config
from widgets import NoteWidget, TaskWidget, TaskListContainer, FloatingPopup

class WeeklyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowStaysOnBottomHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.taskDatas = load_tasks()
        self.notes = load_notes()
        self.buildUI()
        
    def buildUI(self):
        if self.layout() is None:
            layout = QHBoxLayout(self)
            layout.setSpacing(5)
        else:
            while self.layout().count():
                child = self.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                    
        self.taskLayouts = {}
        self.tasks = {col: [] for col in config.get("COLUMNS", [])}

        for col_name in config.get("COLUMNS", []):
            if col_name not in self.notes: self.notes[col_name] = ""
            if col_name not in self.taskDatas: self.taskDatas[col_name] = []
            
            colWidget = QWidget()
            col_layout = QVBoxLayout(colWidget)
            colWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
            col_layout.setContentsMargins(0, 0, 0, 0)
            col_layout.setSpacing(5)
            
            colLabel = QPushButton(col_name)
            # Retain highlighting for TODAY if the column matches the current day abbreviation
            colLabel.setProperty("role", "dayLabel_today" if col_name == TODAY else "dayLabel")
            colLabel.clicked.connect(lambda _, d=col_name: self.setFocus(d))
            colLabel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            colLabel.setContextMenuPolicy(Qt.CustomContextMenu)
            colLabel.customContextMenuRequested.connect(lambda _, d=col_name: self.rightClickCol(d))
            col_layout.addWidget(colLabel)
            
            notes_widget = NoteWidget(self, col_name, self.notes[col_name])
            col_layout.addWidget(notes_widget, config["NOTES_TASKS_RATIO"])

            task_container = TaskListContainer(self, col_name)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(task_container)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
            col_layout.addWidget(scroll, 1)
                
            addTaskButton = QPushButton("+")
            addTaskButton.clicked.connect(lambda _, d=col_name: self.addTask(d))
            addTaskButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            col_layout.addWidget(addTaskButton)
            addTaskButton.setProperty("role", "addTask")

            self.taskLayouts[col_name] = task_container
            self.layout().addWidget(colWidget)
            
        columns = config.get("COLUMNS", [])
        focus_col = TODAY if TODAY in columns else (columns[0] if columns else None)
        if focus_col:
            self.setFocus(focus_col)
            
    def rebuildUI(self):
        # 1. Ensure the config reflects the current columns
        # (This persists your changes to config.json)
        from utils import saveConfig
        saveConfig()

        # 2. Update the internal task dictionary to support the new columns
        new_columns = config.get("COLUMNS", [])
        for col in new_columns:
            if col not in self.tasks:
                self.tasks[col] = []
        
        # 3. Save tasks and notes, then refresh visuals
        self.saveNotes()
        self.saveTasks()
        self.buildUI()
        self.addExistingTasks()
        self.updateConfig()

    def updatePos(self):
        screens = QGuiApplication.screens()
        screenIndex = min(config["DEFAULT_SCREEN"], len(screens) - 1)

        screen = screens[screenIndex]
        geo = screen.availableGeometry()
        
        height = geo.height() - config["TOP_MARGIN"] - config["BOTTOM_MARGIN"]
        width = geo.width() - config["LEFT_MARGIN"] - config["RIGHT_MARGIN"]
        
        self.resize(width, height)
        self.move(config["LEFT_MARGIN"], config["TOP_MARGIN"])
    
    def updateConfig(self):
        self.updatePos()
        self.updateStylesheet()
        
        for col_name in config.get("COLUMNS", []):
            for task in self.tasks[col_name]:
                task.updateStylesheet()
                
    def addExistingTasks(self):
        for col_name in config.get("COLUMNS", []):
            taskContainer = self.taskLayouts[col_name]
            
            for taskData in self.taskDatas[col_name]:
                task = TaskWidget(self, taskData["Description"], taskData["Done"], col_name)
                self.tasks[col_name].append(task)
                taskContainer.layout.addWidget(task)
            
            taskContainer.layout.addStretch()
    
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
            QPushButton:hover {{ background: rgba({config["HIGHLIGHT"]}); }}
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
            QScrollArea{{ background: rgba({config["BACKGROUND"]}); }}
        """)
        
    def rightClickCol(self, col_name):
        popup = FloatingPopup(self, col_name)
        center = self.mapToGlobal(self.rect().center())
        popup.move(center - popup.rect().center())
        popup.show()
        
    def clearCol(self, col_name):
        for task in list(self.tasks[col_name]):
            self.removeTask(task, col_name)
        self.saveTasks()
        
    def removeTask(self, task, col_name):
        self.taskLayouts[col_name].layout.removeWidget(task)
        task.setParent(None)
        task.deleteLater()
        self.tasks[col_name].remove(task)
        self.saveTasks()
        
    def clearAll(self):
        for col_name in config.get("COLUMNS", []):
            self.clearCol(col_name)
            
    def moveTask(self, task, dest_col, dest_index):
        source_col = task.col_name
        
        self.tasks[source_col].remove(task)
        self.taskLayouts[source_col].layout.removeWidget(task)
        
        task.col_name = dest_col
        
        dest_layout = self.taskLayouts[dest_col].layout
        if dest_index >= dest_layout.count() - 1:
            dest_index = dest_layout.count() - 1 
            
        self.tasks[dest_col].insert(dest_index, task)
        dest_layout.insertWidget(dest_index, task)
        
        self.saveTasks()
        self.setFocus(dest_col)
        
    def addTask(self, col_name):
        task = TaskWidget(self, "", False, col_name, True)
        self.tasks[col_name].append(task)
        
        taskLayout = self.taskLayouts[col_name].layout
        taskLayout.insertWidget(taskLayout.count() - 1, task)
        
        self.saveTasks()
        self.setFocus(col_name)
        
    def setFocus(self, col_name):
        columns = config.get("COLUMNS", [])
        if col_name not in columns: return
        dayIndex = columns.index(col_name)
        
        for i in range(len(columns)):
            self.layout().setStretch(i, 1)
        
        self.layout().setStretch(dayIndex, config["FOCUSED_SCALE"])
    
    def saveTasks(self):
        tasksToSave = {col: [] for col in config.get("COLUMNS", [])}
        for col_name in config.get("COLUMNS", []):
            for task in self.tasks[col_name]:
                tasksToSave[col_name].append(task.toData())
        
        # Keep inactive column data around when saving
        for old_col, old_data in self.taskDatas.items():
            if old_col not in tasksToSave:
                tasksToSave[old_col] = old_data
                
        self.taskDatas = tasksToSave
        save_tasks(tasksToSave)
    
    def saveNotes(self):
        save_notes(self.notes)
        
    def hideEvent(self, event):
        self.showNormal()
        self.raise_()
        self.activateWindow()
        super().hideEvent(event)