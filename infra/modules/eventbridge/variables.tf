variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "nightly_scrape_function_arn" {
  type = string
}

variable "nightly_scrape_function_name" {
  type = string
}

variable "recommendation_engine_function_arn" {
  type = string
}

variable "recommendation_engine_function_name" {
  type = string
}

variable "scrape_schedule_expression" {
  description = "When the nightly scrape runs (UTC)."
  type        = string
  default     = "cron(0 6 * * ? *)" # 1-2am US Eastern, after market close data settles
}

variable "recommendation_schedule_expression" {
  description = "When the recommendation engine runs; must trail the scrape by enough time to finish ingesting."
  type        = string
  default     = "cron(0 8 * * ? *)"
}
