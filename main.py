import sys
from PySide6.QtWidgets import QApplication
from utils import updateInstanceOnly, loadConfig
from app_window import WeeklyWidget

def main():
    updateInstanceOnly()
    loadConfig()

    app = QApplication(sys.argv)
    app.dragged_task = None
    
    w = WeeklyWidget()
    w.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()