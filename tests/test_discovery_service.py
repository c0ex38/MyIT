"""Ağ Keşfi (Network Discovery) servisi için birim testleri."""

import ipaddress
import unittest
from unittest.mock import MagicMock, patch

from myit.modules.network.discovery_service import (
    DiscoveredDevice,
    DiscoveryWorker,
    NetworkAdapterInfo,
    validate_cidr,
)


class TestDiscoveryService(unittest.TestCase):
    """CIDR doğrulama ve ağ keşif servisi testleri."""

    def test_valid_cidr(self):
        """Özel /24 CIDR aralığının kabul edildiğini doğrular."""
        valid, msg, net = validate_cidr("192.168.1.0/24")
        self.assertTrue(valid)
        self.assertIsNotNone(net)
        self.assertEqual(net.prefixlen, 24)

        valid, msg, net = validate_cidr("10.0.0.0/24")
        self.assertTrue(valid)

    def test_empty_or_invalid_cidr(self):
        """Boş ve anlamsız CIDR formatlarının reddedildiğini doğrular."""
        valid, msg, _ = validate_cidr("")
        self.assertFalse(valid)
        self.assertIn("boş", msg)

        valid, msg, _ = validate_cidr("gecersiz_cidr")
        self.assertFalse(valid)

    def test_loopback_and_multicast_rejected(self):
        """Geri döngü ve multicast aralıklarının reddedildiğini doğrular."""
        valid, msg, _ = validate_cidr("127.0.0.0/24")
        self.assertFalse(valid)
        self.assertIn("Geri döngü", msg)

        valid, msg, _ = validate_cidr("224.0.0.0/24")
        self.assertFalse(valid)
        self.assertIn("Multicast", msg)

    def test_public_ip_rejected(self):
        """Genel internet IP aralıklarının reddedildiğini doğrular."""
        valid, msg, _ = validate_cidr("8.8.8.0/24")
        self.assertFalse(valid)
        self.assertIn("İnternet geneli", msg)

    def test_wide_cidr_limit_enforced(self):
        """/24'ten daha geniş aralıkların (/16, /8) reddedildiğini doğrular."""
        valid, msg, _ = validate_cidr("192.168.0.0/16")
        self.assertFalse(valid)
        self.assertIn("en fazla /24", msg)

        valid, msg, _ = validate_cidr("10.0.0.0/8")
        self.assertFalse(valid)

    def test_network_and_broadcast_excluded(self):
        """Host listesinin ağ ve broadcast adreslerini dışladığını doğrular."""
        net = ipaddress.IPv4Network("192.168.1.0/29")  # 8 IP: .0 network, .7 broadcast, 6 host
        hosts = [str(ip) for ip in net.hosts()]
        self.assertEqual(len(hosts), 6)
        self.assertNotIn("192.168.1.0", hosts)
        self.assertNotIn("192.168.1.7", hosts)

    @patch("myit.modules.network.discovery_service.probe_single_ip")
    @patch("myit.modules.network.discovery_service.resolve_hostname")
    def test_scan_host_reachable(self, mock_hostname, mock_probe):
        """Erişilebilir bir cihazın doğru modelle döndüğünü test eder."""
        mock_probe.return_value = (True, 5.2)
        mock_hostname.return_value = "my-router.local"

        worker = DiscoveryWorker(ipaddress.IPv4Network("192.168.1.0/29"), gateway_ip="192.168.1.1")
        device = worker._scan_host("192.168.1.1", arp_map={"192.168.1.1": "AA:BB:CC:DD:EE:FF"})

        self.assertEqual(device.ip, "192.168.1.1")
        self.assertEqual(device.status, "Erişilebilir")
        self.assertEqual(device.latency, 5.2)
        self.assertEqual(device.mac_address, "AA:BB:CC:DD:EE:FF")
        self.assertEqual(device.hostname, "my-router.local")
        self.assertTrue(device.is_gateway)

    @patch("myit.modules.network.discovery_service.probe_single_ip")
    def test_scan_host_unreachable(self, mock_probe):
        """Yanıtsız cihazlarda hostname uydurulmadığını ('-') test eder."""
        mock_probe.return_value = (False, None)

        worker = DiscoveryWorker(ipaddress.IPv4Network("192.168.1.0/29"))
        device = worker._scan_host("192.168.1.50", arp_map={})

        self.assertEqual(device.ip, "192.168.1.50")
        self.assertEqual(device.status, "Yanıtsız")
        self.assertIsNone(device.latency)
        self.assertEqual(device.hostname, "-")
        self.assertEqual(device.mac_address, "-")


if __name__ == "__main__":
    unittest.main()
