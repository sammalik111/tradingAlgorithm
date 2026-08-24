#!/bin/sh
# Runs once, when LocalStack's SQS service is ready (mounted into
# /etc/localstack/init/ready.d/ -- see docker-compose.yml). Creates the
# queue TRADE_INGEST_QUEUE_URL points at for local dev.
awslocal sqs create-queue --queue-name trade-ingest
