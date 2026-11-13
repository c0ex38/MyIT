"""MyIT - IT Destek & Sistem Yönetim Paneli.

Uygulamanın ana giriş noktasıdır.
"""

import sys

from PySide6.QtWidgets import QApplication

from myit.ui.main_window import MainWindow


def main():
    """Uygulamayı başlatır ve ana pencereyi görüntüler."""
    app = QApplication(sys.argv)
    app.setApplicationName("MyIT")
    app.setApplicationVersion("0.0.2")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
