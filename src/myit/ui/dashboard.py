"""MyIT başlangıç ve Dashboard ekranı.

Bu modül, v0.0.2 için 4 ana kategori kartını ve sayfa geçiş aksiyonlarını
içeren Dashboard arayüzünü tanımlar.
"""

from typing import Callable, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DashboardCard(QFrame):
    """Dashboard üzerinde yer alan kategori kartı bileşeni."""

    def __init__(
        self,
        title: str,
        description: str,
        target_page_id: str,
        on_open: Optional[Callable[[str], None]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("DashboardCard")
        self.target_page_id = target_page_id
        self.on_open = on_open

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 18)
        layout.setSpacing(10)

        # Kart başlığı
        lbl_title = QLabel(title)
        lbl_title.setObjectName("CardTitle")
        layout.addWidget(lbl_title)

        # Kart açıklaması
        lbl_desc = QLabel(description)
        lbl_desc.setObjectName("CardDescription")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        layout.addStretch()

        # Alt aksiyon butonu
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_open = QPushButton("Aç →")
        btn_open.setObjectName("CardActionBtn")
        btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open.clicked.connect(self._handle_click)
        btn_layout.addWidget(btn_open)

        layout.addLayout(btn_layout)

    def _handle_click(self):
        """Karta tıklandığında ilgili hedef sayfayı açma sinyali verir."""
        if self.on_open:
            self.on_open(self.target_page_id)


class DashboardView(QWidget):
    """Ana Dashboard görünümü."""

    def __init__(self, on_navigate: Optional[Callable[[str], None]] = None, parent=None):
        super().__init__(parent)
        self.on_navigate = on_navigate

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(24)

        # Başlık Bölümü
        header_layout = QVBoxLayout()
        header_layout.setSpacing(6)

        title = QLabel("Genel Bakış")
        title.setObjectName("PageHeaderTitle")
        header_layout.addWidget(title)

        subtitle = QLabel("IT destek ve sistem yönetimi araç kategorileri")
        subtitle.setObjectName("PageHeaderSubtitle")
        header_layout.addWidget(subtitle)

        layout.addLayout(header_layout)

        # Kategori Kartları Izgarası (2x2)
        grid = QGridLayout()
        grid.setSpacing(18)

        categories = [
            (
                "Ağ Araçları",
                "IP yapılandırması, ping testleri, bağlantı noktası kontrolleri ve DNS sorgulama araçları.",
                "network",
                0,
                0,
            ),
            (
                "Donanım & Sistem",
                "İşlemci, bellek, depolama alanı ve sistem donanım bileşenlerinin anlık durumu.",
                "hardware",
                0,
                1,
            ),
            (
                "Windows Yönetimi",
                "Servis yönetimi, hızlı komutlar ve Windows sistem teşhis/onarım yardımcıları.",
                "windows",
                1,
                0,
            ),
            (
                "Yardımcı Araçlar",
                "Geçici dosya temizliği, hızlı notlar ve genel destek bakım fonksiyonları.",
                "tools",
                1,
                1,
            ),
        ]

        for cat_title, cat_desc, page_id, row, col in categories:
            card = DashboardCard(
                title=cat_title,
                description=cat_desc,
                target_page_id=page_id,
                on_open=self._navigate_to_page,
                parent=self,
            )
            grid.addWidget(card, row, col)

        layout.addLayout(grid)
        layout.addStretch()

    def _navigate_to_page(self, page_id: str):
        """Kategori kartından ilgili sayfaya geçişi tetikler."""
        if self.on_navigate:
            self.on_navigate(page_id)
