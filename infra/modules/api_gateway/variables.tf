variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "lambda_function_name" {
  type = string
}

variable "lambda_function_arn" {
  type = string
}

variable "lambda_invoke_arn" {
  type = string
}

variable "cors_allowed_origins" {
  type = list(string)
}

variable "log_retention_days" {
  type    = number
  default = 14
}
