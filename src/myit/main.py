import sys

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow
from PySide6.QtCore import Qt


class MyITWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MyIT - v0.0.1")
        self.resize(1000, 650)
        self.setMinimumSize(800, 500)

        label = QLabel("MyIT\nPortable IT Management Toolbox")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setCentralWidget(label)


def main():
    app = QApplication(sys.argv)

    window = MyITWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
