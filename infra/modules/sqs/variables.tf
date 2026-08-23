variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "visibility_timeout_seconds" {
  description = "Should be >= 6x the consumer Lambda's timeout, per AWS guidance."
  type        = number
  default     = 180
}

variable "max_receive_count" {
  type    = number
  default = 5
}
