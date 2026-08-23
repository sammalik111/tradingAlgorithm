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

# Container-image Lambdas can't be created before an image exists in ECR.
# These placeholders let a first `terraform apply` succeed on an empty
# account; the weekly/manual CodePipeline run replaces them with the real
# backend/workers images on its first successful deploy.
variable "bootstrap_image_uri" {
  type    = string
  default = "public.ecr.aws/lambda/python:3.11"
}
