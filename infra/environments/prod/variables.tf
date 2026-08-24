variable "project" {
  type    = string
  default = "trading-platform"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "availability_zones" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b"]
}

variable "github_owner" {
  type    = string
  default = "sammalik111"
}

variable "github_repo" {
  type    = string
  default = "tradingAlgorithm"
}

variable "deploy_branch" {
  description = "Branch the weekly CodePipeline deploys from."
  type        = string
  default     = "main"
}

variable "frontend_cors_origins" {
  description = "Populated with the CloudFront domain after the first apply (see outputs)."
  type        = list(string)
  default     = []
}

variable "bastion_ssh_public_key" {
  description = "SSH public key content for the DB bastion (e.g. `cat ~/.ssh/id_ed25519.pub`), for a native SSH tunnel (Navicat etc.) instead of SSM port-forwarding. The matching private key never touches this repo or Terraform state. Set together with bastion_allowed_ssh_cidr to enable; leave both unset for SSM-only access (the default, no open ports)."
  type        = string
  default     = null
}

variable "bastion_allowed_ssh_cidr" {
  description = "CIDR allowed to reach the bastion's SSH port when bastion_ssh_public_key is set. Scope to your own IP/32 (e.g. \"203.0.113.5/32\") -- never 0.0.0.0/0."
  type        = string
  default     = null
}
