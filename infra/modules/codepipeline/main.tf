# Created in PENDING state. A human must finish the OAuth handshake once in
# the AWS Console (Developer Tools > Settings > Connections) before the
# pipeline can read the repo — this can't be scripted.
resource "aws_codestarconnections_connection" "github" {
  name          = "${var.project}-${var.environment}-github"
  provider_type = "GitHub"
}

resource "random_id" "artifact_bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "artifacts" {
  bucket = "${var.project}-${var.environment}-pipeline-artifacts-${random_id.artifact_bucket_suffix.hex}"
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_security_group" "codebuild" {
  name        = "${var.project}-${var.environment}-codebuild-sg"
  description = "CodeBuild deploy job"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-${var.environment}-codebuild-sg" }
}

resource "aws_security_group_rule" "codebuild_to_aurora" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = var.aurora_security_group_id
  source_security_group_id = aws_security_group.codebuild.id
  description              = "Allow the weekly deploy job to run Alembic migrations"
}

# --- CodeBuild ---------------------------------------------------------

data "aws_iam_policy_document" "codebuild_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["codebuild.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "codebuild" {
  name               = "${var.project}-${var.environment}-codebuild-role"
  assume_role_policy = data.aws_iam_policy_document.codebuild_assume_role.json
}

data "aws_iam_policy_document" "codebuild_permissions" {
  statement {
    sid = "Logs"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["*"]
  }

  statement {
    sid = "PullSourceArtifacts"
    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:PutObject",
    ]
    resources = ["${aws_s3_bucket.artifacts.arn}/*"]
  }

  statement {
    sid       = "ArtifactBucketList"
    actions   = ["s3:GetBucketLocation"]
    resources = [aws_s3_bucket.artifacts.arn]
  }

  statement {
    sid = "PushImages"
    actions = [
      "ecr:GetAuthorizationToken",
    ]
    resources = ["*"]
  }

  statement {
    sid = "PushImagesToRepos"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
    ]
    resources = [var.backend_ecr_arn, var.workers_ecr_arn]
  }

  statement {
    sid       = "ReadDbSecret"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [var.db_master_secret_arn]
  }

  statement {
    sid       = "DeployFrontend"
    actions   = ["s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
    resources = [var.frontend_bucket_arn, "${var.frontend_bucket_arn}/*"]
  }

  statement {
    sid       = "InvalidateCdn"
    actions   = ["cloudfront:CreateInvalidation"]
    resources = [var.cloudfront_distribution_arn]
  }

  statement {
    sid       = "UpdateLambdas"
    actions   = ["lambda:UpdateFunctionCode", "lambda:GetFunction"]
    resources = var.lambda_function_arns
  }

  statement {
    sid = "VpcNetworking"
    actions = [
      "ec2:CreateNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DeleteNetworkInterface",
      "ec2:DescribeSubnets",
      "ec2:DescribeSecurityGroups",
      "ec2:DescribeDhcpOptions",
      "ec2:DescribeVpcs",
      "ec2:CreateNetworkInterfacePermission",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "codebuild" {
  name   = "${var.project}-${var.environment}-codebuild-policy"
  role   = aws_iam_role.codebuild.id
  policy = data.aws_iam_policy_document.codebuild_permissions.json
}

resource "aws_cloudwatch_log_group" "codebuild" {
  name              = "/aws/codebuild/${var.project}-${var.environment}-deploy"
  retention_in_days = 14
}

resource "aws_codebuild_project" "deploy" {
  name         = "${var.project}-${var.environment}-deploy"
  service_role = aws_iam_role.codebuild.arn

  artifacts {
    type = "CODEPIPELINE"
  }

  # Explicit rather than relying on the API's implicit default, so there's
  # a guaranteed, known place to find build output.
  logs_config {
    cloudwatch_logs {
      status     = "ENABLED"
      group_name = aws_cloudwatch_log_group.codebuild.name
    }
  }

  environment {
    # Smallest available CodeBuild compute size.
    compute_type    = "BUILD_GENERAL1_SMALL"
    image           = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    type            = "LINUX_CONTAINER"
    privileged_mode = true # required to build Docker images

    environment_variable {
      name  = "BACKEND_ECR_URL"
      value = var.backend_ecr_url
    }
    environment_variable {
      name  = "WORKERS_ECR_URL"
      value = var.workers_ecr_url
    }
    environment_variable {
      name  = "DB_MASTER_SECRET_ARN"
      value = var.db_master_secret_arn
    }
    environment_variable {
      name  = "DB_HOST"
      value = var.db_host
    }
    environment_variable {
      name  = "DB_NAME"
      value = var.db_name
    }
    environment_variable {
      name  = "FRONTEND_BUCKET"
      value = var.frontend_bucket_name
    }
    environment_variable {
      name  = "CLOUDFRONT_DISTRIBUTION_ID"
      value = var.cloudfront_distribution_id
    }
    environment_variable {
      name  = "VITE_API_BASE_URL"
      value = "${var.api_endpoint}/api/v1"
    }
    environment_variable {
      name  = "BACKEND_API_FUNCTION"
      value = var.backend_api_function_name
    }
    environment_variable {
      name  = "RECOMMENDATION_ENGINE_FUNCTION"
      value = var.recommendation_engine_function_name
    }
    environment_variable {
      name  = "NIGHTLY_SCRAPE_FUNCTION"
      value = var.nightly_scrape_function_name
    }
    environment_variable {
      name  = "PROCESS_TRADE_MESSAGE_FUNCTION"
      value = var.process_trade_message_function_name
    }
  }

  vpc_config {
    vpc_id             = var.vpc_id
    subnets            = var.private_subnet_ids
    security_group_ids = [aws_security_group.codebuild.id]
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "infra/codebuild/buildspec.yml"
  }
}

# --- CodePipeline --------------------------------------------------------

data "aws_iam_policy_document" "codepipeline_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["codepipeline.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "codepipeline" {
  name               = "${var.project}-${var.environment}-codepipeline-role"
  assume_role_policy = data.aws_iam_policy_document.codepipeline_assume_role.json
}

data "aws_iam_policy_document" "codepipeline_permissions" {
  statement {
    sid       = "ArtifactBucket"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:GetBucketVersioning"]
    resources = [aws_s3_bucket.artifacts.arn, "${aws_s3_bucket.artifacts.arn}/*"]
  }

  statement {
    sid       = "UseGithubConnection"
    actions   = ["codestar-connections:UseConnection"]
    resources = [aws_codestarconnections_connection.github.arn]
  }

  statement {
    sid = "RunCodeBuild"
    actions = [
      "codebuild:BatchGetBuilds",
      "codebuild:StartBuild",
    ]
    resources = [aws_codebuild_project.deploy.arn]
  }
}

resource "aws_iam_role_policy" "codepipeline" {
  name   = "${var.project}-${var.environment}-codepipeline-policy"
  role   = aws_iam_role.codepipeline.id
  policy = data.aws_iam_policy_document.codepipeline_permissions.json
}

resource "aws_codepipeline" "deploy" {
  name     = "${var.project}-${var.environment}-deploy"
  role_arn = aws_iam_role.codepipeline.arn

  artifact_store {
    type     = "S3"
    location = aws_s3_bucket.artifacts.bucket
  }

  # DetectChanges = false: a normal `git push` never triggers this pipeline.
  # It only runs on the weekly EventBridge schedule below, or a manual
  # "Release change" click in the console.
  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeStarSourceConnection"
      version          = "1"
      output_artifacts = ["source_output"]

      configuration = {
        ConnectionArn    = aws_codestarconnections_connection.github.arn
        FullRepositoryId = "${var.github_owner}/${var.github_repo}"
        BranchName       = var.branch_name
        DetectChanges    = "false"
      }
    }
  }

  stage {
    name = "Deploy"

    action {
      name             = "BuildAndDeploy"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["source_output"]
      output_artifacts = ["deploy_output"]

      configuration = {
        ProjectName = aws_codebuild_project.deploy.name
      }
    }
  }
}

# --- Weekly trigger --------------------------------------------------------

data "aws_iam_policy_document" "scheduler_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "deploy_scheduler" {
  name               = "${var.project}-${var.environment}-deploy-scheduler-role"
  assume_role_policy = data.aws_iam_policy_document.scheduler_assume_role.json
}

resource "aws_iam_role_policy" "deploy_scheduler" {
  name = "${var.project}-${var.environment}-deploy-scheduler-policy"
  role = aws_iam_role.deploy_scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "codepipeline:StartPipelineExecution"
        Resource = aws_codepipeline.deploy.arn
      }
    ]
  })
}

resource "aws_scheduler_schedule" "weekly_deploy" {
  name                         = "${var.project}-${var.environment}-weekly-deploy"
  schedule_expression          = var.deploy_schedule_expression
  schedule_expression_timezone = "UTC"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = "arn:aws:scheduler:::aws-sdk:codepipeline:startPipelineExecution"
    role_arn = aws_iam_role.deploy_scheduler.arn

    input = jsonencode({ Name = aws_codepipeline.deploy.name })
  }
}
