"""Port Tarayıcı servisi için birim testleri."""

import socket
import unittest
from unittest.mock import MagicMock, patch

from myit.modules.network.port_scan_service import (
    COMMON_PORTS,
    MAX_PORTS_PER_SCAN,
    PortScanResult,
    PortScanWorker,
    get_known_service_name,
    parse_port_expression,
    scan_single_tcp_port,
)


class TestPortScanService(unittest.TestCase):
    """Port ayrıştırıcı ve soket tarama testleri."""

    def test_parse_comma_separated_ports(self):
        """Virgülle ayrılmış portların doğru ayrıştırıldığını test eder."""
        valid, msg, ports = parse_port_expression("80, 443, 3389")
        self.assertTrue(valid)
        self.assertEqual(ports, [80, 443, 3389])

    def test_parse_ranges_and_duplicates(self):
        """Aralık ve tekrarlayan portların doğru sıralanıp tekilleştirildiğini test eder."""
        valid, msg, ports = parse_port_expression("20-22, 80, 21")
        self.assertTrue(valid)
        self.assertEqual(ports, [20, 21, 22, 80])

    def test_invalid_ports_and_ranges(self):
        """Geçersiz port numaralarının ve ters aralıkların reddedildiğini test eder."""
        # 0 portu geçersiz
        valid, msg, _ = parse_port_expression("0, 80")
        self.assertFalse(valid)

        # 65536 portu sınır dışı
        valid, msg, _ = parse_port_expression("65536")
        self.assertFalse(valid)

        # Ters aralık (80-20)
        valid, msg, _ = parse_port_expression("80-20")
        self.assertFalse(valid)
        self.assertIn("büyük olamaz", msg)

        # Boş girdi
        valid, msg, _ = parse_port_expression("")
        self.assertFalse(valid)

        # Bozuk karakterler
        valid, msg, _ = parse_port_expression("80; whoami")
        self.assertFalse(valid)

    def test_max_ports_limit(self):
        """256 port sınırının uygulandığını test eder."""
        # 1-300 aralığı 300 port eder
        valid, msg, _ = parse_port_expression("1-300")
        self.assertFalse(valid)
        self.assertIn("en fazla 256", msg)

    def test_known_service_name(self):
        """Bilinen servis adlarının ve bilinmeyen port durumunun kontrolü."""
        self.assertIn("HTTPS", get_known_service_name(443))
        self.assertIn("RDP", get_known_service_name(3389))
        self.assertEqual(get_known_service_name(64999), "Bilinmiyor")

    @patch("socket.socket")
    def test_scan_single_port_open(self, mock_socket_class):
        """Açık port durumunu test eder."""
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        mock_sock.connect.return_value = None  # Başarılı bağlantı

        result = scan_single_tcp_port("127.0.0.1", 80, timeout_sec=0.5)
        self.assertEqual(result.port, 80)
        self.assertEqual(result.status, "Açık")
        self.assertIsNotNone(result.latency)

    @patch("socket.socket")
    def test_scan_single_port_closed(self, mock_socket_class):
        """Kapalı (ConnectionRefused) port durumunu test eder."""
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        mock_sock.connect.side_effect = ConnectionRefusedError("Connection refused")

        result = scan_single_tcp_port("127.0.0.1", 81, timeout_sec=0.5)
        self.assertEqual(result.port, 81)
        self.assertEqual(result.status, "Kapalı")

    @patch("socket.socket")
    def test_scan_single_port_timeout(self, mock_socket_class):
        """Zaman aşımı / filtreli port durumunu test eder."""
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        mock_sock.connect.side_effect = socket.timeout("Timed out")

        result = scan_single_tcp_port("192.168.1.99", 445, timeout_sec=0.2)
        self.assertEqual(result.port, 445)
        self.assertEqual(result.status, "Zaman Aşımı / Filtreli")

    def test_worker_stop_flag(self):
        """Worker stop() çağrıldığında yeni görevlerin iptal edildiğini test eder."""
        worker = PortScanWorker("127.0.0.1", [80, 443])
        worker.stop()
        res = worker._scan_task("127.0.0.1", 80)
        self.assertEqual(res.status, "Durduruldu")


if __name__ == "__main__":
    unittest.main()
