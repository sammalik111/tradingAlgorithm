variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "github_owner" {
  type = string
}

variable "github_repo" {
  type = string
}

variable "branch_name" {
  type    = string
  default = "main"
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "aurora_security_group_id" {
  type = string
}

variable "backend_ecr_url" {
  type = string
}

variable "workers_ecr_url" {
  type = string
}

variable "backend_ecr_arn" {
  type = string
}

variable "workers_ecr_arn" {
  type = string
}

variable "db_master_secret_arn" {
  type = string
}

variable "db_host" {
  type = string
}

variable "db_name" {
  type = string
}

variable "frontend_bucket_name" {
  type = string
}

variable "frontend_bucket_arn" {
  type = string
}

variable "cloudfront_distribution_id" {
  type = string
}

variable "cloudfront_distribution_arn" {
  type = string
}

variable "api_endpoint" {
  type = string
}

variable "backend_api_function_name" {
  type = string
}

variable "recommendation_engine_function_name" {
  type = string
}

variable "nightly_scrape_function_name" {
  type = string
}

variable "process_trade_message_function_name" {
  type = string
}

variable "lambda_function_arns" {
  description = "Every Lambda function ARN CodeBuild is allowed to update code for."
  type        = list(string)
}

variable "deploy_schedule_expression" {
  description = "Weekly by default; the account otherwise only deploys on a manual pipeline release."
  type        = string
  default     = "cron(0 13 ? * MON *)"
}
