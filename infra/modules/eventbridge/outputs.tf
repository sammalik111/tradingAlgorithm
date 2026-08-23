output "nightly_scrape_schedule_arn" {
  value = aws_scheduler_schedule.nightly_scrape.arn
}

output "recommendation_engine_schedule_arn" {
  value = aws_scheduler_schedule.recommendation_engine.arn
}
