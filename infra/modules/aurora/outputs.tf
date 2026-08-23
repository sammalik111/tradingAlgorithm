output "cluster_endpoint" {
  value = aws_rds_cluster.this.endpoint
}

output "reader_endpoint" {
  value = aws_rds_cluster.this.reader_endpoint
}

output "database_name" {
  value = aws_rds_cluster.this.database_name
}

output "master_user_secret_arn" {
  description = "ARN of the AWS-managed Secrets Manager secret holding the master password."
  value       = aws_rds_cluster.this.master_user_secret[0].secret_arn
}

output "cluster_resource_id" {
  value = aws_rds_cluster.this.cluster_resource_id
}
