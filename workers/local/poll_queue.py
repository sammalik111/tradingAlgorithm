"""Poll the local (LocalStack) SQS queue and drive process_trade_message's
handler exactly as the real SQS-triggered Lambda would -- there's no event
source mapping locally, so something has to pull messages and call the
handler. Local dev only -- see documentation/workers.md.

Usage: docker compose exec workers python local/poll_queue.py
"""

import time

from trading_workers.config import get_settings
from trading_workers.jobs.process_trade_message import handler
from trading_workers.queue.sqs_client import get_sqs_client

POLL_INTERVAL_SECONDS = 2
MAX_MESSAGES_PER_POLL = 10


def _to_sqs_event(messages: list[dict]) -> dict:
    return {"Records": [{"messageId": m["MessageId"], "body": m["Body"]} for m in messages]}


def run_once(queue_url: str) -> int:
    client = get_sqs_client()
    response = client.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=MAX_MESSAGES_PER_POLL, WaitTimeSeconds=1
    )
    messages = response.get("Messages", [])
    if not messages:
        return 0

    result = handler(_to_sqs_event(messages), None)
    failed_ids = {failure["itemIdentifier"] for failure in result.get("batchItemFailures", [])}

    processed = 0
    for message in messages:
        if message["MessageId"] not in failed_ids:
            client.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])
            processed += 1
    return processed


def main() -> None:
    queue_url = get_settings().trade_ingest_queue_url
    if not queue_url:
        raise SystemExit("TRADE_INGEST_QUEUE_URL is not set")

    print(f"Polling {queue_url} every {POLL_INTERVAL_SECONDS}s. Ctrl+C to stop.")
    while True:
        processed = run_once(queue_url)
        if processed:
            print(f"processed {processed} message(s)")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
