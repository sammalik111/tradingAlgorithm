variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "security_group_id" {
  type = string
}

variable "max_storage_gb" {
  description = "Ceiling on ElastiCache Serverless storage; keeps the cache tiny and cheap."
  type        = number
  default     = 1
}

variable "max_ecpu_per_second" {
  type    = number
  default = 1000
}
