from dataclasses import dataclass

import pytest

import trading_workers.queue.sqs_client as sqs_client


@dataclass
class _FakeSettings:
    aws_region: str = "us-east-1"
    aws_endpoint_url: str | None = None


@pytest.fixture(autouse=True)
def _clear_client_cache():
    sqs_client.get_sqs_client.cache_clear()
    yield
    sqs_client.get_sqs_client.cache_clear()


def test_get_sqs_client_passes_endpoint_url_through_to_boto3(monkeypatch):
    calls = []
    settings = _FakeSettings(aws_endpoint_url="http://localstack:4566")
    monkeypatch.setattr(sqs_client, "get_settings", lambda: settings)
    monkeypatch.setattr(sqs_client.boto3, "client", lambda *a, **kw: calls.append((a, kw)))

    sqs_client.get_sqs_client()

    [(args, kwargs)] = calls
    assert args == ("sqs",)
    assert kwargs == {"region_name": "us-east-1", "endpoint_url": "http://localstack:4566"}


def test_get_sqs_client_passes_none_endpoint_url_when_unset(monkeypatch):
    calls = []
    monkeypatch.setattr(sqs_client, "get_settings", lambda: _FakeSettings())
    monkeypatch.setattr(sqs_client.boto3, "client", lambda *a, **kw: calls.append((a, kw)))

    sqs_client.get_sqs_client()

    [(args, kwargs)] = calls
    assert args == ("sqs",)
    assert kwargs == {"region_name": "us-east-1", "endpoint_url": None}
