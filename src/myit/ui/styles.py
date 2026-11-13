"""MyIT tema ve renk tanımları.

Bu modül, Midnight Blue marka renklerini, açık ve koyu tema token'larını
ve Qt Style Sheets (QSS) şablonlarını merkezi olarak yönetir.
"""

from typing import Dict

# Tema Token Tanımları
THEMES: Dict[str, Dict[str, str]] = {
    "dark": {
        "name": "Koyu",
        "bg": "#0B1220",
        "sidebar_bg": "#101A2B",
        "surface": "#151F32",
        "surface_hover": "#1E2C45",
        "text_primary": "#E2E8F0",
        "text_secondary": "#94A3B8",
        "accent": "#2563EB",
        "accent_hover": "#1D4ED8",
        "border": "#2B3A52",
        "secondary_accent": "#38BDF8",
        "selected_bg": "#1E2C45",
        "footer_bg": "#0B1220",
        "input_bg": "#0F1A2C",
        "console_bg": "#080E18",
        "danger": "#EF4444",
        "danger_hover": "#DC2626",
        "table_header_bg": "#101A2B",
        "table_row_alt": "#121C2D",
    },
    "light": {
        "name": "Açık",
        "bg": "#F5F7FB",
        "sidebar_bg": "#FFFFFF",
        "surface": "#FFFFFF",
        "surface_hover": "#EFF4FB",
        "text_primary": "#17243B",
        "text_secondary": "#53657D",
        "accent": "#1D4ED8",
        "accent_hover": "#1E40AF",
        "border": "#D7E1EF",
        "secondary_accent": "#0284C7",
        "selected_bg": "#E5EEFF",
        "footer_bg": "#FFFFFF",
        "input_bg": "#F8FAFD",
        "console_bg": "#FFFFFF",
        "danger": "#DC2626",
        "danger_hover": "#B91C1C",
        "table_header_bg": "#EDF2F9",
        "table_row_alt": "#F9FAFC",
    },
}


def get_stylesheet(theme_key: str = "dark") -> str:
    """Belirtilen tema için QSS stil metnini döndürür.

    Args:
        theme_key: 'dark' veya 'light'.
    """
    t = THEMES.get(theme_key, THEMES["dark"])

    return f"""
/* Genel Pencere ve Arka Plan */
QMainWindow {{
    background-color: {t["bg"]};
}}

QWidget#CentralWidget {{
    background-color: {t["bg"]};
}}

QWidget#ContentArea {{
    background-color: {t["bg"]};
}}

/* Sol Sidebar Menü */
QFrame#SidebarFrame {{
    background-color: {t["sidebar_bg"]};
    border-right: 1px solid {t["border"]};
}}

QLabel#SidebarBrandTitle {{
    color: {t["text_primary"]};
    font-size: 18px;
    font-weight: bold;
    font-family: 'Segoe UI', sans-serif;
}}

QPushButton#SidebarToggleBtn {{
    background-color: transparent;
    color: {t["text_secondary"]};
    border: 1px solid {t["border"]};
    border-radius: 6px;
    padding: 4px;
    font-size: 14px;
}}

QPushButton#SidebarToggleBtn:hover {{
    background-color: {t["surface_hover"]};
    color: {t["text_primary"]};
}}

/* Sidebar Menü Butonları */
QPushButton#SidebarNavButton {{
    background-color: transparent;
    color: {t["text_secondary"]};
    border: none;
    border-radius: 8px;
    text-align: left;
    padding: 10px 14px;
    font-size: 13px;
    font-weight: 500;
    font-family: 'Segoe UI', sans-serif;
}}

QPushButton#SidebarNavButton:hover {{
    background-color: {t["surface_hover"]};
    color: {t["text_primary"]};
}}

QPushButton#SidebarNavButton[active="true"] {{
    background-color: {t["selected_bg"]};
    color: {t["secondary_accent"]};
    font-weight: 600;
    border-left: 3px solid {t["secondary_accent"]};
}}

/* Tema Değiştirme Butonu */
QPushButton#ThemeToggleBtn {{
    background-color: transparent;
    color: {t["text_secondary"]};
    border: 1px solid {t["border"]};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
    font-family: 'Segoe UI', sans-serif;
    text-align: center;
}}

QPushButton#ThemeToggleBtn:hover {{
    background-color: {t["surface_hover"]};
    color: {t["text_primary"]};
    border-color: {t["secondary_accent"]};
}}

/* Başlıklar */
QLabel#PageHeaderTitle {{
    color: {t["text_primary"]};
    font-size: 24px;
    font-weight: bold;
    font-family: 'Segoe UI', sans-serif;
}}

QLabel#PageHeaderSubtitle {{
    color: {t["text_secondary"]};
    font-size: 13px;
    font-family: 'Segoe UI', sans-serif;
}}

/* QTabWidget (Ağ Araçları alt sekmeleri) */
QTabWidget::pane {{
    border: none;
    background-color: transparent;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {t["text_secondary"]};
    border: none;
    border-bottom: 2px solid transparent;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 500;
    font-family: 'Segoe UI', sans-serif;
}}

QTabBar::tab:hover {{
    color: {t["text_primary"]};
}}

QTabBar::tab:selected {{
    color: {t["secondary_accent"]};
    border-bottom: 2px solid {t["secondary_accent"]};
    font-weight: 600;
}}

/* Dashboard Kartları */
QFrame#DashboardCard {{
    background-color: {t["surface"]};
    border: 1px solid {t["border"]};
    border-radius: 10px;
    padding: 18px;
}}

QFrame#DashboardCard:hover {{
    border: 1px solid {t["secondary_accent"]};
    background-color: {t["surface_hover"]};
}}

QLabel#CardTitle {{
    color: {t["text_primary"]};
    font-size: 16px;
    font-weight: 600;
    font-family: 'Segoe UI', sans-serif;
}}

QLabel#CardDescription {{
    color: {t["text_secondary"]};
    font-size: 13px;
    line-height: 1.4;
    font-family: 'Segoe UI', sans-serif;
}}

QPushButton#CardActionBtn {{
    background-color: transparent;
    color: {t["accent"]};
    border: 1px solid {t["accent"]};
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 12px;
    font-weight: 600;
    font-family: 'Segoe UI', sans-serif;
}}

QPushButton#CardActionBtn:hover {{
    background-color: {t["accent"]};
    color: #FFFFFF;
}}

/* Kontrol Kartları */
QFrame#PingControlCard, QFrame#DiscoveryControlCard, QFrame#PortControlCard {{
    background-color: {t["surface"]};
    border: 1px solid {t["border"]};
    border-radius: 10px;
}}

QLabel#FieldLabel {{
    color: {t["text_primary"]};
    font-size: 13px;
    font-weight: 500;
    font-family: 'Segoe UI', sans-serif;
}}

QLabel#DiscoveryNoticeLabel {{
    color: {t["secondary_accent"]};
    font-size: 12px;
    font-family: 'Segoe UI', sans-serif;
}}

QLabel#PortSummaryLabel {{
    color: {t["secondary_accent"]};
    font-size: 13px;
    font-weight: bold;
    font-family: 'Segoe UI', sans-serif;
}}

QLineEdit#PingInput, QLineEdit#DiscoveryInput, QLineEdit#PortInput {{
    background-color: {t["input_bg"]};
    color: {t["text_primary"]};
    border: 1px solid {t["border"]};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    font-family: 'Segoe UI', sans-serif;
}}

QLineEdit#PingInput:focus, QLineEdit#DiscoveryInput:focus, QLineEdit#PortInput:focus {{
    border: 1px solid {t["secondary_accent"]};
}}

QDoubleSpinBox#PortTimeoutSpin {{
    background-color: {t["input_bg"]};
    color: {t["text_primary"]};
    border: 1px solid {t["border"]};
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 13px;
    font-family: 'Segoe UI', sans-serif;
}}

QRadioButton#PortRadio {{
    color: {t["text_primary"]};
    font-size: 12px;
    font-family: 'Segoe UI', sans-serif;
}}

QComboBox#PingCombo, QComboBox#DiscoveryCombo {{
    background-color: {t["input_bg"]};
    color: {t["text_primary"]};
    border: 1px solid {t["border"]};
    border-radius: 6px;
    padding: 7px 12px;
    font-size: 13px;
    font-family: 'Segoe UI', sans-serif;
}}

QPushButton#PingStartBtn, QPushButton#DiscoveryStartBtn, QPushButton#PortStartBtn {{
    background-color: {t["accent"]};
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
    font-family: 'Segoe UI', sans-serif;
}}

QPushButton#PingStartBtn:hover, QPushButton#DiscoveryStartBtn:hover, QPushButton#PortStartBtn:hover {{
    background-color: {t["accent_hover"]};
}}

QPushButton#PingStartBtn:disabled, QPushButton#DiscoveryStartBtn:disabled, QPushButton#PortStartBtn:disabled {{
    background-color: {t["border"]};
    color: {t["text_secondary"]};
}}

QPushButton#PingStopBtn, QPushButton#DiscoveryStopBtn, QPushButton#PortStopBtn {{
    background-color: {t["danger"]};
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
    font-family: 'Segoe UI', sans-serif;
}}

QPushButton#PingStopBtn:hover, QPushButton#DiscoveryStopBtn:hover, QPushButton#PortStopBtn:hover {{
    background-color: {t["danger_hover"]};
}}

QPushButton#PingStopBtn:disabled, QPushButton#DiscoveryStopBtn:disabled, QPushButton#PortStopBtn:disabled {{
    background-color: {t["border"]};
    color: {t["text_secondary"]};
}}

QPushButton#PingClearBtn, QPushButton#DiscoveryClearBtn, QPushButton#DiscoveryRefreshBtn, QPushButton#PortClearBtn {{
    background-color: transparent;
    color: {t["text_secondary"]};
    border: 1px solid {t["border"]};
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 13px;
    font-family: 'Segoe UI', sans-serif;
}}

QPushButton#PingClearBtn:hover, QPushButton#DiscoveryClearBtn:hover, QPushButton#DiscoveryRefreshBtn:hover, QPushButton#PortClearBtn:hover {{
    background-color: {t["surface_hover"]};
    color: {t["text_primary"]};
}}

QLabel#PingFeedbackLabel, QLabel#DiscoveryStatusLabel, QLabel#PortStatusLabel {{
    color: {t["text_secondary"]};
    font-size: 12px;
    font-family: 'Segoe UI', sans-serif;
}}

/* İlerleme Çubuğu (QProgressBar) */
QProgressBar#DiscoveryProgressBar {{
    background-color: {t["surface"]};
    border: 1px solid {t["border"]};
    border-radius: 6px;
    text-align: center;
    color: {t["text_primary"]};
    font-size: 11px;
    font-weight: 600;
    height: 18px;
}}

QProgressBar#DiscoveryProgressBar::chunk {{
    background-color: {t["accent"]};
    border-radius: 5px;
}}

QCheckBox#DiscoveryFilterCheck {{
    color: {t["text_secondary"]};
    font-size: 12px;
    font-family: 'Segoe UI', sans-serif;
}}

/* Sonuç Tablosu (QTableWidget) */
QTableWidget#DiscoveryTable {{
    background-color: {t["surface"]};
    color: {t["text_primary"]};
    border: 1px solid {t["border"]};
    border-radius: 8px;
    gridline-color: {t["border"]};
    font-size: 13px;
    font-family: 'Segoe UI', sans-serif;
}}

QTableWidget#DiscoveryTable QHeaderView::section {{
    background-color: {t["table_header_bg"]};
    color: {t["text_primary"]};
    border: none;
    border-bottom: 1px solid {t["border"]};
    padding: 8px;
    font-weight: 600;
}}

QPushButton#TablePingBtn, QPushButton#TablePortBtn {{
    background-color: transparent;
    color: {t["secondary_accent"]};
    border: 1px solid {t["secondary_accent"]};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 500;
}}

QPushButton#TablePingBtn:hover, QPushButton#TablePortBtn:hover {{
    background-color: {t["secondary_accent"]};
    color: #FFFFFF;
}}

/* Ping İstatistik Paneli */
QFrame#PingStatsFrame {{
    background-color: {t["surface"]};
    border: 1px solid {t["border"]};
    border-radius: 8px;
}}

QLabel#StatTitle {{
    color: {t["text_secondary"]};
    font-size: 12px;
    font-family: 'Segoe UI', sans-serif;
}}

QLabel#StatValue {{
    color: {t["secondary_accent"]};
    font-size: 13px;
    font-weight: bold;
    font-family: 'Segoe UI', sans-serif;
}}

/* Canlı Konsol Çıktısı */
QPlainTextEdit#PingConsole {{
    background-color: {t["console_bg"]};
    color: {t["text_primary"]};
    border: 1px solid {t["border"]};
    border-radius: 8px;
    padding: 10px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
}}

/* Yer Tutucu (Placeholder) Sayfalar */
QFrame#PlaceholderCard {{
    background-color: {t["surface"]};
    border: 1px dashed {t["border"]};
    border-radius: 12px;
    padding: 40px;
}}

QLabel#PlaceholderTitle {{
    color: {t["text_primary"]};
    font-size: 18px;
    font-weight: 600;
    font-family: 'Segoe UI', sans-serif;
}}

QLabel#PlaceholderMessage {{
    color: {t["text_secondary"]};
    font-size: 13px;
    font-family: 'Segoe UI', sans-serif;
}}

/* Alt Durum Çubuğu */
QFrame#FooterFrame {{
    background-color: {t["footer_bg"]};
    border-top: 1px solid {t["border"]};
}}

QLabel#FooterStatusLabel {{
    color: {t["text_secondary"]};
    font-size: 12px;
    font-family: 'Segoe UI', sans-serif;
}}

QLabel#FooterThemeLabel {{
    color: {t["secondary_accent"]};
    font-size: 12px;
    font-weight: 500;
    font-family: 'Segoe UI', sans-serif;
}}

QLabel#FooterVersionLabel {{
    color: {t["text_secondary"]};
    font-size: 12px;
    font-family: 'Segoe UI', sans-serif;
}}
"""
