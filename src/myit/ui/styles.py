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
        "icon_color": "#94A3B8",
        "icon_active": "#38BDF8",
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
        "icon_color": "#53657D",
        "icon_active": "#1D4ED8",
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

QPushButton#CardActionBtn:pressed {{
    background-color: {t["accent_hover"]};
    color: #FFFFFF;
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
