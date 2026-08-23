import asyncio
import logging
from typing import Any

from trading_workers.db.session import session_scope
from trading_workers.ingest.canonicalizer import ingest_record
from trading_workers.ingest.source_resolver import get_or_create_source
from trading_workers.queue.messages import TradeIngestMessage

logger = logging.getLogger(__name__)


async def _process_one(message_id: str, body: str) -> str | None:
    """Ingest a single SQS message. Returns the message id on failure (for
    SQS partial batch response), or None on success.
    """
    try:
        message = TradeIngestMessage.model_validate_json(body)
        async with session_scope() as db:
            source = await get_or_create_source(db, message.source_code)
            await ingest_record(db, source, message.to_record())
            await db.commit()
        return None
    except Exception:
        logger.exception("failed to process SQS message %s", message_id)
        return message_id


async def _process_batch(records: list[dict]) -> dict[str, Any]:
    failures = []
    for sqs_record in records:
        failed_id = await _process_one(sqs_record["messageId"], sqs_record["body"])
        if failed_id is not None:
            failures.append({"itemIdentifier": failed_id})
    return {"batchItemFailures": failures}


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """SQS trigger entrypoint (see infra/modules/lambda). Uses the SQS
    partial batch failure report so only the messages that actually failed
    get redelivered, not the whole batch.
    """
    return asyncio.run(_process_batch(event.get("Records", [])))
