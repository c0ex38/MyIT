"""Traceroute servisi ve çıktı ayrıştırma motoru.

Bu modül; Windows tracert.exe sürecini güvenli parametrelerle çalıştıran,
gerçek zamanlı hop çıktısını ayrıştıran ve QThread üzerinde çalışan
TracerouteWorker bileşenini barındırır.
"""

from dataclasses import dataclass
import ipaddress
import re
import subprocess
from typing import List, Optional, Tuple
from PySide6.QtCore import QObject, Signal

from myit.modules.network.ping_service import HOSTNAME_REGEX, validate_target


@dataclass
class HopResult:
    """Tek bir ağ atlama noktası (Hop) veri modeli."""
    hop_num: int
    rtt1: str = "*"
    rtt2: str = "*"
    rtt3: str = "*"
    ip_or_host: str = "*"
    status: str = "Yanıt Alındı"  # "Yanıt Alındı", "Zaman Aşımı (*)", "Kısmi Yanıt", "Hedefe Ulaşıldı"


# Hop satırı regex'i:
# Örnek: "  1    <1 ms    <1 ms    <1 ms  192.168.1.1 "
# Örnek: "  2     *        *        *     Request timed out."
# Örnek: "  3    12 ms     *       14 ms  10.0.0.1 "
HOP_LINE_REGEX = re.compile(
    r"^\s*(\d+)\s+([<0-9\*\s]+ms|\*)\s+([<0-9\*\s]+ms|\*)\s+([<0-9\*\s]+ms|\*)\s+(.+)$",
    re.IGNORECASE,
)


def validate_traceroute_target(target: str) -> Tuple[bool, str, str]:
    """Traceroute hedefini doğrular.

    Returns:
        (is_valid, error_message, cleaned_target)
    """
    clean_val = (target or "").strip()
    if not clean_val:
        return False, "Hedef adres boş olamaz.", ""

    # CLI enjeksiyonu ve komut karakterleri kontrolü
    if clean_val.startswith("-") or clean_val.startswith("/"):
        return False, "Geçersiz hedef: Parametre formatında değer girilemez.", ""

    if any(prefix in clean_val.lower() for prefix in ("http://", "https://", "ftp://")):
        return False, "Lütfen URL yerine yalnızca IP veya alan adı girin (http/https olmadan).", ""

    if any(c in clean_val for c in " \t\r\n;&|`$><\"'/?#\\"):
        return False, "Geçersiz hedef: Boşluk veya özel komut karakteri içeremez.", ""

    # 1. IP adresi mi? (IPv4 / IPv6)
    try:
        ip_obj = ipaddress.ip_address(clean_val)
        return True, "", str(ip_obj)
    except ValueError:
        pass

    # 2. Hostname mi?
    # Port ayrımı için ':' yasaklanmıştı, dolayısıyla hostname doğrulaması:
    if ":" in clean_val:
        return False, "Geçersiz hedef: Hostname içinde iki nokta (:) bulunamaz.", ""

    if HOSTNAME_REGEX.match(clean_val):
        return True, "", clean_val

    return False, "Geçersiz hedef formatı. Lütfen geçerli bir IPv4, IPv6 veya alan adı girin.", ""


def validate_traceroute_params(max_hops: int, timeout_ms: int) -> Tuple[bool, str]:
    """Maksimum hop ve zaman aşımı sınırlarını denetler."""
    if not (1 <= max_hops <= 30):
        return False, f"Maksimum hop sayısı 1 ile 30 arasında olmalıdır (Girilen: {max_hops})."

    if not (250 <= timeout_ms <= 5000):
        return False, f"Hop başına zaman aşımı 250 ile 5000 ms arasında olmalıdır (Girilen: {timeout_ms})."

    return True, ""


def build_tracert_args(
    target: str,
    max_hops: int = 20,
    timeout_ms: int = 1000,
    ip_version: str = "AUTO",  # "AUTO", "IPV4", "IPV6"
) -> List[str]:
    """tracert.exe komut argüman listesini güvenle oluşturur."""
    args = ["tracert.exe", "-d", "-h", str(max_hops), "-w", str(timeout_ms)]

    if ip_version.upper() == "IPV4":
        args.append("-4")
    elif ip_version.upper() == "IPV6":
        args.append("-6")

    args.append(target)
    return args


def parse_hop_line(line: str, target_host: str = "") -> Optional[HopResult]:
    """Windows tracert çıktısındaki tekil bir satırı inceler ve HopResult üretir."""
    clean_line = line.strip()
    if not clean_line:
        return None

    # Başlık veya bilgilendirme satırlarını atla
    if clean_line.startswith("Tracing route") or clean_line.startswith("Trace complete"):
        return None
    if "over a maximum of" in clean_line:
        return None

    match = HOP_LINE_REGEX.match(clean_line)
    if not match:
        return None

    hop_num_str, r1_raw, r2_raw, r3_raw, host_raw = match.groups()

    hop_num = int(hop_num_str)
    r1 = r1_raw.strip()
    r2 = r2_raw.strip()
    r3 = r3_raw.strip()
    host_candidate = host_raw.strip()

    # Zaman aşımı durumları (Request timed out / İstek zaman aşımına uğradı vb.)
    is_timeout = (r1 == "*" and r2 == "*" and r3 == "*")
    if is_timeout or any(kw in host_candidate.lower() for kw in ("timed out", "zaman aşımı", "unreachable")):
        if is_timeout:
            return HopResult(
                hop_num=hop_num,
                rtt1="*",
                rtt2="*",
                rtt3="*",
                ip_or_host="*",
                status="Zaman Aşımı (*)",
            )

    # Kısmi yanıt durumu
    is_partial = any(r == "*" for r in (r1, r2, r3))

    # Hedefe ulaşıldı mı?
    is_target_reached = False
    if target_host and target_host in host_candidate:
        is_target_reached = True

    status = "Hedefe Ulaşıldı" if is_target_reached else ("Kısmi Yanıt" if is_partial else "Yanıt Alındı")

    return HopResult(
        hop_num=hop_num,
        rtt1=r1,
        rtt2=r2,
        rtt3=r3,
        ip_or_host=host_candidate,
        status=status,
    )


class TracerouteWorker(QObject):
    """tracert.exe sürecini asenkron yürüten ve çıktıları yayan iş parçacığı."""

    hop_received = Signal(object)       # HopResult nesnesi
    status_changed = Signal(str)       # Bilgilendirme mesajı
    finished = Signal()                # Süreç bitti
    error_occurred = Signal(str)       # Hata sinyali

    def __init__(
        self,
        target: str,
        max_hops: int = 20,
        timeout_ms: int = 1000,
        ip_version: str = "AUTO",
    ):
        super().__init__()
        self.target = target
        self.max_hops = max_hops
        self.timeout_ms = timeout_ms
        self.ip_version = ip_version

        self._is_stopped = False
        self._process: Optional[subprocess.Popen] = None

    def stop(self):
        """Çalışan tracert.exe sürecini güvenle sonlandırır."""
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
        """Traceroute sürecini başlatır ve çıktıları canlı satır satır okur."""
        cmd_args = build_tracert_args(
            target=self.target,
            max_hops=self.max_hops,
            timeout_ms=self.timeout_ms,
            ip_version=self.ip_version,
        )

        try:
            self.status_changed.emit(f"Traceroute başlatılıyor: {self.target} (Maks. {self.max_hops} hop)...")

            # CREATE_NO_WINDOW ile konsol penceresi açılmasını engelle
            creation_flags = 0x08000000
            self._process = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="cp857",
                errors="replace",
                bufsize=1,
                creationflags=creation_flags,
            )

            for line in iter(self._process.stdout.readline, ""):
                if self._is_stopped:
                    break

                clean_line = line.strip()
                if not clean_line:
                    continue

                # Hop satırını ayrıştır
                hop_res = parse_hop_line(clean_line, target_host=self.target)
                if hop_res:
                    self.hop_received.emit(hop_res)

            self._process.stdout.close()
            self._process.wait()

            if self._is_stopped:
                self.status_changed.emit("Traceroute işlemi kullanıcı tarafından durduruldu.")
            else:
                self.status_changed.emit("Güzergah analizi tamamlandı.")

        except Exception as exc:
            self.error_occurred.emit(f"Traceroute yürütme hatası: {str(exc)}")
        finally:
            self.stop()
            self.finished.emit()
