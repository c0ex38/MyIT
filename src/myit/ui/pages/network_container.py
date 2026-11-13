"""MyIT Ağ Araçları ana sayfası.

Bu modül; 'Ping Teşhisi' ve 'Ağ Keşfi' modüllerini tek bir
QTabWidget altında sekmeler halinde birleştirir.
"""

from typing import Optional
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from myit.ui.pages.discovery_page import DiscoveryPage
from myit.ui.pages.network_page import NetworkPage


class NetworkToolsContainer(QWidget):
    """Ağ Araçları konteyner sayfası (Ping & Ağ Keşfi sekmeleri)."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("NetworkTabWidget")

        # 1. Ping Sekmesi
        self.ping_page = NetworkPage(parent=self)
        self.tab_widget.addTab(self.ping_page, "Hızlı Ping")

        # 2. Ağ Keşfi Sekmesi
        self.discovery_page = DiscoveryPage(on_send_to_ping=self.set_ping_target, parent=self)
        self.tab_widget.addTab(self.discovery_page, "Ağ Cihaz Keşfi")

        layout.addWidget(self.tab_widget)

    def set_ping_target(self, target_ip: str):
        """Ağ keşfinden seçilen bir IP'yi Ping aracına aktarır ve sekmeyi açar."""
        self.ping_page.input_target.setText(target_ip)
        self.tab_widget.setCurrentIndex(0)
        self.ping_page.lbl_feedback.setText(f"Hedef {target_ip} Ping aracına aktarıldı. 'Başlat'a basabilirsiniz.")

    def cleanup(self):
        """Pencere kapanırken aktif alt süreçleri sonlandırır."""
        if hasattr(self, "ping_page") and self.ping_page:
            self.ping_page.cleanup()
        if hasattr(self, "discovery_page") and self.discovery_page:
            self.discovery_page.cleanup()
