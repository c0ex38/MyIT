"""Ping servisi ve doğrulama mantığı.

Bu modül, Windows ping.exe sürecini güvenli parametrelerle yöneten,
girdiyi doğrulayan ve QThread tabanlı arka plan ping görevini barındırır.
"""

from dataclasses import dataclass
from datetime import datetime
import ipaddress
import re
import subprocess
from typing import Optional, Tuple
from PySide6.QtCore import QObject, QThread, Signal


# Alan adı / hostname doğrulama regex'i (RFC 1123)
HOSTNAME_REGEX = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$"
)

# Yanıt satırlarından gecikme (ms) ayıklama regex'i (TR/EN uyumlu: time=12ms, time<1ms, süre=12ms, süre<1ms)
TIME_REGEX = re.compile(r"(?:time|süre)[<=](\d+)\s*ms", re.IGNORECASE)
TIMEOUT_KEYWORDS = [
    "timed out",
    "zaman aşımı",
    "unreachable",
    "ulaşılamıyor",
    "failure",
    "başarısız",
    "could not find host",
    "bulunamadı",
]


def validate_target(target: str) -> Tuple[bool, str]:
    """Ping hedefini (IP veya Hostname) güvenli şekilde doğrular.

    Args:
        target: Kullanıcının girdiği hedef metin.

    Returns:
        (is_valid, error_message_or_cleaned_target)
    """
    cleaned = (target or "").strip()

    if not cleaned:
        return False, "Hedef IP adresi veya alan adı boş olamaz."

    # Parametre enjeksiyonuna karşı kontrol (örn. '-n 1', '/w 100')
    if cleaned.startswith("-") or cleaned.startswith("/"):
        return False, "Geçersiz hedef: Parametre formatında değer girilemez."

    # Boşluk veya zararlı karakter kontrolü
    if any(c in cleaned for c in " \t\r\n;&|`$><\"'"):
        return False, "Geçersiz hedef: Boşluk veya özel komut karakteri içeremez."

    # 1. IP adresi mi? (IPv4 / IPv6)
    try:
        ipaddress.ip_address(cleaned)
        return True, cleaned
    except ValueError:
        pass

    # 2. Geçerli bir hostname / alan adı mı?
    if HOSTNAME_REGEX.match(cleaned):
        return True, cleaned

    return False, "Geçersiz hedef formatı. Lütfen geçerli bir IPv4, IPv6 veya alan adı girin."


@dataclass
class PingStatistics:
    """Canlı ping istatistik veri modeli."""
    sent: int = 0
    received: int = 0
    lost: int = 0
    loss_percent: float = 0.0
    avg_latency: Optional[float] = None


class PingWorker(QObject):
    """Ping.exe sürecini asenkron çalıştıran ve çıktıları yayan iş parçacığı (Worker)."""

    # Sinyaller
    line_received = Signal(str)           # Zaman damgalı satır çıktısı
    stats_updated = Signal(object)        # PingStatistics nesnesi
    finished = Signal()                   # İşlem bittiğinde tetiklenir
    error_occurred = Signal(str)          # Hata durumunda tetiklenir

    def __init__(self, target: str, continuous: bool = False, count: int = 4):
        super().__init__()
        self.target = target
        self.continuous = continuous
        self.count = count
        self._is_stopped = False
        self._process: Optional[subprocess.Popen] = None

        self._stats = PingStatistics()
        self._latencies = []

    def stop(self):
        """Çalışan ping sürecini sonlandırır."""
        self._is_stopped = True
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass

    def run(self):
        """Ping sürecini başlatır ve çıktı satırlarını canlı okur."""
        # Komut argümanları (shell=False ile güvenli çalıştırma)
        args = ["ping.exe"]
        if self.continuous:
            args.append("-t")
        else:
            args.extend(["-n", str(self.count)])
        args.append(self.target)

        try:
            # CREATE_NO_WINDOW bayrağı ile arka planda penceresiz çalıştırma
            creation_flags = 0x08000000  # win32 subprocess.CREATE_NO_WINDOW
            self._process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="cp857",  # Windows Türkçe/Türkçe DOS OEM veya UTF-8 toleranslı
                errors="replace",
                creationflags=creation_flags,
                bufsize=1,
            )

            for line in iter(self._process.stdout.readline, ""):
                if self._is_stopped:
                    break

                line_clean = line.strip()
                if not line_clean:
                    continue

                now_str = datetime.now().strftime("%H:%M:%S")
                formatted_line = f"[{now_str}] {line_clean}"
                self.line_received.emit(formatted_line)

                # İstatistikleri satırdan ayrıştır
                self._process_line_stats(line_clean)

            self._process.stdout.close()
            self._process.wait()

        except Exception as exc:
            self.error_occurred.emit(f"Ping işlemi sırasında hata oluştu: {str(exc)}")
        finally:
            self.stop()
            self.finished.emit()

    def _process_line_stats(self, line: str):
        """Satırdaki gecikme veya paket kaybı bilgisini inceler."""
        line_lower = line.lower()

        # Yanıt satırı kontrolü
        time_match = TIME_REGEX.search(line)
        if time_match:
            latency = float(time_match.group(1))
            self._stats.sent += 1
            self._stats.received += 1
            self._latencies.append(latency)
            self._stats.avg_latency = round(sum(self._latencies) / len(self._latencies), 1)
        elif any(keyword in line_lower for keyword in TIMEOUT_KEYWORDS):
            self._stats.sent += 1
            self._stats.lost += 1

        if self._stats.sent > 0:
            self._stats.loss_percent = round((self._stats.lost / self._stats.sent) * 100, 1)

        self.stats_updated.emit(self._stats)
