variable "project" {
  type = string
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "availability_zones" {
  type = list(string)
}

variable "nat_instance_type" {
  description = "Smallest ARM instance size — this only needs to shuttle low-volume Lambda egress traffic."
  type        = string
  default     = "t4g.nano"
}
