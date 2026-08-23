output "queue_url" {
  value = aws_sqs_queue.trade_ingest.id
}

output "queue_arn" {
  value = aws_sqs_queue.trade_ingest.arn
}

output "dlq_arn" {
  value = aws_sqs_queue.trade_ingest_dlq.arn
}
