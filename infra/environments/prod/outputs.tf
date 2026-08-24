output "api_endpoint" {
  value = module.api_gateway.api_endpoint
}

output "frontend_url" {
  value = "https://${module.frontend_hosting.distribution_domain_name}"
}

output "frontend_bucket_name" {
  value = module.frontend_hosting.bucket_name
}

output "cloudfront_distribution_id" {
  value = module.frontend_hosting.distribution_id
}

output "ecr_repository_urls" {
  value = module.ecr.repository_urls
}

output "github_connection_arn" {
  description = "PENDING until authorized in the AWS Console: Developer Tools > Settings > Connections."
  value       = module.codepipeline.github_connection_arn
}

output "deploy_pipeline_name" {
  value = module.codepipeline.pipeline_name
}

output "aurora_cluster_endpoint" {
  value = module.aurora.cluster_endpoint
}

output "aurora_master_secret_arn" {
  description = "Secrets Manager ARN holding the RDS-managed master password -- see documentation/infra.md"
  value       = module.aurora.master_user_secret_arn
}

output "db_bastion_instance_id" {
  description = "For 'aws ssm start-session --target <id> ...' -- see documentation/infra.md"
  value       = module.db_bastion.instance_id
}

output "db_bastion_ssh_public_ip" {
  description = "Set only when bastion_ssh_public_key/bastion_allowed_ssh_cidr are configured. Elastic IP, stable across restarts -- see documentation/infra.md"
  value       = module.db_bastion.ssh_public_ip
}
