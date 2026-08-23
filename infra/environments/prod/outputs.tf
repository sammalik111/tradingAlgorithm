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
