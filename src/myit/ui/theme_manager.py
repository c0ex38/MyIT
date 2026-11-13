"""MyIT tema yöneticisi.

Bu modül, uygulamanın anlık tema durumunu (koyu/açık) tutar ve
tema değiştiğinde dinleyicilere sinyal yayar. Bellekte (RAM) çalışır;
ayarlar hiçbir dosyaya kaydedilmez.
"""

from PySide6.QtCore import QObject, Signal


class ThemeManager(QObject):
    """Çalışma zamanı tema durum yöneticisi."""

    # Tema değiştiğinde yeni tema adını yayan sinyal ('dark' veya 'light')
    theme_changed = Signal(str)

    def __init__(self):
        super().__init__()
        # Varsayılan tema daima KOYU (Midnight Blue)
        self._current_theme: str = "dark"

    @property
    def current_theme(self) -> str:
        """Geçerli tema anahtarını döndürür ('dark' veya 'light')."""
        return self._current_theme

    @property
    def theme_display_name(self) -> str:
        """Geçerli temanın Türkçe görünen adını döndürür."""
        return "Koyu Tema" if self._current_theme == "dark" else "Açık Tema"

    def toggle_theme(self) -> str:
        """Temayı koyu ile açık arasında değiştirir ve sinyal tetikler."""
        self._current_theme = "light" if self._current_theme == "dark" else "dark"
        self.theme_changed.emit(self._current_theme)
        return self._current_theme

    def set_theme(self, theme_key: str):
        """Belirli bir temayı ayarlar ('dark' veya 'light')."""
        if theme_key in ("dark", "light") and theme_key != self._current_theme:
            self._current_theme = theme_key
            self.theme_changed.emit(self._current_theme)
