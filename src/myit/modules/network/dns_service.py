"""DNS sorgu servisi ve veri modelleri.

Bu modül; alan adı doğrulama, DNS sunucu IP kontrolü, dnspython kütüphanesi
ile A, AAAA, MX, NS, TXT, CNAME, SOA kayıtlarını asenkron sorgulama ve
hata sınıflandırma işlevlerini sağlar.
"""

from dataclasses import dataclass
import ipaddress
import re
from typing import Any, List, Optional, Tuple
from PySide6.QtCore import QObject, Signal

import dns.exception
import dns.rdatatype
import dns.resolver


# Desteklenen temel ve ek DNS kayıt türleri
SUPPORTED_RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]


@dataclass
class DnsRecordItem:
    """Tekil bir DNS kaydı sonuç modeli."""
    record_type: str
    value: str
    ttl: Optional[int] = None
    extra_info: str = "-"


@dataclass
class DnsQueryResult:
    """Bir kayıt türü sorgusunun genel sonuç modeli."""
    domain: str
    record_type: str
    records: List[DnsRecordItem]
    status_code: str  # "NOERROR", "NXDOMAIN", "NOANSWER", "TIMEOUT", "NONAMESERVERS", "ERROR"
    message: str


def validate_domain(domain_input: str) -> Tuple[bool, str, str]:
    """Alan adı girdisini doğrular ve IDNA formatına normalize eder.

    Returns:
        (is_valid, error_message, normalized_domain)
    """
    clean_val = (domain_input or "").strip()

    if not clean_val:
        return False, "Alan adı boş olamaz.", ""

    # URL, protokol, yol veya port enjeksiyonu kontrolü
    if any(prefix in clean_val.lower() for prefix in ("http://", "https://", "ftp://")):
        return False, "Lütfen URL yerine yalnızca alan adı girin (http/https olmadan).", ""

    if "/" in clean_val or "\\" in clean_val or ":" in clean_val or "?" in clean_val or "#" in clean_val:
        return False, "Alan adı yol, port (:) veya özel URL karakterleri içeremez.", ""

    # Boşluk ve kontrol karakterleri denetimi
    if any(c.isspace() for c in clean_val):
        return False, "Alan adı boşluk içeremez.", ""

    # Sonundaki noktayı temizle (FQDN gösterimi)
    if clean_val.endswith("."):
        clean_val = clean_val[:-1]

    # FQDN uzunluk sınırları: tam uzunluk <= 253, etiket <= 63
    if len(clean_val) > 253:
        return False, "Alan adı toplam uzunluğu 253 karakterden fazla olamaz.", ""

    raw_labels = clean_val.split(".")
    for r_lbl in raw_labels:
        if len(r_lbl) > 63:
            return False, f"Alan adı parçası 63 karakterden uzun olamaz: '{r_lbl}'", ""

    # IDN (Uluslararası alan adı) dönüşümü
    try:
        idna_domain = clean_val.encode("idna").decode("ascii").lower()
    except Exception:
        return False, "Geçersiz alan adı kodlaması (IDNA hatası).", ""

    labels = idna_domain.split(".")
    if len(labels) < 2 and idna_domain != "localhost":
        return False, "Lütfen geçerli bir üst seviye alan adı girin (Örn: example.com).", ""

    label_regex = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")
    for label in labels:
        if not label:
            return False, "Alan adı boş etiket (ardışık nokta) içeremez.", ""
        if len(label) > 63:
            return False, f"Alan adı parçası 63 karakterden uzun olamaz: '{label}'", ""
        if not label_regex.match(label):
            return False, f"Geçersiz alan adı karakterleri: '{label}'", ""

    return True, "", idna_domain


def validate_dns_server(server_input: str) -> Tuple[bool, str, str]:
    """Özel DNS sunucu IP adresini (IPv4 veya IPv6) doğrular.

    Returns:
        (is_valid, error_message, cleaned_ip)
    """
    clean_val = (server_input or "").strip()
    if not clean_val:
        return False, "DNS sunucu IP adresi boş olamaz.", ""

    try:
        ip_obj = ipaddress.ip_address(clean_val)
        return True, "", str(ip_obj)
    except ValueError:
        return False, "Geçersiz DNS sunucu adresi. Lütfen geçerli bir IPv4 veya IPv6 adresi girin.", ""


def create_resolver(custom_server: Optional[str] = None, timeout_sec: float = 2.0) -> dns.resolver.Resolver:
    """Belirtilen ayarlara göre yapılandırılmış bir dns.resolver.Resolver nesnesi üretir."""
    if custom_server:
        # Özel DNS sunucusu seçildiğinde sistem yapılandırmasını ez
        res = dns.resolver.Resolver(configure=False)
        res.nameservers = [custom_server]
    else:
        # Sistem varsayılan DNS çözücüsü
        try:
            res = dns.resolver.Resolver(configure=True)
        except Exception:
            res = dns.resolver.Resolver(configure=False)
            res.nameservers = ["8.8.8.8", "1.1.1.1"]

    res.timeout = timeout_sec
    res.lifetime = timeout_sec * 2.0
    return res


def format_rdata_item(record_type: str, rdata: Any, ttl: Optional[int]) -> DnsRecordItem:
    """Dönen dnspython rdata nesnesini tablo için yapılandırılmış modele çevirir."""
    rec_type_upper = record_type.upper()
    extra = "-"
    val = str(rdata)

    if rec_type_upper == "MX":
        # MX: preference, exchange
        preference = getattr(rdata, "preference", "-")
        exchange = str(getattr(rdata, "exchange", val)).rstrip(".")
        val = exchange
        extra = f"Öncelik: {preference}"

    elif rec_type_upper == "TXT":
        # TXT parçacıklarını kayıpsız ve düzgün birleştir
        strings = getattr(rdata, "strings", None)
        if strings:
            parts = []
            for s in strings:
                if isinstance(s, bytes):
                    parts.append(s.decode("utf-8", errors="replace"))
                else:
                    parts.append(str(s))
            val = "".join(parts)
        else:
            val = val.strip('"')

    elif rec_type_upper in ("NS", "CNAME"):
        val = val.rstrip(".")

    elif rec_type_upper == "SOA":
        # SOA alanları: mname, rname, serial vb.
        mname = str(getattr(rdata, "mname", "")).rstrip(".")
        rname = str(getattr(rdata, "rname", "")).rstrip(".")
        serial = getattr(rdata, "serial", "")
        extra = f"Serial: {serial}, Yönetici: {rname}"
        val = f"Birincil Sunucu: {mname}"

    return DnsRecordItem(record_type=rec_type_upper, value=val, ttl=ttl, extra_info=extra)


def query_single_type(
    domain: str,
    record_type: str,
    resolver: dns.resolver.Resolver
) -> DnsQueryResult:
    """Belirli bir kayıt türü için DNS sorgusu çalıştırır."""
    rec_type_upper = record_type.upper()
    try:
        answers = resolver.resolve(domain, rec_type_upper)
        ttl = answers.rrset.ttl if answers.rrset is not None else None

        records: List[DnsRecordItem] = []
        for rdata in answers:
            item = format_rdata_item(rec_type_upper, rdata, ttl)
            records.append(item)

        return DnsQueryResult(
            domain=domain,
            record_type=rec_type_upper,
            records=records,
            status_code="NOERROR",
            message=f"{len(records)} adet {rec_type_upper} kaydı bulundu.",
        )

    except dns.resolver.NXDOMAIN:
        return DnsQueryResult(
            domain=domain,
            record_type=rec_type_upper,
            records=[],
            status_code="NXDOMAIN",
            message="Alan adı bulunamadı (NXDOMAIN).",
        )
    except dns.resolver.NoAnswer:
        return DnsQueryResult(
            domain=domain,
            record_type=rec_type_upper,
            records=[],
            status_code="NOANSWER",
            message=f"Bu alan adı için {rec_type_upper} kaydı mevcut değil (NoAnswer).",
        )
    except dns.resolver.NoNameservers:
        return DnsQueryResult(
            domain=domain,
            record_type=rec_type_upper,
            records=[],
            status_code="NONAMESERVERS",
            message="Kullanılabilir veya yanıt veren DNS sunucusu bulunamadı.",
        )
    except (dns.resolver.Timeout, dns.resolver.LifetimeTimeout):
        return DnsQueryResult(
            domain=domain,
            record_type=rec_type_upper,
            records=[],
            status_code="TIMEOUT",
            message=f"DNS sunucusundan yanıt alınamadı (Zaman aşımı - {resolver.timeout:.1f}s).",
        )
    except Exception as exc:
        return DnsQueryResult(
            domain=domain,
            record_type=rec_type_upper,
            records=[],
            status_code="ERROR",
            message=f"DNS sorgu hatası: {str(exc)}",
        )


class DnsQueryWorker(QObject):
    """QThread üzerinde DNS sorgularını yöneten asenkron iş parçacığı."""

    record_received = Signal(object)    # DnsRecordItem nesnesi
    query_completed = Signal(object)   # DnsQueryResult nesnesi
    status_changed = Signal(str)       # Durum mesajı
    finished = Signal()                # Tüm sorgular bitti
    error_occurred = Signal(str)       # Genel hata mesajı

    def __init__(
        self,
        domain: str,
        query_type: str,  # "A", "AAAA", ... veya "ALL" ("Tümü")
        custom_server: Optional[str] = None,
        timeout_sec: float = 2.0,
    ):
        super().__init__()
        self.domain = domain
        self.query_type = query_type
        self.custom_server = custom_server
        self.timeout_sec = timeout_sec
        self._is_stopped = False

    def stop(self):
        """Devam eden sorgu dizisini güvenle durdurur."""
        self._is_stopped = True

    def run(self):
        """DNS sorgu döngüsünü çalıştırır."""
        try:
            resolver = create_resolver(self.custom_server, self.timeout_sec)

            if self.query_type == "ALL" or self.query_type == "Tümü":
                target_types = list(SUPPORTED_RECORD_TYPES)
            else:
                target_types = [self.query_type]

            server_desc = self.custom_server if self.custom_server else "Sistem Varsayılanı"
            self.status_changed.emit(f"DNS sorgusu başlatıldı: {self.domain} ({server_desc})...")

            for rec_type in target_types:
                if self._is_stopped:
                    break

                self.status_changed.emit(f"Sorgulanıyor: {rec_type} kaydı...")
                result = query_single_type(self.domain, rec_type, resolver)

                if self._is_stopped:
                    break

                # Kayıtları tabloya anında akıt
                for record in result.records:
                    self.record_received.emit(record)

                self.query_completed.emit(result)

            if self._is_stopped:
                self.status_changed.emit("Sorgu kullanıcı tarafından durduruldu.")
            else:
                self.status_changed.emit("DNS sorguları tamamlandı.")

        except Exception as exc:
            self.error_occurred.emit(f"Beklenmeyen DNS hatası: {str(exc)}")
        finally:
            self.finished.emit()
