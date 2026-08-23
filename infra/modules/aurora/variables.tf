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

variable "database_name" {
  type    = string
  default = "trading"
}

variable "master_username" {
  type    = string
  default = "trading_admin"
}

variable "min_capacity_acu" {
  description = "Smallest Aurora Serverless v2 capacity unit AWS allows."
  type        = number
  default     = 0.5
}

variable "max_capacity_acu" {
  type    = number
  default = 2
}

variable "backup_retention_days" {
  type    = number
  default = 7
}

variable "deletion_protection" {
  type    = bool
  default = true
}
