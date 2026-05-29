from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, 
    QPushButton, QLineEdit, QTextEdit, QGridLayout, QFrame
)
from PySide6.QtCore import Qt, QTimer
from utils import config

class NoteWidget(QWidget):
    def __init__(self, parent, day, text):
        super().__init__()
        self.parent_widget = parent
        self.day = day
        
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
        self.parent_widget.setFocus(self.day)
        QTextEdit.focusInEvent(self.editor, event)
        
    def endEditing(self, event):
        self.parent_widget.notes[self.day] = self.editor.toPlainText()
        self.parent_widget.saveNotes()
        QTextEdit.focusOutEvent(self.editor, event)

class TaskWidget(QWidget):
    def __init__(self, parent, description, done, day, new=False):
        super().__init__()
        self.parent_widget = parent
        self.description = description
        self.done = done
        self.day = day

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        frame = QFrame()
        frameLayout = QHBoxLayout(frame)
        frameLayout.setContentsMargins(0, 0, 0, 0)
        frameLayout.setSpacing(0)
        layout.addWidget(frame)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.done)
        self.checkbox.stateChanged.connect(self.updateChecked)
        frameLayout.addWidget(self.checkbox)

        self.editor = QLineEdit(self.description)
        self.editor.setReadOnly(True)
        self.editor.setCursorPosition(0)
        self.editor.setFrame(False)
        self.editor.editingFinished.connect(self.finishEdit)
        self.editor.mousePressEvent = self.startEdit
        frameLayout.addWidget(self.editor)
        
        self.deleteButton = QPushButton("X")
        self.deleteButton.clicked.connect(self.deleteTask)
        frameLayout.addWidget(self.deleteButton)

        self.updateStylesheet()
        if new:
            QTimer.singleShot(0, self.startEdit)

    def startEdit(self, event=None):
        self.parent_widget.setFocus(self.day)
        self.editor.setReadOnly(False)
        self.editor.setCursorPosition(len(self.editor.text()))
        self.editor.setFocus()

    def finishEdit(self):
        self.editor.setReadOnly(True)
        self.editor.setCursorPosition(0)
        self.description = self.editor.text()
        self.parent_widget.saveTasks()
    
    def deleteTask(self):
        self.parent_widget.removeTask(self, self.day)

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

class FloatingPopup(QWidget):
    def __init__(self, parent, day):
        super().__init__(parent)
        self.parent_widget = parent
        self.day = day

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(300, 125)
        
        bg = QWidget(self)
        bg.setGeometry(self.rect())
    
        layout = QGridLayout(bg)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        clearWeek = QPushButton("Clear Week")
        clearDay = QPushButton("Clear Day")
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
        self.parent_widget.clearWeek()
        self.close()
        
    def clearDay(self):
        self.parent_widget.clearDay(self.day)
        self.close()