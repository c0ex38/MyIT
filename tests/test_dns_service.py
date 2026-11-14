"""DNS servisi ve ayrıştırıcı birim testleri."""

import unittest
from unittest.mock import MagicMock, patch

import dns.resolver

from myit.modules.network.dns_service import (
    DnsQueryWorker,
    DnsRecordItem,
    create_resolver,
    format_rdata_item,
    query_single_type,
    validate_dns_server,
    validate_domain,
)


class TestDnsService(unittest.TestCase):
    """DNS girdi doğrulama, rdata ayrıştırma ve worker testleri."""

    def test_valid_domain(self):
        """1. Geçerli alan adı kabul edilir."""
        valid, msg, domain = validate_domain("example.com")
        self.assertTrue(valid)
        self.assertEqual(domain, "example.com")

        valid, msg, domain = validate_domain("Sub.Example.com.")
        self.assertTrue(valid)
        self.assertEqual(domain, "sub.example.com")

    def test_invalid_url_and_special_chars(self):
        """2. URL, kontrol karakteri ve boşluk içeren girdi reddedilir."""
        valid, msg, _ = validate_domain("http://example.com")
        self.assertFalse(valid)
        self.assertIn("URL", msg)

        valid, msg, _ = validate_domain("example.com/path")
        self.assertFalse(valid)

        valid, msg, _ = validate_domain("example.com:8080")
        self.assertFalse(valid)

        valid, msg, _ = validate_domain("example com")
        self.assertFalse(valid)

    def test_empty_or_too_long_domain(self):
        """3. Boş veya fazla uzun alan adı reddedilir."""
        valid, msg, _ = validate_domain("")
        self.assertFalse(valid)
        self.assertIn("boş", msg)

        long_label = "a" * 64 + ".com"
        valid, msg, _ = validate_domain(long_label)
        self.assertFalse(valid)
        self.assertIn("63", msg)

    def test_idn_domain_normalized(self):
        """4. IDN alan adı normalize edilir (örn. türkçe karakterler)."""
        valid, msg, domain = validate_domain("türkiye.gov.tr")
        self.assertTrue(valid)
        self.assertTrue(domain.startswith("xn--"))

    def test_valid_ipv4_dns_server(self):
        """5. Geçerli IPv4 DNS sunucusu kabul edilir."""
        valid, msg, ip = validate_dns_server("8.8.8.8")
        self.assertTrue(valid)
        self.assertEqual(ip, "8.8.8.8")

        valid, msg, ip = validate_dns_server("1.1.1.1")
        self.assertTrue(valid)

    def test_valid_ipv6_dns_server(self):
        """6. Geçerli IPv6 DNS sunucusu kabul edilir."""
        valid, msg, ip = validate_dns_server("2001:4860:4860::8888")
        self.assertTrue(valid)
        self.assertEqual(ip, "2001:4860:4860::8888")

    def test_invalid_dns_server(self):
        """7. Geçersiz DNS sunucusu reddedilir."""
        valid, msg, _ = validate_dns_server("google.com")  # Yalnızca IP kabul edilir
        self.assertFalse(valid)

        valid, msg, _ = validate_dns_server("999.999.999.999")
        self.assertFalse(valid)

        valid, msg, _ = validate_dns_server("")
        self.assertFalse(valid)

    def test_format_a_record(self):
        """8. A kaydı ayrışımı ve TTL testi."""
        item = format_rdata_item("A", "93.184.216.34", 300)
        self.assertEqual(item.record_type, "A")
        self.assertEqual(item.value, "93.184.216.34")
        self.assertEqual(item.ttl, 300)

    def test_format_mx_record(self):
        """9. MX öncelik ve sunucu ayrışımı testi."""
        mock_mx = MagicMock()
        mock_mx.preference = 10
        mock_mx.exchange = "mail.example.com."
        item = format_rdata_item("MX", mock_mx, 3600)

        self.assertEqual(item.record_type, "MX")
        self.assertEqual(item.value, "mail.example.com")
        self.assertIn("10", item.extra_info)

    def test_format_txt_record(self):
        """10. TXT string parçacıklarını kayıpsız birleştirme testi."""
        mock_txt = MagicMock()
        mock_txt.strings = [b"v=spf1 ", b"include:_spf.google.com ~all"]
        item = format_rdata_item("TXT", mock_txt, 600)

        self.assertEqual(item.record_type, "TXT")
        self.assertEqual(item.value, "v=spf1 include:_spf.google.com ~all")

    def test_nxdomain_and_noanswer(self):
        """11. NXDOMAIN / NoAnswer hata sınıflandırması testi."""
        mock_resolver = MagicMock()
        mock_resolver.resolve.side_effect = dns.resolver.NXDOMAIN()

        res = query_single_type("bilinmeyen-alan-adi.xyz", "A", mock_resolver)
        self.assertEqual(res.status_code, "NXDOMAIN")
        self.assertIn("NXDOMAIN", res.message)

        mock_resolver.resolve.side_effect = dns.resolver.NoAnswer()
        res = query_single_type("example.com", "AAAA", mock_resolver)
        self.assertEqual(res.status_code, "NOANSWER")
        self.assertIn("NoAnswer", res.message)

    def test_timeout_and_nonameservers(self):
        """12. Timeout / NoNameservers hata sınıflandırması testi."""
        mock_resolver = MagicMock()
        mock_resolver.timeout = 2.0
        mock_resolver.resolve.side_effect = dns.resolver.Timeout()

        res = query_single_type("example.com", "A", mock_resolver)
        self.assertEqual(res.status_code, "TIMEOUT")
        self.assertIn("Zaman aşımı", res.message)

        mock_resolver.resolve.side_effect = dns.resolver.NoNameservers()
        res = query_single_type("example.com", "A", mock_resolver)
        self.assertEqual(res.status_code, "NONAMESERVERS")

    def test_worker_stop_flag(self):
        """14. İptal bayrağının sorgu döngüsünü durdurması testi."""
        worker = DnsQueryWorker("example.com", "ALL")
        worker.stop()
        self.assertTrue(worker._is_stopped)

    def test_mock_full_query_without_network(self):
        """15. Dış ağa bağlanmadan mock resolver ile tam sorgu testi."""
        mock_resolver = MagicMock()
        mock_answer = MagicMock()
        mock_answer.rrset.ttl = 300
        mock_answer.__iter__.return_value = ["93.184.216.34"]
        mock_resolver.resolve.return_value = mock_answer

        res = query_single_type("example.com", "A", mock_resolver)
        self.assertEqual(res.status_code, "NOERROR")
        self.assertEqual(len(res.records), 1)
        self.assertEqual(res.records[0].value, "93.184.216.34")


if __name__ == "__main__":
    unittest.main()
