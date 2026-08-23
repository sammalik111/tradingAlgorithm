terraform {
  required_version = ">= 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }

  # Bootstrap an S3 bucket (+ DynamoDB lock table) once, by hand, then
  # uncomment this block and `terraform init -migrate-state`. Left as local
  # state until then so a first `terraform init` works with zero AWS setup.
  # backend "s3" {
  #   bucket         = "trading-platform-tfstate"
  #   key            = "prod/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "trading-platform-tfstate-lock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region
}
