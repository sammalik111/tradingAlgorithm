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
