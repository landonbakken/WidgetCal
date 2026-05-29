import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFileSystemWatcher
from utils import updateInstanceOnly, loadConfig, CONFIG_FILE
from app_window import WeeklyWidget

def main():
    updateInstanceOnly()
    loadConfig()

    app = QApplication(sys.argv)
    w = WeeklyWidget()
    w.show()

    # Attach watcher to window instance so it is not garbage collected
    w.watcher = QFileSystemWatcher()
    w.watcher.addPath(str(CONFIG_FILE))
    
    def on_config_changed(path):
        loadConfig()
        w.updateConfig()
        
    w.watcher.fileChanged.connect(on_config_changed)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()