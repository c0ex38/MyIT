"""TCP Port Tarayıcı servisi ve doğrulama mantığı.

Bu modül; port aralıklarını ayrıştıran, geçerli port listeleri üreten,
Python soketleri (TCP connect) ile hedefteki portların durumunu kontrol eden
ve asenkron tarama iş parçacığını barındıran çekirdek servistir.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import errno
import re
import socket
from typing import Dict, List, Optional, Set, Tuple
from PySide6.QtCore import QObject, Signal

from myit.modules.network.ping_service import validate_target

# Yaygın standart portlar ve bilinen servis etiketleri
COMMON_PORTS: List[int] = [
    21, 22, 25, 53, 80, 110, 135, 139, 143, 443, 445, 587,
    993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 5985, 5986, 8080, 8443
]

PORT_SERVICE_MAP: Dict[int, str] = {
    21: "FTP",
    22: "SSH",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    135: "RPC",
    139: "NetBIOS",
    143: "IMAP",
    443: "HTTPS",
    445: "SMB",
    587: "SMTP (Submission)",
    993: "IMAPS",
    995: "POP3S",
    1433: "MS SQL",
    1521: "Oracle DB",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    5985: "WinRM (HTTP)",
    5986: "WinRM (HTTPS)",
    8080: "HTTP Proxy/Alt",
    8443: "HTTPS Alt",
}

MAX_PORTS_PER_SCAN = 256


@dataclass
class PortScanResult:
    """Tekil bir portun tarama sonuç modeli."""
    port: int
    protocol: str = "TCP"
    status: str = "Bilinmiyor"  # "Açık", "Kapalı", "Zaman Aşımı / Filtreli", "Hata"
    service: str = "Bilinmiyor"
    latency: Optional[float] = None
    error_message: Optional[str] = None


def get_known_service_name(port: int) -> str:
    """Port numarasına karşılık gelen yaygın bilinen servis etiketini döndürür."""
    if port in PORT_SERVICE_MAP:
        return f"{PORT_SERVICE_MAP[port]} (yaygın)"
    try:
        service_name = socket.getservbyport(port, "tcp")
        return f"{service_name.upper()} (sistem)"
    except Exception:
        return "Bilinmiyor"


def parse_port_expression(expression: str) -> Tuple[bool, str, List[int]]:
    """Kullanıcının girdiği port ifadesini (örn. '80,443,3389' veya '20-25,80') ayrıştırır.

    Kurallar:
    - Portlar 1 ile 65535 arasında olmalıdır.
    - Tekrarlar elenir ve liste küçükten büyüğe sıralanır.
    - Tek bir taramada en fazla 256 port desteklenir.

    Returns:
        (is_valid, error_message, sorted_unique_ports)
    """
    clean_expr = (expression or "").strip()
    if not clean_expr:
        return False, "Port listesi boş olamaz.", []

    # Geçersiz karakter kontrolü
    if not re.match(r"^[0-9,\-\s]+$", clean_expr):
        return False, "Port listesi yalnızca sayılar, virgül (,) ve tire (-) içerebilir.", []

    ports_set: Set[int] = set()
    parts = [p.strip() for p in clean_expr.split(",") if p.strip()]

    if not parts:
        return False, "Geçerli bir port numarası bulunamadı.", []

    for part in parts:
        if "-" in part:
            range_parts = part.split("-")
            if len(range_parts) != 2:
                return False, f"Geçersiz aralık formatı: '{part}'", []

            start_str, end_str = range_parts[0].strip(), range_parts[1].strip()
            if not start_str.isdigit() or not end_str.isdigit():
                return False, f"Aralık değerleri sayı olmalıdır: '{part}'", []

            start, end = int(start_str), int(end_str)
            if start < 1 or end > 65535:
                return False, f"Port numaraları 1-65535 arasında olmalıdır ({start}-{end}).", []

            if start > end:
                return False, f"Başlangıç portu bitiş portundan büyük olamaz: '{part}'", []

            # Aşırı geniş aralık denetimi
            if (end - start + 1) > MAX_PORTS_PER_SCAN:
                return False, f"Tek bir aralıkta en fazla {MAX_PORTS_PER_SCAN} port taranabilir.", []

            for port_num in range(start, end + 1):
                ports_set.add(port_num)
        else:
            if not part.isdigit():
                return False, f"Geçersiz port numarası: '{part}'", []

            port_num = int(part)
            if port_num < 1 or port_num > 65535:
                return False, f"Port numarası 1-65535 arasında olmalıdır: {port_num}", []

            ports_set.add(port_num)

    sorted_ports = sorted(list(ports_set))

    if len(sorted_ports) > MAX_PORTS_PER_SCAN:
        return (
            False,
            f"Toplam {len(sorted_ports)} port seçildi. Bir taramada en fazla {MAX_PORTS_PER_SCAN} port taranabilir.",
            [],
        )

    return True, "", sorted_ports


def scan_single_tcp_port(target_ip: str, port: int, timeout_sec: float = 0.7) -> PortScanResult:
    """Tek bir TCP portuna soket connect() ile erişim durumunu test eder."""
    import time
    start_time = time.perf_counter()

    result = PortScanResult(
        port=port,
        protocol="TCP",
        service=get_known_service_name(port),
    )

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout_sec)

    try:
        sock.connect((target_ip, port))
        latency = (time.perf_counter() - start_time) * 1000.0
        result.status = "Açık"
        result.latency = round(latency, 1)
    except socket.timeout:
        result.status = "Zaman Aşımı / Filtreli"
    except ConnectionRefusedError:
        result.status = "Kapalı"
    except OSError as err:
        if err.errno in (errno.ECONNREFUSED, 10061):  # WSAECONNREFUSED
            result.status = "Kapalı"
        elif err.errno in (errno.ETIMEDOUT, 10060):   # WSAETIMEDOUT
            result.status = "Zaman Aşımı / Filtreli"
        else:
            result.status = "Hata"
            result.error_message = str(err)
    except Exception as exc:
        result.status = "Hata"
        result.error_message = str(exc)
    finally:
        try:
            sock.close()
        except Exception:
            pass

    return result


class PortScanWorker(QObject):
    """Hedef IP üzerinde eşzamanlı TCP port taraması yapan iş parçacığı."""

    port_scanned = Signal(object)       # PortScanResult nesnesi
    progress_updated = Signal(int, int) # (tamamlanan, toplam)
    status_changed = Signal(str)        # Bilgilendirme metni
    finished = Signal()                 # Tarama bitti
    error_occurred = Signal(str)        # Hata sinyali

    MAX_CONCURRENCY = 16

    def __init__(self, target_host: str, ports: List[int], timeout_sec: float = 0.7):
        super().__init__()
        self.target_host = target_host
        self.ports = ports
        self.timeout_sec = timeout_sec
        self._is_stopped = False

    def stop(self):
        """Taramayı durdurur ve yeni soket bağlantıları açılmasını engeller."""
        self._is_stopped = True

    def run(self):
        """Port taramasını başlatır."""
        try:
            # 1. Hedef IP'yi çözümle
            self.status_changed.emit(f"Hedef adres çözümleniyor: {self.target_host}...")
            try:
                resolved_ip = socket.gethostbyname(self.target_host)
            except Exception:
                self.error_occurred.emit(f"Hedef adres çözümlenemedi (DNS hatası): {self.target_host}")
                self.finished.emit()
                return

            total_ports = len(self.ports)
            if total_ports == 0:
                self.error_occurred.emit("Taranacak port bulunamadı.")
                self.finished.emit()
                return

            self.status_changed.emit(
                f"Tarama başladı: {self.target_host} ({resolved_ip}) — {total_ports} port kontrol ediliyor..."
            )

            completed_count = 0
            with ThreadPoolExecutor(max_workers=self.MAX_CONCURRENCY) as executor:
                future_to_port = {
                    executor.submit(self._scan_task, resolved_ip, port): port
                    for port in self.ports
                }

                for future in as_completed(future_to_port):
                    if self._is_stopped:
                        break

                    completed_count += 1
                    res = future.result()
                    self.port_scanned.emit(res)
                    self.progress_updated.emit(completed_count, total_ports)

            if self._is_stopped:
                self.status_changed.emit("Tarama kullanıcı tarafından durduruldu.")
            else:
                self.status_changed.emit("Port taraması tamamlandı.")

        except Exception as exc:
            self.error_occurred.emit(f"Tarama sırasında beklenmeyen hata: {str(exc)}")
        finally:
            self.finished.emit()

    def _scan_task(self, target_ip: str, port: int) -> PortScanResult:
        """Havuzdaki tekil port görevi."""
        if self._is_stopped:
            return PortScanResult(port=port, status="Durduruldu")
        return scan_single_tcp_port(target_ip, port, timeout_sec=self.timeout_sec)
