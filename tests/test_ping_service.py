"""Ping servisi için birim testleri."""

import unittest
from myit.modules.network.ping_service import validate_target, PingStatistics


class TestPingService(unittest.TestCase):
    """Ping hedef doğrulama ve veri modeli testleri."""

    def test_valid_ipv4(self):
        valid, val = validate_target("127.0.0.1")
        self.assertTrue(valid)
        self.assertEqual(val, "127.0.0.1")

        valid, val = validate_target("  192.168.1.1  ")
        self.assertTrue(valid)
        self.assertEqual(val, "192.168.1.1")

    def test_valid_hostname(self):
        valid, val = validate_target("google.com")
        self.assertTrue(valid)
        self.assertEqual(val, "google.com")

        valid, val = validate_target("one.one.one.one")
        self.assertTrue(valid)

    def test_empty_target(self):
        valid, msg = validate_target("")
        self.assertFalse(valid)
        self.assertIn("boş", msg)

        valid, msg = validate_target("   ")
        self.assertFalse(valid)

    def test_command_injection(self):
        # Parametre enjeksiyonu
        valid, msg = validate_target("-n 1 127.0.0.1")
        self.assertFalse(valid)

        # Komut birleştirme
        valid, msg = validate_target("127.0.0.1 & dir")
        self.assertFalse(valid)

        valid, msg = validate_target("127.0.0.1; whoami")
        self.assertFalse(valid)

        valid, msg = validate_target("127.0.0.1 | notepad")
        self.assertFalse(valid)

    def test_invalid_chars(self):
        valid, msg = validate_target("invalid host with spaces")
        self.assertFalse(valid)


if __name__ == "__main__":
    unittest.main()
