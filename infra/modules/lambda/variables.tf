variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "function_name" {
  description = "Suffix appended to \"<project>-<environment>-\""
  type        = string
}

variable "image_uri" {
  type = string
}

variable "image_command" {
  description = "Overrides the image's CMD, e.g. [\"trading_backend.main.handler\"]"
  type        = list(string)
}

variable "memory_size" {
  type    = number
  default = 512
}

variable "timeout_seconds" {
  type    = number
  default = 30
}

variable "reserved_concurrent_executions" {
  description = "-1 (default) leaves it unreserved; set low for DB-writing consumers."
  type        = number
  default     = -1
}

variable "environment_variables" {
  type    = map(string)
  default = {}
}

variable "vpc_enabled" {
  type    = bool
  default = false
}

variable "subnet_ids" {
  type    = list(string)
  default = []
}

variable "security_group_ids" {
  type    = list(string)
  default = []
}

variable "secret_arns" {
  description = "Secrets Manager ARNs this function may read."
  type        = list(string)
  default     = []
}

variable "extra_policy_statements" {
  description = "Additional IAM policy statements (as objects) beyond logs/VPC/secrets."
  type        = list(any)
  default     = []
}

variable "create_sqs_trigger" {
  description = <<-EOT
    Whether to create an SQS event source mapping for this function. A
    plain bool set directly by the caller, deliberately not inferred from
    `sqs_trigger_arn != null` — that ARN usually comes from a queue that
    doesn't exist yet on a fresh apply, so Terraform can't resolve the
    comparison at plan time and errors on `count`.
  EOT
  type        = bool
  default     = false
}

variable "sqs_trigger_arn" {
  description = "Required when create_sqs_trigger is true."
  type        = string
  default     = null
}

variable "sqs_batch_size" {
  type    = number
  default = 10
}

variable "log_retention_days" {
  type    = number
  default = 14
}
