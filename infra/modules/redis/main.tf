# ElastiCache Serverless: pay-per-use rather than an always-on node, which
# suits a cache that's mostly idle outside of nightly recommendation runs
# and daytime API reads.
resource "aws_elasticache_serverless_cache" "this" {
  engine = "redis"
  name   = "${var.project}-${var.environment}"

  cache_usage_limits {
    data_storage {
      maximum = var.max_storage_gb
      unit    = "GB"
    }
    ecpu_per_second {
      maximum = var.max_ecpu_per_second
    }
  }

  subnet_ids         = var.private_subnet_ids
  security_group_ids = [var.security_group_id]

  tags = { Name = "${var.project}-${var.environment}-redis" }
}
