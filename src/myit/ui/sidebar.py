"""MyIT sol gezinme çubuğu (Sidebar).

Bu modül, daraltılabilir (collapsible) sol menüyü, sayfa seçim butonlarını
ve tema değiştirme kontrolünü yönetir.
"""

from typing import Callable, Dict, List, Optional
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStyle,
    QVBoxLayout,
)


class Sidebar(QFrame):
    """Genişletilebilir ve daraltılabilir sol menü bileşeni."""

    WIDTH_EXPANDED = 230
    WIDTH_COLLAPSED = 68

    def __init__(
        self,
        on_page_selected: Optional[Callable[[str], None]] = None,
        on_theme_toggle: Optional[Callable[[], None]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("SidebarFrame")
        self.on_page_selected = on_page_selected
        self.on_theme_toggle = on_theme_toggle
        self._is_collapsed: bool = False
        self._active_page_id: str = "dashboard"
        self._nav_buttons: Dict[str, QPushButton] = {}

        # Başlangıç genişliği
        self.setFixedWidth(self.WIDTH_EXPANDED)

        # Menü öğeleri tanımı: (page_id, title, Qt StandardPixmap)
        self._menu_items: List[tuple] = [
            ("dashboard", "Dashboard", QStyle.StandardPixmap.SP_DesktopIcon),
            ("network", "Ağ Araçları", QStyle.StandardPixmap.SP_DriveNetIcon),
            ("hardware", "Donanım", QStyle.StandardPixmap.SP_ComputerIcon),
            ("windows", "Windows", QStyle.StandardPixmap.SP_TitleBarMenuButton),
            ("tools", "Yardımcı Araçlar", QStyle.StandardPixmap.SP_FileDialogDetailedView),
            ("about", "Hakkında", QStyle.StandardPixmap.SP_MessageBoxInformation),
        ]

        self._init_ui()

    def _init_ui(self):
        """Arayüz bileşenlerini oluşturur ve yerleştirir."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(8)

        # 1. Üst Başlık ve Daraltma Butonu
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(4, 0, 4, 8)

        self.lbl_brand = QLabel("MyIT")
        self.lbl_brand.setObjectName("SidebarBrandTitle")
        top_layout.addWidget(self.lbl_brand)

        top_layout.addStretch()

        self.btn_toggle = QPushButton("◀")
        self.btn_toggle.setObjectName("SidebarToggleBtn")
        self.btn_toggle.setFixedSize(30, 30)
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.setToolTip("Menüyü Daralt / Genişlet")
        self.btn_toggle.clicked.connect(self.toggle_collapse)
        top_layout.addWidget(self.btn_toggle)

        layout.addLayout(top_layout)

        # 2. Navigasyon Butonları
        style = self.style()
        for page_id, title, icon_pixmap in self._menu_items:
            btn = QPushButton()
            btn.setObjectName("SidebarNavButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setIcon(style.standardIcon(icon_pixmap))
            btn.setIconSize(QSize(18, 18))
            btn.setText(f"  {title}")
            btn.setToolTip(title)

            # Tıklama olayını bağla
            btn.clicked.connect(lambda checked=False, pid=page_id: self._handle_nav_click(pid))

            layout.addWidget(btn)
            self._nav_buttons[page_id] = btn

        # Boşluk
        layout.addStretch()

        # 3. Tema Değiştirme Butonu
        self.btn_theme = QPushButton("☀️ Açık Tema")
        self.btn_theme.setObjectName("ThemeToggleBtn")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.setToolTip("Koyu / Açık Tema Değiştir")
        if self.on_theme_toggle:
            self.btn_theme.clicked.connect(self.on_theme_toggle)
        layout.addWidget(self.btn_theme)

        # İlk aktif durumu uygula
        self.set_active_page("dashboard")

    def _handle_nav_click(self, page_id: str):
        """Menü butonuna tıklandığında sayfayı aktif yapar ve dışarı bildirir."""
        self.set_active_page(page_id)
        if self.on_page_selected:
            self.on_page_selected(page_id)

    def set_active_page(self, page_id: str):
        """Belirtilen sayfayı aktif olarak işaretler ve stilini günceller."""
        self._active_page_id = page_id
        for pid, btn in self._nav_buttons.items():
            is_active = (pid == page_id)
            btn.setProperty("active", "true" if is_active else "false")
            # Dynamic property değişikliğini zorla güncelle
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def toggle_collapse(self):
        """Sidebar genişliğini dar/geniş mod arasında değiştirir."""
        self._is_collapsed = not self._is_collapsed

        if self._is_collapsed:
            self.setFixedWidth(self.WIDTH_COLLAPSED)
            self.lbl_brand.setVisible(False)
            self.btn_toggle.setText("▶")
            self.btn_theme.setText("🌓")
            for page_id, title, _ in self._menu_items:
                btn = self._nav_buttons[page_id]
                btn.setText("")  # Dar modda yalnızca ikon göster
        else:
            self.setFixedWidth(self.WIDTH_EXPANDED)
            self.lbl_brand.setVisible(True)
            self.btn_toggle.setText("◀")
            for page_id, title, _ in self._menu_items:
                btn = self._nav_buttons[page_id]
                btn.setText(f"  {title}")

        # Aktif sayfa vurgusunu koru
        self.set_active_page(self._active_page_id)

    def update_theme_button(self, current_theme_key: str):
        """Tema butonunun metnini aktif temaya göre günceller."""
        if self._is_collapsed:
            self.btn_theme.setText("🌓")
        else:
            if current_theme_key == "dark":
                self.btn_theme.setText("☀️ Açık Tema")
            else:
                self.btn_theme.setText("🌙 Koyu Tema")
