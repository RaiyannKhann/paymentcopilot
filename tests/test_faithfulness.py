from unittest.mock import patch

from paymentcopilot.guardrails.faithfulness import check_faithfulness


def test_passes_when_judge_returns_pass():
    with patch(
        "paymentcopilot.guardrails.faithfulness.call_claude",
        return_value="PASS — every claim is supported by the grounding text",
    ):
        result = check_faithfulness("Webhooks are verified via HMAC-SHA256.", "grounding text")
    assert result.passed
    assert "supported" in result.reason


def test_fails_when_judge_returns_fail():
    with patch(
        "paymentcopilot.guardrails.faithfulness.call_claude",
        return_value="FAIL — the answer claims a 30-day window not present in the context",
    ):
        result = check_faithfulness("Refunds are allowed within 30 days.", "grounding text")
    assert not result.passed
    assert "30-day" in result.reason


def test_fails_when_no_grounding_text_without_calling_llm():
    with patch("paymentcopilot.guardrails.faithfulness.call_claude") as mock_call:
        result = check_faithfulness("Some answer.", "")
    assert not result.passed
    mock_call.assert_not_called()
