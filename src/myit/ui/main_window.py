"""MyIT ana pencere bileşeni.

Bu modül; sol sidebar, sayfa yığını (QStackedWidget) ve alt durum çubuğunu
birleştirerek v0.0.2 Midnight Blue arayüzünü oluşturur.
"""

from typing import Dict
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from myit.ui.dashboard import DashboardView
from myit.ui.sidebar import Sidebar
from myit.ui.styles import get_stylesheet
from myit.ui.theme_manager import ThemeManager


class PlaceholderView(QWidget):
    """Henüz uygulanmamış modüller için yer tutucu görünüm."""

    def __init__(self, title: str, description: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # Başlık Bölümü
        header_layout = QVBoxLayout()
        header_layout.setSpacing(6)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("PageHeaderTitle")
        header_layout.addWidget(lbl_title)

        lbl_subtitle = QLabel(description)
        lbl_subtitle.setObjectName("PageHeaderSubtitle")
        header_layout.addWidget(lbl_subtitle)

        layout.addLayout(header_layout)

        # Bilgilendirme Kartı
        card = QFrame()
        card.setObjectName("PlaceholderCard")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        msg_title = QLabel(f"{title} Modülü")
        msg_title.setObjectName("PlaceholderTitle")
        msg_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(msg_title)

        msg_desc = QLabel("Bu modül sonraki sürümlerde geliştirilecek.")
        msg_desc.setObjectName("PlaceholderMessage")
        msg_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(msg_desc)

        layout.addWidget(card)
        layout.addStretch()


class MainWindow(QMainWindow):
    """MyIT v0.0.2 Ana Penceresi."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyIT — IT Management Toolbox")
        self.resize(1150, 750)
        self.setMinimumSize(900, 600)

        # Tema Yöneticisi (Varsayılan Koyu Tema)
        self.theme_manager = ThemeManager()
        self.theme_manager.theme_changed.connect(self._on_theme_changed)

        # Sayfa eşleştirme sözlüğü (page_id -> QStackedWidget indeksi)
        self._page_indices: Dict[str, int] = {}

        self._init_ui()
        self._apply_theme()

    def _init_ui(self):
        """Pencere düzenini ve ana bileşenleri kurar."""
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Gövde Alanı (Sol Sidebar + Sağ İçerik)
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sol Sidebar
        self.sidebar = Sidebar(
            on_page_selected=self.navigate_to_page,
            on_theme_toggle=self.theme_manager.toggle_theme,
            parent=self,
        )
        body_layout.addWidget(self.sidebar)

        # Sağ İçerik Alanı (QStackedWidget)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("ContentArea")
        self._init_pages()
        body_layout.addWidget(self.stacked_widget, 1)

        root_layout.addLayout(body_layout, 1)

        # 2. Alt Durum Çubuğu
        self._init_footer(root_layout)

    def _init_pages(self):
        """Sayfaları QStackedWidget içerisine ekler."""
        # 1. Dashboard
        dashboard = DashboardView(on_navigate=self._on_dashboard_navigate, parent=self)
        idx_dash = self.stacked_widget.addWidget(dashboard)
        self._page_indices["dashboard"] = idx_dash

        # 2. Diğer Sayfalar (Yer Tutucu)
        pages = [
            ("network", "Ağ Araçları", "Ping, cihaz keşfi, port tarama ve ağ teşhisi"),
            ("hardware", "Donanım", "Sistem donanım bileşenleri, CPU, RAM ve disk bilgileri"),
            ("windows", "Windows Yönetimi", "Windows servisleri, teşhis araçları ve hızlı komutlar"),
            ("tools", "Yardımcı Araçlar", "Sistem temizliği, hızlı notlar ve genel destek araçları"),
            ("about", "Hakkında", "MyIT sürüm, lisans ve mimari bilgileri"),
        ]

        for pid, ptitle, pdesc in pages:
            view = PlaceholderView(ptitle, pdesc, parent=self)
            idx = self.stacked_widget.addWidget(view)
            self._page_indices[pid] = idx

        # Başlangıçta Dashboard göster
        self.stacked_widget.setCurrentIndex(self._page_indices["dashboard"])

    def _init_footer(self, layout: QVBoxLayout):
        """Alt durum çubuğunu oluşturur."""
        footer = QFrame()
        footer.setObjectName("FooterFrame")
        footer.setFixedHeight(36)

        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(18, 0, 18, 0)

        # Sol durum metni
        self.lbl_status = QLabel("MyIT Hazır")
        self.lbl_status.setObjectName("FooterStatusLabel")
        footer_layout.addWidget(self.lbl_status)

        footer_layout.addStretch()

        # Aktif tema bilgisi
        self.lbl_theme = QLabel(self.theme_manager.theme_display_name)
        self.lbl_theme.setObjectName("FooterThemeLabel")
        footer_layout.addWidget(self.lbl_theme)

        # Ayırıcı
        sep = QLabel("•")
        sep.setObjectName("FooterVersionLabel")
        footer_layout.addWidget(sep)

        # Sürüm etiketi
        lbl_version = QLabel("v0.0.2")
        lbl_version.setObjectName("FooterVersionLabel")
        footer_layout.addWidget(lbl_version)

        layout.addWidget(footer)

    def navigate_to_page(self, page_id: str):
        """Sayfa değiştirir ve durum çubuğunu günceller."""
        if page_id in self._page_indices:
            idx = self._page_indices[page_id]
            self.stacked_widget.setCurrentIndex(idx)
            self.sidebar.set_active_page(page_id)
            self.lbl_status.setText(f"Sayfa: {page_id.capitalize()}")

    def _on_dashboard_navigate(self, page_id: str):
        """Dashboard kartından gelen yönlendirmeyi işler."""
        self.navigate_to_page(page_id)

    def _on_theme_changed(self, new_theme: str):
        """Tema değiştiğinde stili ve göstergeleri yeniler."""
        self._apply_theme()
        self.sidebar.update_theme_button(new_theme)
        self.lbl_theme.setText(self.theme_manager.theme_display_name)
        self.lbl_status.setText(f"Tema güncellendi: {self.theme_manager.theme_display_name}")

    def _apply_theme(self):
        """Mevcut temanın QSS stilini tüm pencereye uygular."""
        qss = get_stylesheet(self.theme_manager.current_theme)
        self.setStyleSheet(qss)
