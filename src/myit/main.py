"""MyIT - IT Destek & Sistem Yönetim Paneli.

Uygulamanın ana giriş noktasıdır.
"""

import sys

from PySide6.QtWidgets import QApplication

from myit.core.version import APP_NAME, __version__
from myit.ui.main_window import MainWindow


def main():
    """Uygulamayı başlatır ve ana pencereyi görüntüler."""
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
