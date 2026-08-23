from functools import lru_cache

import boto3

from trading_workers.config import get_settings
from trading_workers.queue.messages import TradeIngestMessage


class TradeQueueNotConfiguredError(RuntimeError):
    """Raised when TRADE_INGEST_QUEUE_URL is unset."""


@lru_cache
def get_sqs_client():
    return boto3.client("sqs", region_name=get_settings().aws_region)


def enqueue_trade(message: TradeIngestMessage) -> None:
    """Publish one scraped trade to the ingest queue. Consumed by the SQS
    Lambda trigger in `jobs/process_trade_message.py`.
    """
    settings = get_settings()
    if not settings.trade_ingest_queue_url:
        raise TradeQueueNotConfiguredError("TRADE_INGEST_QUEUE_URL is not set")

    get_sqs_client().send_message(
        QueueUrl=settings.trade_ingest_queue_url,
        MessageBody=message.model_dump_json(),
    )
