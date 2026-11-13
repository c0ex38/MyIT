"""Ağ keşfi (Network Discovery) servisi.

Bu modül; aktif ağ bağdaştırıcılarını tespit eden, yerel CIDR aralığını
hesaplayan, eşzamanlı olarak IP hedeflerini ICMP ping ile yoklayan,
ters DNS ve ARP tablosundan MAC sorgulayan arka plan tarama motorunu içerir.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import ipaddress
import json
import re
import socket
import subprocess
from typing import Dict, List, Optional, Tuple
from PySide6.QtCore import QObject, Signal

from myit.modules.network.ping_service import TIME_REGEX


@dataclass
class NetworkAdapterInfo:
    """Ağ bağdaştırıcı veri modeli."""
    alias: str
    ip_address: str
    prefix_length: int
    gateway: Optional[str] = None

    @property
    def cidr(self) -> str:
        """Hesaplanan CIDR ağ adresini döndürür (Örn: 192.168.1.0/24)."""
        try:
            net = ipaddress.IPv4Network(f"{self.ip_address}/{self.prefix_length}", strict=False)
            return str(net)
        except Exception:
            return f"{self.ip_address}/24"


@dataclass
class DiscoveredDevice:
    """Ağda tespit edilen cihaz veri modeli."""
    ip: str
    hostname: str = "-"
    mac_address: str = "-"
    status: str = "Yanıtsız"  # "Erişilebilir", "Yanıtsız", "Belirsiz"
    latency: Optional[float] = None
    is_gateway: bool = False


def get_network_adapters() -> List[NetworkAdapterInfo]:
    """Sistemdeki aktif IPv4 ağ bağdaştırıcılarını ve varsayılan ağ geçitlerini tespit eder."""
    adapters: List[NetworkAdapterInfo] = []

    # 1. Varsayılan ağ geçitlerini öğren
    gateways: Dict[str, str] = {}
    try:
        gw_cmd = [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | Select-Object InterfaceAlias, NextHop | ConvertTo-Json -Compress",
        ]
        res = subprocess.run(gw_cmd, capture_output=True, text=True, timeout=5, creationflags=0x08000000)
        if res.returncode == 0 and res.stdout.strip():
            raw_gw = json.loads(res.stdout.strip())
            if isinstance(raw_gw, dict) and "InterfaceAlias" in raw_gw:
                gateways[raw_gw["InterfaceAlias"]] = raw_gw.get("NextHop", "")
            elif isinstance(raw_gw, list):
                for item in raw_gw:
                    if isinstance(item, dict) and "InterfaceAlias" in item:
                        gateways[item["InterfaceAlias"]] = item.get("NextHop", "")
    except Exception:
        pass

    # 2. IPv4 adreslerini ve prefix uzunluklarını al
    try:
        ip_cmd = [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } | Select-Object InterfaceAlias, IPAddress, PrefixLength | ConvertTo-Json -Compress",
        ]
        res = subprocess.run(ip_cmd, capture_output=True, text=True, timeout=5, creationflags=0x08000000)
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout.strip())
            items = [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])
            for item in items:
                alias = item.get("InterfaceAlias", "Ağ")
                ip = item.get("IPAddress", "")
                prefix = item.get("PrefixLength", 24)
                if ip:
                    gw = gateways.get(alias)
                    adapters.append(NetworkAdapterInfo(alias=alias, ip_address=ip, prefix_length=prefix, gateway=gw))
    except Exception:
        pass

    return adapters


def validate_cidr(cidr_str: str) -> Tuple[bool, str, Optional[ipaddress.IPv4Network]]:
    """Girilen CIDR aralığını doğrular ve güvenlik sınırlarını kontrol eder.

    Returns:
        (is_valid, message, network_object)
    """
    clean_str = (cidr_str or "").strip()
    if not clean_str:
        return False, "CIDR aralığı boş olamaz.", None

    try:
        net = ipaddress.IPv4Network(clean_str, strict=False)
    except Exception:
        return False, "Geçersiz CIDR formatı. (Örn: 192.168.1.0/24)", None

    # Güvenlik ve aralık sınırları
    if net.is_loopback:
        return False, "Geri döngü (Loopback - 127.0.0.0/8) adresleri taranamaz.", None

    if net.is_multicast:
        return False, "Multicast (224.0.0.0+) adresleri taranamaz.", None

    if net.is_link_local:
        return False, "Link-local (169.254.0.0/16) adresleri taranamaz.", None

    if net.is_global:
        return False, "Güvenlik kuralı: İnternet geneli (Public) IP blokları taranamaz. Yalnızca yerel ağınızı tarayın.", None

    # /24 sınırı (en fazla 256 adres, 254 kullanılabilir host)
    if net.prefixlen < 24:
        return False, f"Tarama aralığı çok geniş (/{net.prefixlen}). İlk sürümde en fazla /24 (maks. 254 cihaz) desteklenmektedir.", None

    return True, "Geçerli yerel CIDR aralığı.", net


def get_arp_table() -> Dict[str, str]:
    """Windows 'arp -a' çıktısını okuyarak IP -> MAC haritasını döndürür."""
    arp_map: Dict[str, str] = {}
    try:
        res = subprocess.run(["arp", "-a"], capture_output=True, text=True, errors="replace", creationflags=0x08000000)
        if res.returncode == 0:
            # Satır örnek: 192.168.1.1  98-3f-a4-e0-12-fb  dynamic
            for line in res.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2:
                    ip_candidate, mac_candidate = parts[0], parts[1]
                    # MAC formatı kontrolü (xx-xx-xx-xx-xx-xx)
                    if re.match(r"^([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})$", mac_candidate):
                        arp_map[ip_candidate] = mac_candidate.upper().replace("-", ":")
    except Exception:
        pass
    return arp_map


def resolve_hostname(ip: str) -> str:
    """Ters DNS (Reverse DNS) sorgusu yapar; bulunamazsa '-' döndürür."""
    try:
        host, _, _ = socket.gethostbyaddr(ip)
        return host or "-"
    except Exception:
        return "-"


def probe_single_ip(ip: str, timeout_ms: int = 1000) -> Tuple[bool, Optional[float]]:
    """Tekil bir IP'ye tek bir ICMP ping paketi gönderir.

    Returns:
        (is_reachable, latency_ms)
    """
    args = ["ping.exe", "-n", "1", "-w", str(timeout_ms), ip]
    try:
        res = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="cp857",
            errors="replace",
            timeout=max(2.0, (timeout_ms / 1000.0) + 1.0),
            creationflags=0x08000000,
        )
        output = res.stdout or ""
        time_match = TIME_REGEX.search(output)
        if time_match:
            latency = float(time_match.group(1))
            return True, latency
        return False, None
    except Exception:
        return False, None


class DiscoveryWorker(QObject):
    """Eşzamanlı ağ keşfi yapan arka plan iş parçacığı."""

    device_found = Signal(object)       # DiscoveredDevice nesnesi
    progress_updated = Signal(int, int) # (taranan, toplam)
    status_changed = Signal(str)        # Bilgi mesajı
    finished = Signal()                 # Tarama tamamlandı
    error_occurred = Signal(str)        # Hata mesajı

    MAX_CONCURRENCY = 16

    def __init__(self, network: ipaddress.IPv4Network, gateway_ip: Optional[str] = None):
        super().__init__()
        self.network = network
        self.gateway_ip = gateway_ip
        self._is_stopped = False

    def stop(self):
        """Taramayı iptal eder."""
        self._is_stopped = True

    def run(self):
        """Taramayı başlatır ve her bulunan sonucu anında bildirir."""
        try:
            # Ağ ve broadcast adreslerini dışlayarak host listesini al
            hosts = [str(ip) for ip in self.network.hosts()]
            total_hosts = len(hosts)

            if total_hosts == 0:
                self.error_occurred.emit("Taranacak geçerli IP adresi bulunamadı.")
                self.finished.emit()
                return

            self.status_changed.emit(f"ARP tablosu okunuyor ve {total_hosts} IP hazırlanıyor...")
            arp_map = get_arp_table()

            self.status_changed.emit(f"Tarama başladı: {self.network} ({total_hosts} hedef)")
            scanned_count = 0

            with ThreadPoolExecutor(max_workers=self.MAX_CONCURRENCY) as executor:
                # Görevleri gönder
                future_to_ip = {executor.submit(self._scan_host, ip, arp_map): ip for ip in hosts}

                for future in as_completed(future_to_ip):
                    if self._is_stopped:
                        break

                    scanned_count += 1
                    device = future.result()
                    self.device_found.emit(device)
                    self.progress_updated.emit(scanned_count, total_hosts)

            if self._is_stopped:
                self.status_changed.emit("Tarama kullanıcı tarafından durduruldu.")
            else:
                self.status_changed.emit("Ağ taraması tamamlandı.")

        except Exception as exc:
            self.error_occurred.emit(f"Tarama hatası: {str(exc)}")
        finally:
            self.finished.emit()

    def _scan_host(self, ip: str, arp_map: Dict[str, str]) -> DiscoveredDevice:
        """Tek bir cihazı sorgular."""
        if self._is_stopped:
            return DiscoveredDevice(ip=ip, status="Yanıtsız")

        reachable, latency = probe_single_ip(ip, timeout_ms=1000)

        mac = arp_map.get(ip, "-")
        hostname = "-"

        # Erişilebilirse ters DNS çözmeyi dene
        if reachable:
            status = "Erişilebilir"
            hostname = resolve_hostname(ip)
        else:
            status = "Yanıtsız"

        is_gw = (ip == self.gateway_ip)
        return DiscoveredDevice(
            ip=ip,
            hostname=hostname,
            mac_address=mac,
            status=status,
            latency=latency,
            is_gateway=is_gw,
        )
