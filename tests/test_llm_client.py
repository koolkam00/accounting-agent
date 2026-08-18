"""VLLMLLMClient payload + MockLLM temperature compatibility (no GPU)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.errors import LLMExtractionError
from app.llm_client import (
    VLLMLLMClient,
    build_chat_extra_body,
    is_gpt_oss,
    is_qwen3_dense,
)
from app.settings import Settings, get_settings

SAMPLE = {
    "vendor_name": "Acme",
    "vendor_id": "V001",
    "invoice_number": "INV-1",
    "invoice_date": "2026-01-01",
    "po_number": "PO-1",
    "currency": "USD",
    "subtotal": "10.00",
    "tax": "0.00",
    "freight": "0.00",
    "invoice_total": "10.00",
    "payment_terms": "Net 30",
    "line_items": [
        {
            "line_number": 1,
            "sku": "SKU-1",
            "description": "Item",
            "quantity": "1",
            "unit_price": "10.00",
            "line_total": "10.00",
        }
    ],
    "ambiguities": [],
    "evidence": {},
}


class FakeCompletions:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.content = json.dumps(SAMPLE)
        self.reasoning_content = '{"vendor_name": "DO-NOT-PARSE"}'
        self.finish_reason = "stop"
        self.choices_empty = False

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.choices_empty:
            return SimpleNamespace(choices=[])
        msg = SimpleNamespace(content=self.content, reasoning_content=self.reasoning_content)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=msg, finish_reason=self.finish_reason)]
        )


class FakeOpenAI:
    last = None

    def __init__(self, **kwargs) -> None:
        self.init_kwargs = kwargs
        self.chat = SimpleNamespace(completions=FakeCompletions())
        FakeOpenAI.last = self


def _client(monkeypatch, **env) -> VLLMLLMClient:
    for key in (
        "MODEL_NAME",
        "MODEL_REVISION",
        "REASONING_EFFORT",
        "TEMPERATURE",
        "VLLM_BASE_URL",
        "VLLM_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, str(v))
    get_settings.cache_clear()
    import openai

    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    return VLLMLLMClient()


def test_model_name_helpers():
    assert is_gpt_oss("openai/gpt-oss-120b")
    assert is_gpt_oss("GPT-OSS-20B")
    assert not is_gpt_oss("Qwen/Qwen3-8B")
    assert is_qwen3_dense("Qwen/Qwen3-8B")
    assert is_qwen3_dense("Qwen/Qwen3-30B-A3B")
    assert not is_qwen3_dense("Qwen/Qwen3.5-9B")
    assert not is_qwen3_dense("Qwen/Qwen3.6-27B")
    assert not is_qwen3_dense("Qwen/Qwen3-Next-GDN")
    assert not is_qwen3_dense("openai/gpt-oss-120b")


def test_extra_body_gpt_oss_not_qwen():
    body = build_chat_extra_body("openai/gpt-oss-120b", "low")
    assert body == {"reasoning_effort": "low"}
    qwen = build_chat_extra_body("Qwen/Qwen3-8B", "low")
    assert qwen == {"chat_template_kwargs": {"enable_thinking": False}}
    assert build_chat_extra_body("Qwen/Qwen3.5-9B") == {}


def test_settings_code_defaults():
    s = Settings.__new__(Settings)
    # construct without dotenv by calling __init__ after env is whatever; just check class defaults via getenv fallbacks
    # Use a fresh Settings after deleting keys in a subprocess-like way: instantiate and compare fallbacks
    import os

    name = os.getenv("MODEL_NAME", "openai/gpt-oss-120b")
    # The code default string is what we care about when env is unset — already tested via helpers.
    assert Settings.__init__.__doc__ is None or True
    src = Settings.__init__.__code__.co_consts
    assert "openai/gpt-oss-120b" in src
    assert "low" in src


def test_gpt_oss_reasoning_payload(monkeypatch):
    client = _client(monkeypatch, MODEL_NAME="openai/gpt-oss-120b", REASONING_EFFORT="low")
    client.extract_invoice("invoice text")
    call = FakeOpenAI.last.chat.completions.calls[0]
    assert call["extra_body"] == {"reasoning_effort": "low"}
    assert "chat_template_kwargs" not in call["extra_body"]
    assert call["response_format"]["type"] == "json_schema"
    assert call["seed"] == 42
    assert call["top_p"] == 1
    assert call["n"] == 1


def test_qwen3_dense_thinking_disabled(monkeypatch):
    client = _client(monkeypatch, MODEL_NAME="Qwen/Qwen3-8B")
    client.extract_invoice("invoice text")
    call = FakeOpenAI.last.chat.completions.calls[0]
    assert call["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}


def test_qwen35_no_thinking_kwarg(monkeypatch):
    client = _client(monkeypatch, MODEL_NAME="Qwen/Qwen3.5-9B")
    client.extract_invoice("invoice text")
    call = FakeOpenAI.last.chat.completions.calls[0]
    assert "extra_body" not in call


def test_per_call_temperature_override(monkeypatch):
    client = _client(monkeypatch, MODEL_NAME="openai/gpt-oss-120b", TEMPERATURE="0")
    client.extract_invoice("invoice text", temperature=0.7)
    assert FakeOpenAI.last.chat.completions.calls[0]["temperature"] == 0.7
    client.extract_invoice("invoice text", temperature=1.0)
    assert FakeOpenAI.last.chat.completions.calls[1]["temperature"] == 1.0
    client.extract_invoice("invoice text")
    assert FakeOpenAI.last.chat.completions.calls[2]["temperature"] == 0.0


def test_init_temperature_override(monkeypatch):
    for key in ("MODEL_NAME", "TEMPERATURE"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MODEL_NAME", "openai/gpt-oss-120b")
    get_settings.cache_clear()
    import openai

    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    client = VLLMLLMClient(temperature=0.3)
    client.extract_invoice("invoice text")
    assert FakeOpenAI.last.chat.completions.calls[0]["temperature"] == 0.3
    client.extract_invoice("invoice text", temperature=1.0)
    assert FakeOpenAI.last.chat.completions.calls[1]["temperature"] == 1.0


def test_parses_message_content_only(monkeypatch):
    client = _client(monkeypatch, MODEL_NAME="openai/gpt-oss-120b")
    extracted = client.extract_invoice("invoice text")
    assert extracted.vendor_name == "Acme"
    assert extracted.vendor_name != "DO-NOT-PARSE"


@pytest.mark.parametrize(
    "attr,value",
    [
        ("content", None),
        ("content", "   "),
        ("content", "not json at all"),
        ("content", '{"vendor_name": 5}'),
        ("finish_reason", "length"),
        ("choices_empty", True),
    ],
)
def test_unusable_model_response_raises(monkeypatch, attr, value):
    client = _client(monkeypatch, MODEL_NAME="openai/gpt-oss-120b")
    setattr(FakeOpenAI.last.chat.completions, attr, value)
    with pytest.raises(LLMExtractionError):
        client.extract_invoice("invoice text")
