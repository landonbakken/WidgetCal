from PySide6.QtGui import QTextOption, QDrag
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, 
    QPushButton, QLineEdit, QTextEdit, QGridLayout, 
    QFrame, QLabel, QScrollArea, QFormLayout, QApplication
)
from PySide6.QtCore import Qt, QTimer, QMimeData
from utils import config, DEFAULT_COLUMNS, saveConfig

class NoteWidget(QWidget):
    def __init__(self, parent, col_name, text):
        super().__init__()
        self.parent_widget = parent
        self.col_name = col_name
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.editor = QTextEdit()
        self.editor.setAcceptRichText(False)
        self.editor.setWordWrapMode(QTextOption.WordWrap)
        self.editor.setLineWrapMode(QTextEdit.WidgetWidth)
        self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.editor.setPlainText(text)
        
        self.editor.focusInEvent = self.startEditing
        self.editor.focusOutEvent = self.endEditing

        layout.addWidget(self.editor)
        
    def startEditing(self, event):
        self.parent_widget.setFocus(self.col_name)
        QTextEdit.focusInEvent(self.editor, event)
        
    def endEditing(self, event):
        self.parent_widget.notes[self.col_name] = self.editor.toPlainText()
        self.parent_widget.saveNotes()
        QTextEdit.focusOutEvent(self.editor, event)

class TaskWidget(QWidget):
    def __init__(self, parent, description, done, col_name, new=False):
        super().__init__()
        self.parent_widget = parent
        self.description = description
        self.done = done
        self.col_name = col_name

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        frame = QFrame()
        frameLayout = QHBoxLayout(frame)
        frameLayout.setContentsMargins(0, 0, 0, 0)
        frameLayout.setSpacing(2)
        layout.addWidget(frame)
        
        self.dragHandle = QLabel("⋮")
        self.dragHandle.setStyleSheet("color: rgba(100, 100, 100, 150); font-weight: bold;")
        self.dragHandle.setCursor(Qt.OpenHandCursor)
        frameLayout.addWidget(self.dragHandle)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.done)
        self.checkbox.stateChanged.connect(self.updateChecked)
        frameLayout.addWidget(self.checkbox)

        self.editor = QLineEdit(self.description)
        self.editor.setFrame(False)
        self.editor.setStyleSheet("background: transparent;")
        self.editor.editingFinished.connect(self.finishEdit)
        frameLayout.addWidget(self.editor)
        
        self.deleteButton = QPushButton("X")
        self.deleteButton.clicked.connect(self.deleteTask)
        frameLayout.addWidget(self.deleteButton)

        self.updateStylesheet()
        if new:
            # Let the window finish rendering, then auto-focus the new line edit
            QTimer.singleShot(0, self.editor.setFocus)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton): return
        if (event.position().toPoint() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance(): return
        
        QApplication.instance().dragged_task = self
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData("application/x-task", b"")
        drag.setMimeData(mime)
        drag.exec(Qt.MoveAction)

    def finishEdit(self):
        self.description = self.editor.text()
        self.parent_widget.saveTasks()
    
    def deleteTask(self):
        self.parent_widget.removeTask(self, self.col_name)

    def updateChecked(self):
        self.done = self.checkbox.isChecked()
        self.updateStylesheet()
        self.parent_widget.saveTasks()

    def updateStylesheet(self):
        if self.checkbox.isChecked():
            self.setStyleSheet(f"""
                QFrame{{
                    background: rgba({config["CHECKED_BACKGROUND"]});
                    color: rgba({config["CHECKED_TEXT"]});
                }}
                QCheckBox {{ spacing: 0px; padding: 1px; margin: 0px; }}
                QCheckBox::indicator {{ margin: 0px; padding: 0px; }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame{{
                    background: rgba({config["UNCHECKED_BACKGROUND"]});
                    color: rgba({config["UNCHECKED_TEXT"]});
                }}
                QCheckBox {{ spacing: 0px; padding: 1px; margin: 0px; }}
                QCheckBox::indicator {{ margin: 0px; padding: 0px; }}
            """)
            
    def toData(self):
        return {
            "Description": self.description,
            "Done": self.done
        }

class TaskListContainer(QWidget):
    def __init__(self, parent, col_name):
        super().__init__()
        self.main_window = parent
        self.col_name = col_name
        self.setAcceptDrops(True)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-task"):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-task"):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        task = getattr(QApplication.instance(), "dragged_task", None)
        if task:
            y = event.position().y()
            index = 0
            for i in range(self.layout.count() - 1):
                w = self.layout.itemAt(i).widget()
                if w and y > w.y() + w.height() / 2:
                    index += 1
            self.main_window.moveTask(task, self.col_name, index)
            event.accept()

class ConfigWindow(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.main_window = parent
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(450, 500)
        
        bg = QWidget(self)
        bg.setGeometry(self.rect())
        
        layout = QVBoxLayout(bg)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content = QWidget()
        self.form = QFormLayout(content)
        self.inputs = {}
        
        # Build Columns String Input
        cols_str = ", ".join(config.get("COLUMNS", DEFAULT_COLUMNS))
        self.columns_input = QLineEdit(cols_str)
        self.form.addRow("Columns (comma separated)", self.columns_input)
        
        # Build other config fields
        for key, val in config.items():
            if key in ["unused", "COLUMNS", "ACTIVE_DAYS"]: continue
            inp = QLineEdit(str(val))
            self.form.addRow(key, inp)
            self.inputs[key] = inp
            
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save && Apply")
        save_btn.clicked.connect(self.save_config)
        close_btn = QPushButton("Cancel")
        close_btn.clicked.connect(self.close)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        self.setStyleSheet(f"""
            QWidget{{
                background: rgba({config["POPUP_BACKGROUND"]});
                border-radius: 10px;
                color: rgba({config["CHECKED_TEXT"]});
            }}
            QPushButton {{
                background: rgba({config["POPUP_BUTTON"]});
                border-radius: 8px;
                padding: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba({config["POPUP_BUTTON_HIGHLIGHT"]});
            }}
            QLineEdit {{
                background: rgba(255, 255, 255, 100);
                border: 1px solid rgba(0, 0, 0, 50);
                padding: 2px;
                border-radius: 4px;
            }}
        """)
        
    def save_config(self):
        cols_raw = self.columns_input.text().split(",")
        config["COLUMNS"] = [c.strip() for c in cols_raw if c.strip()]
        
        for key, inp in self.inputs.items():
            val = inp.text()
            if isinstance(config.get(key), int):
                try: val = int(val)
                except ValueError: pass
            config[key] = val
        
        saveConfig()
        self.main_window.rebuildUI()
        self.close()

class FloatingPopup(QWidget):
    def __init__(self, parent, col_name):
        super().__init__(parent)
        self.parent_widget = parent
        self.col_name = col_name

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(300, 160)
        
        bg = QWidget(self)
        bg.setGeometry(self.rect())
    
        layout = QGridLayout(bg)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        clearAll = QPushButton("Clear All Columns")
        clearCol = QPushButton("Clear Column")
        settingsBtn = QPushButton("Settings")
        cancel = QPushButton("Close")

        cancel.clicked.connect(self.close)
        clearAll.clicked.connect(self.clearAll)
        clearCol.clicked.connect(self.clearCol)
        settingsBtn.clicked.connect(self.openSettings)

        layout.addWidget(clearAll, 0, 0)
        layout.addWidget(clearCol, 0, 1)
        layout.addWidget(settingsBtn, 1, 0, 1, 2)
        layout.addWidget(cancel, 2, 0, 1, 2)
    
        self.setStyleSheet(f"""
            QWidget{{
                background: rgba({config["POPUP_BACKGROUND"]});
                border-radius: 10px;
            }}
            QPushButton {{
                background: rgba({config["POPUP_BUTTON"]});
                border-radius: 8px;
                padding: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba({config["POPUP_BUTTON_HIGHLIGHT"]});
            }}
        """)
        
    def clearAll(self):
        self.parent_widget.clearAll()
        self.close()
        
    def clearCol(self):
        self.parent_widget.clearCol(self.col_name)
        self.close()

    def openSettings(self):
        self.config_win = ConfigWindow(self.parent_widget)
        center = self.parent_widget.mapToGlobal(self.parent_widget.rect().center())
        self.config_win.move(center - self.config_win.rect().center())
        self.config_win.show()
        self.close()