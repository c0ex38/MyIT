"""Traceroute servisi ve çıktı ayrıştırma testleri."""

import unittest
from unittest.mock import MagicMock, patch

from myit.modules.network.traceroute_service import (
    HopResult,
    TracerouteWorker,
    build_tracert_args,
    parse_hop_line,
    validate_traceroute_params,
    validate_traceroute_target,
)


class TestTracerouteService(unittest.TestCase):
    """Traceroute girdi doğrulama, argüman oluşturma ve çıktı ayrıştırma testleri."""

    def test_01_valid_ipv4_target(self):
        """01. Geçerli IPv4 hedef kabul edilir."""
        valid, msg, target = validate_traceroute_target("127.0.0.1")
        self.assertTrue(valid)
        self.assertEqual(target, "127.0.0.1")

        valid, msg, target = validate_traceroute_target("192.168.1.1")
        self.assertTrue(valid)

    def test_02_valid_ipv6_target(self):
        """02. Geçerli IPv6 hedef kabul edilir."""
        valid, msg, target = validate_traceroute_target("::1")
        self.assertTrue(valid)
        self.assertEqual(target, "::1")

        valid, msg, target = validate_traceroute_target("2001:4860:4860::8888")
        self.assertTrue(valid)

    def test_03_valid_hostname(self):
        """03. Geçerli hostname kabul edilir."""
        valid, msg, target = validate_traceroute_target("example.com")
        self.assertTrue(valid)
        self.assertEqual(target, "example.com")

        valid, msg, target = validate_traceroute_target("sub.domain.local")
        self.assertTrue(valid)

    def test_04_invalid_injection_and_url(self):
        """04. CLI enjeksiyonu ve URL gibi geçersiz hedeflerin reddi."""
        valid, msg, _ = validate_traceroute_target("http://example.com")
        self.assertFalse(valid)
        self.assertIn("URL", msg)

        valid, msg, _ = validate_traceroute_target("-h 5 example.com")
        self.assertFalse(valid)

        valid, msg, _ = validate_traceroute_target("example.com; dir")
        self.assertFalse(valid)

        valid, msg, _ = validate_traceroute_target("example.com:8080")
        self.assertFalse(valid)

    def test_05_max_hops_validation(self):
        """05. Hop sayısı alt/üst sınır doğrulaması (1-30)."""
        valid, msg = validate_traceroute_params(max_hops=20, timeout_ms=1000)
        self.assertTrue(valid)

        # 0 ve 31 sınır dışı
        valid, msg = validate_traceroute_params(max_hops=0, timeout_ms=1000)
        self.assertFalse(valid)

        valid, msg = validate_traceroute_params(max_hops=31, timeout_ms=1000)
        self.assertFalse(valid)

    def test_06_timeout_validation(self):
        """06. Timeout alt/üst sınır doğrulaması (250-5000 ms)."""
        valid, msg = validate_traceroute_params(max_hops=20, timeout_ms=100)  # Çok küçük
        self.assertFalse(valid)

        valid, msg = validate_traceroute_params(max_hops=20, timeout_ms=6000)  # Çok büyük
        self.assertFalse(valid)

    def test_07_build_args_ipv4(self):
        """07. IPv4 seçeneği için -4 argüman listesi."""
        args = build_tracert_args("8.8.8.8", max_hops=15, timeout_ms=800, ip_version="IPV4")
        self.assertEqual(args[0], "tracert.exe")
        self.assertIn("-d", args)
        self.assertIn("-4", args)
        self.assertNotIn("-6", args)
        self.assertIn("8.8.8.8", args)

    def test_08_build_args_ipv6(self):
        """08. IPv6 seçeneği için -6 argüman listesi."""
        args = build_tracert_args("::1", max_hops=10, timeout_ms=500, ip_version="IPV6")
        self.assertIn("-6", args)
        self.assertNotIn("-4", args)
        self.assertIn("::1", args)

    def test_09_parse_normal_hop_line(self):
        """09. Normal hop satırı ve 3 RTT ayrışma."""
        line = "  1    12 ms    14 ms    11 ms  192.168.1.1"
        res = parse_hop_line(line)
        self.assertIsNotNone(res)
        self.assertEqual(res.hop_num, 1)
        self.assertEqual(res.rtt1, "12 ms")
        self.assertEqual(res.rtt2, "14 ms")
        self.assertEqual(res.rtt3, "11 ms")
        self.assertEqual(res.ip_or_host, "192.168.1.1")
        self.assertEqual(res.status, "Yanıt Alındı")

    def test_10_parse_timeout_and_subsequent_hop(self):
        """10. * timeout hop ve sonrasında normal hop ayrışma."""
        timeout_line = "  2     *        *        *     Request timed out."
        res1 = parse_hop_line(timeout_line)
        self.assertIsNotNone(res1)
        self.assertEqual(res1.hop_num, 2)
        self.assertEqual(res1.status, "Zaman Aşımı (*)")

        # Ardından gelen normal hop
        next_line = "  3    15 ms    16 ms    14 ms  10.0.0.1"
        res2 = parse_hop_line(next_line)
        self.assertIsNotNone(res2)
        self.assertEqual(res2.hop_num, 3)
        self.assertEqual(res2.ip_or_host, "10.0.0.1")

    def test_11_parse_sub_millisecond_rtt(self):
        """11. <1 ms ve kısmi yanıt güvenli ayrışma."""
        line = "  1    <1 ms    <1 ms    <1 ms  127.0.0.1"
        res = parse_hop_line(line, target_host="127.0.0.1")
        self.assertIsNotNone(res)
        self.assertEqual(res.rtt1, "<1 ms")
        self.assertEqual(res.status, "Hedefe Ulaşıldı")

        partial_line = "  2     *       24 ms     *     192.168.10.1"
        res_partial = parse_hop_line(partial_line)
        self.assertIsNotNone(res_partial)
        self.assertEqual(res_partial.status, "Kısmi Yanıt")

    def test_12_worker_stop_and_cleanup(self):
        """12. İptalde alt süreç temizliği / yeni işlem başlamaması."""
        worker = TracerouteWorker("127.0.0.1")
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # Çalışıyor
        worker._process = mock_proc

        worker.stop()
        self.assertTrue(worker._is_stopped)
        mock_proc.terminate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
