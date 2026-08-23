output "github_connection_arn" {
  description = "PENDING until a human authorizes it in the AWS Console (Developer Tools > Settings > Connections)."
  value       = aws_codestarconnections_connection.github.arn
}

output "pipeline_name" {
  value = aws_codepipeline.deploy.name
}
