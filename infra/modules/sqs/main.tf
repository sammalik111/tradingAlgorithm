resource "aws_sqs_queue" "trade_ingest_dlq" {
  name                      = "${var.project}-${var.environment}-trade-ingest-dlq"
  message_retention_seconds = 1209600 # 14 days, so a failing batch can be inspected/replayed

  tags = { Name = "${var.project}-${var.environment}-trade-ingest-dlq" }
}

resource "aws_sqs_queue" "trade_ingest" {
  name                       = "${var.project}-${var.environment}-trade-ingest"
  visibility_timeout_seconds = var.visibility_timeout_seconds
  message_retention_seconds  = 345600 # 4 days

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.trade_ingest_dlq.arn
    maxReceiveCount      = var.max_receive_count
  })

  tags = { Name = "${var.project}-${var.environment}-trade-ingest" }
}
