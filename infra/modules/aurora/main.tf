resource "aws_db_subnet_group" "aurora" {
  name       = "${var.project}-${var.environment}-aurora"
  subnet_ids = var.private_subnet_ids

  tags = { Name = "${var.project}-${var.environment}-aurora" }
}

# AWS periodically retires old Aurora PostgreSQL minor versions, so a
# hardcoded version string (e.g. "15.4") can start failing CreateDBCluster
# with no warning. Look up whatever the current default actually is instead.
data "aws_rds_engine_version" "postgresql" {
  engine = "aurora-postgresql"
  latest = true
}

# Aurora Serverless v2, single instance, no reader — the smallest and
# cheapest configuration that still gives us Postgres-compatible Aurora.
# Scale up (add a reader, raise max_capacity_acu) once real traffic needs it.
resource "aws_rds_cluster" "this" {
  cluster_identifier          = "${var.project}-${var.environment}"
  engine                      = "aurora-postgresql"
  engine_mode                 = "provisioned"
  engine_version              = data.aws_rds_engine_version.postgresql.version
  database_name               = var.database_name
  master_username             = var.master_username
  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.aurora.name
  vpc_security_group_ids = [var.security_group_id]

  serverlessv2_scaling_configuration {
    min_capacity = var.min_capacity_acu
    max_capacity = var.max_capacity_acu
  }

  backup_retention_period   = var.backup_retention_days
  preferred_backup_window   = "07:00-08:00"
  storage_encrypted         = true
  deletion_protection       = var.deletion_protection
  skip_final_snapshot       = !var.deletion_protection
  final_snapshot_identifier = var.deletion_protection ? "${var.project}-${var.environment}-final" : null

  tags = { Name = "${var.project}-${var.environment}-aurora" }
}

resource "aws_rds_cluster_instance" "writer" {
  cluster_identifier = aws_rds_cluster.this.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.this.engine
  engine_version     = aws_rds_cluster.this.engine_version

  tags = { Name = "${var.project}-${var.environment}-aurora-writer" }
}
