"""Tests for loading the do-not-contact list from a file."""
import config


def test_load_dnc_reads_contacts(tmp_path):
    f = tmp_path / "dnc.csv"
    f.write_text(
        "# comment line\ncontact\nuser@example.com\n\n+919812345678\n",
        encoding="utf-8",
    )
    contacts = config.load_dnc(f)
    assert contacts == {"user@example.com", "+919812345678"}


def test_load_dnc_falls_back_when_file_missing(tmp_path):
    contacts = config.load_dnc(tmp_path / "does_not_exist.csv")
    assert contacts  # non-empty default set so the DNC rule still works


def test_project_dnc_file_is_loaded():
    # The shipped list should contain at least the known opt-out address.
    assert "dnc_customer@example.com" in config.DO_NOT_CONTACT


def test_force_offline_disables_providers(monkeypatch):
    # Even with keys set, FORCE_OFFLINE makes the providers report unavailable.
    monkeypatch.setattr(config, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(config, "RAZORPAY_KEY_ID", "id")
    monkeypatch.setattr(config, "RAZORPAY_KEY_SECRET", "secret")
    monkeypatch.setattr(config, "FORCE_OFFLINE", True)
    assert config.has_groq() is False
    assert config.has_razorpay() is False
