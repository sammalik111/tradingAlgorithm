variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_id" {
  description = "Private subnet to launch the bastion in."
  type        = string
}

variable "aurora_security_group_id" {
  description = "Aurora's security group -- gets a standalone ingress rule granting the bastion access to 5432."
  type        = string
}

variable "instance_type" {
  type    = string
  default = "t4g.nano"
}
