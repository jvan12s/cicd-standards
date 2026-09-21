import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import dsgvo_guard  # noqa: E402


class TestEmailDetection(unittest.TestCase):
    def test_detects_real_looking_email(self):
        findings = dsgvo_guard.scan_text("kontakt = 'jan.mueller@kundenfirma.de'", [])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "email")

    def test_ignores_example_domain(self):
        findings = dsgvo_guard.scan_text("email = 'user@example.com'", [])
        self.assertEqual(findings, [])

    def test_ignores_dot_test_suffix(self):
        findings = dsgvo_guard.scan_text("email = 'user@acme.test'", [])
        self.assertEqual(findings, [])

    def test_allowlisted_email_ignored(self):
        allowlist = ["jan.mueller@kundenfirma.de"]
        findings = dsgvo_guard.scan_text("kontakt = 'jan.mueller@kundenfirma.de'", allowlist)
        self.assertEqual(findings, [])

    def test_inline_suppression_comment(self):
        findings = dsgvo_guard.scan_text(
            "email = 'jan.mueller@kundenfirma.de'  # dsgvo-guard: allow", []
        )
        self.assertEqual(findings, [])


class TestIbanDetection(unittest.TestCase):
    def test_detects_valid_iban(self):
        # gültige Testbeispiel-IBAN mit korrekter Prüfsumme (öffentlich bekanntes Beispiel)
        findings = dsgvo_guard.scan_text("iban = 'DE89370400440532013000'", [])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "iban")

    def test_ignores_invalid_checksum(self):
        findings = dsgvo_guard.scan_text("iban = 'DE00370400440532013000'", [])
        self.assertEqual(findings, [])

    def test_ignores_random_alnum_lookalike(self):
        findings = dsgvo_guard.scan_text("id = 'AB1234567890123456789'", [])
        self.assertEqual(findings, [])


class TestPhoneDetection(unittest.TestCase):
    def test_detects_german_phone_with_country_code(self):
        findings = dsgvo_guard.scan_text("tel = '+49 170 1234567'", [])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "phone")

    def test_ignores_plain_digit_sequence(self):
        findings = dsgvo_guard.scan_text("version = '4917012345678'", [])
        self.assertEqual(findings, [])


class TestIbanChecksum(unittest.TestCase):
    def test_valid_known_iban(self):
        self.assertTrue(dsgvo_guard.iban_checksum_valid("DE89370400440532013000"))

    def test_invalid_checksum(self):
        self.assertFalse(dsgvo_guard.iban_checksum_valid("DE00370400440532013000"))

    def test_too_short_is_invalid(self):
        self.assertFalse(dsgvo_guard.iban_checksum_valid("DE1234"))


class TestRedact(unittest.TestCase):
    def test_redacts_middle(self):
        self.assertEqual(dsgvo_guard.redact("jan@kundenfirma.de"), "ja**************de")

    def test_short_value_fully_masked(self):
        self.assertEqual(dsgvo_guard.redact("ab"), "**")


class TestExitCode(unittest.TestCase):
    def test_main_returns_zero_when_clean(self, tmp_path=None):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "clean.py").write_text("user = 'user@example.com'\n")
            code = dsgvo_guard.main(["--root", str(root)])
            self.assertEqual(code, 0)

    def test_main_returns_one_when_finding(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "fixture.py").write_text("user = 'jan.mueller@kundenfirma.de'\n")
            code = dsgvo_guard.main(["--root", str(root)])
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
