"""MyIT Ağ Araçları ana sayfası.

Bu modül; 'Hızlı Ping', 'Ağ Cihaz Keşfi', 'Port Tarayıcı' ve 'DNS Araçları'
modüllerini tek bir QTabWidget altında sekmeler halinde birleştirir.
"""

from typing import Optional
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from myit.ui.pages.discovery_page import DiscoveryPage
from myit.ui.pages.dns_page import DnsPage
from myit.ui.pages.network_page import NetworkPage
from myit.ui.pages.port_scan_page import PortScanPage


class NetworkToolsContainer(QWidget):
    """Ağ Araçları konteyner sayfası (Ping, Keşif, Port Tarama ve DNS sekmeleri)."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("NetworkTabWidget")

        # 1. Hızlı Ping Sekmesi
        self.ping_page = NetworkPage(parent=self)
        self.tab_widget.addTab(self.ping_page, "Hızlı Ping")

        # 2. Ağ Cihaz Keşfi Sekmesi
        self.discovery_page = DiscoveryPage(
            on_send_to_ping=self.set_ping_target,
            on_send_to_port_scan=self.set_port_scan_target,
            parent=self,
        )
        self.tab_widget.addTab(self.discovery_page, "Ağ Cihaz Keşfi")

        # 3. Port Tarayıcı Sekmesi
        self.port_scan_page = PortScanPage(parent=self)
        self.tab_widget.addTab(self.port_scan_page, "Port Tarayıcı")

        # 4. DNS Araçları Sekmesi
        self.dns_page = DnsPage(parent=self)
        self.tab_widget.addTab(self.dns_page, "DNS Araçları")

        layout.addWidget(self.tab_widget)

    def set_ping_target(self, target_ip: str):
        """Ağ keşfinden seçilen bir IP'yi Ping aracına aktarır ve sekmeyi açar."""
        self.ping_page.input_target.setText(target_ip)
        self.tab_widget.setCurrentIndex(0)
        self.ping_page.lbl_feedback.setText(f"Hedef {target_ip} Ping aracına aktarıldı. 'Başlat'a basabilirsiniz.")

    def set_port_scan_target(self, target_ip: str):
        """Ağ keşfinden seçilen bir IP'yi Port Tarayıcıya aktarır ve sekmeyi açar (otomatik başlatmaz)."""
        self.port_scan_page.set_target(target_ip)
        self.tab_widget.setCurrentIndex(2)

    def cleanup(self):
        """Pencere kapanırken tüm sekmelerdeki aktif alt süreçleri sonlandırır."""
        if hasattr(self, "ping_page") and self.ping_page:
            self.ping_page.cleanup()
        if hasattr(self, "discovery_page") and self.discovery_page:
            self.discovery_page.cleanup()
        if hasattr(self, "port_scan_page") and self.port_scan_page:
            self.port_scan_page.cleanup()
        if hasattr(self, "dns_page") and self.dns_page:
            self.dns_page.cleanup()
