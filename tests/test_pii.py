from paymentcopilot.guardrails.pii import scan_and_redact

SAMPLE_CARD = "4111111111111111"
SAMPLE_EMAIL = "merchant-support@example.com"
SAMPLE_PHONE = "+1 415-555-0132"


def test_credit_card_detected_and_redacted():
    result = scan_and_redact(f"My card number is {SAMPLE_CARD}, please check it.")
    assert result.had_pii
    assert "CREDIT_CARD" in result.found_entities
    assert SAMPLE_CARD not in result.redacted_text


def test_email_detected_and_redacted():
    result = scan_and_redact(f"You can reach me at {SAMPLE_EMAIL} about this.")
    assert result.had_pii
    assert "EMAIL_ADDRESS" in result.found_entities
    assert SAMPLE_EMAIL not in result.redacted_text


def test_combined_pii_detected():
    text = f"Card {SAMPLE_CARD}, email {SAMPLE_EMAIL}, phone {SAMPLE_PHONE}."
    result = scan_and_redact(text)
    assert result.had_pii
    assert "CREDIT_CARD" in result.found_entities
    assert "EMAIL_ADDRESS" in result.found_entities


def test_clean_text_unchanged():
    text = "Why did my payment fail with error code GATEWAY_TIMEOUT?"
    result = scan_and_redact(text)
    assert not result.had_pii
    assert result.found_entities == []
    assert result.redacted_text == text


def test_empty_text_unchanged():
    result = scan_and_redact("")
    assert not result.had_pii
    assert result.redacted_text == ""
