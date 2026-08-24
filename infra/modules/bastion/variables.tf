variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_id" {
  description = "Private subnet to launch the bastion in when SSH access is not enabled (the default)."
  type        = string
}

variable "public_subnet_id" {
  description = "Public subnet to launch the bastion in when SSH access is enabled (see ssh_public_key)."
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

variable "ssh_public_key" {
  description = "SSH public key content (e.g. `cat ~/.ssh/id_ed25519.pub`), for a native SSH tunnel instead of SSM port-forwarding. Set together with allowed_ssh_cidr to enable SSH access; leave both null for SSM-only (the default)."
  type        = string
  default     = null
}

variable "allowed_ssh_cidr" {
  description = "CIDR allowed to reach port 22 when ssh_public_key is set. Scope to your own IP/32 (e.g. \"203.0.113.5/32\") -- never 0.0.0.0/0."
  type        = string
  default     = null
}
