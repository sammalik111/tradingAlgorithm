module "networking" {
  source = "../../modules/networking"

  project            = var.project
  availability_zones = var.availability_zones
}

module "aurora" {
  source = "../../modules/aurora"

  project            = var.project
  environment        = var.environment
  private_subnet_ids = module.networking.private_subnet_ids
  security_group_id  = module.networking.aurora_security_group_id
}

module "redis" {
  source = "../../modules/redis"

  project            = var.project
  environment        = var.environment
  private_subnet_ids = module.networking.private_subnet_ids
  security_group_id  = module.networking.redis_security_group_id
}

module "sqs" {
  source = "../../modules/sqs"

  project     = var.project
  environment = var.environment
}

module "secrets" {
  source = "../../modules/secrets"

  project     = var.project
  environment = var.environment
}

module "ecr" {
  source = "../../modules/ecr"

  project          = var.project
  environment      = var.environment
  repository_names = ["backend", "workers"]
}

module "frontend_hosting" {
  source = "../../modules/frontend_hosting"

  project     = var.project
  environment = var.environment
}

locals {
  # DB_SECRET_ARN/DB_HOST/DB_NAME (no DATABASE_URL) tells the app to resolve
  # the password from the RDS-managed Secrets Manager secret at cold start
  # instead of it ever being written into a Lambda environment variable.
  shared_lambda_env = {
    ENVIRONMENT   = var.environment
    LOG_LEVEL     = "INFO"
    DB_SECRET_ARN = module.aurora.master_user_secret_arn
    DB_HOST       = module.aurora.cluster_endpoint
    DB_NAME       = module.aurora.database_name
  }

  cors_origins = length(var.frontend_cors_origins) > 0 ? var.frontend_cors_origins : [
    "https://${module.frontend_hosting.distribution_domain_name}"
  ]
}

module "backend_api_lambda" {
  source     = "../../modules/lambda"
  depends_on = [null_resource.bootstrap_backend_image]

  project         = var.project
  environment     = var.environment
  function_name   = "backend-api"
  image_uri       = local.backend_bootstrap_image
  image_command   = ["trading_backend.main.handler"]
  memory_size     = 512
  timeout_seconds = 15

  vpc_enabled        = true
  subnet_ids         = module.networking.private_subnet_ids
  security_group_ids = [module.networking.lambda_security_group_id]

  secret_arns = [
    module.aurora.master_user_secret_arn,
    module.secrets.anthropic_api_key_arn,
  ]

  environment_variables = merge(local.shared_lambda_env, {
    # rediss:// (TLS), not redis:// -- ElastiCache Serverless enforces
    # in-transit encryption unconditionally; there's no opt-out, so a
    # plaintext client connection fails outright.
    REDIS_URL            = "rediss://${module.redis.endpoint_address}:${module.redis.endpoint_port}/0"
    CORS_ALLOWED_ORIGINS = join(",", local.cors_origins)
  })
}

module "recommendation_engine_lambda" {
  source     = "../../modules/lambda"
  depends_on = [null_resource.bootstrap_backend_image]

  project         = var.project
  environment     = var.environment
  function_name   = "recommendation-engine"
  image_uri       = local.backend_bootstrap_image
  image_command   = ["trading_backend.recommendation_engine.lambda_handler.handler"]
  memory_size     = 512
  timeout_seconds = 300

  vpc_enabled        = true
  subnet_ids         = module.networking.private_subnet_ids
  security_group_ids = [module.networking.lambda_security_group_id]

  secret_arns = [
    module.aurora.master_user_secret_arn,
    module.secrets.anthropic_api_key_arn,
  ]

  environment_variables = merge(local.shared_lambda_env, {
    REDIS_URL = "rediss://${module.redis.endpoint_address}:${module.redis.endpoint_port}/0"
  })
}

module "nightly_scrape_lambda" {
  source     = "../../modules/lambda"
  depends_on = [null_resource.bootstrap_workers_image]

  project         = var.project
  environment     = var.environment
  function_name   = "nightly-scrape"
  image_uri       = local.workers_bootstrap_image
  image_command   = ["trading_workers.jobs.nightly_scrape.handler"]
  memory_size     = 512
  timeout_seconds = 300

  # Not in the VPC: it only needs internet (to scrape) and the public SQS
  # API, so it skips the NAT Gateway hop private subnets require.
  vpc_enabled = false

  environment_variables = {
    ENVIRONMENT            = var.environment
    LOG_LEVEL              = "INFO"
    TRADE_INGEST_QUEUE_URL = module.sqs.queue_url
  }

  extra_policy_statements = [
    {
      sid       = "SendToIngestQueue"
      actions   = ["sqs:SendMessage"]
      resources = [module.sqs.queue_arn]
    }
  ]

  secret_arns = [module.secrets.quiver_quant_api_key_arn]
}

module "process_trade_message_lambda" {
  source     = "../../modules/lambda"
  depends_on = [null_resource.bootstrap_workers_image]

  project         = var.project
  environment     = var.environment
  function_name   = "process-trade-message"
  image_uri       = local.workers_bootstrap_image
  image_command   = ["trading_workers.jobs.process_trade_message.handler"]
  memory_size     = 256
  timeout_seconds = 30

  # A reservation here (to keep SQS bursts from opening more DB connections
  # than Aurora's 0.5 ACU floor can serve) is left off deliberately: a new
  # AWS account's default unreserved-concurrency pool is often too small to
  # carve any out of without erroring. Revisit once there's a quota bump or
  # real traffic to size against.

  vpc_enabled        = true
  subnet_ids         = module.networking.private_subnet_ids
  security_group_ids = [module.networking.lambda_security_group_id]

  create_sqs_trigger = true
  sqs_trigger_arn    = module.sqs.queue_arn

  secret_arns = [module.aurora.master_user_secret_arn]

  environment_variables = local.shared_lambda_env
}

module "api_gateway" {
  source = "../../modules/api_gateway"

  project              = var.project
  environment          = var.environment
  lambda_function_name = module.backend_api_lambda.function_name
  lambda_function_arn  = module.backend_api_lambda.function_arn
  lambda_invoke_arn    = module.backend_api_lambda.invoke_arn
  cors_allowed_origins = local.cors_origins
}

module "eventbridge" {
  source = "../../modules/eventbridge"

  project     = var.project
  environment = var.environment

  nightly_scrape_function_arn         = module.nightly_scrape_lambda.function_arn
  nightly_scrape_function_name        = module.nightly_scrape_lambda.function_name
  recommendation_engine_function_arn  = module.recommendation_engine_lambda.function_arn
  recommendation_engine_function_name = module.recommendation_engine_lambda.function_name
}

module "codepipeline" {
  source = "../../modules/codepipeline"

  project     = var.project
  environment = var.environment

  github_owner = var.github_owner
  github_repo  = var.github_repo
  branch_name  = var.deploy_branch

  vpc_id                   = module.networking.vpc_id
  private_subnet_ids       = module.networking.private_subnet_ids
  aurora_security_group_id = module.networking.aurora_security_group_id

  backend_ecr_url = module.ecr.repository_urls["backend"]
  workers_ecr_url = module.ecr.repository_urls["workers"]
  backend_ecr_arn = module.ecr.repository_arns["backend"]
  workers_ecr_arn = module.ecr.repository_arns["workers"]

  db_master_secret_arn = module.aurora.master_user_secret_arn
  db_host              = module.aurora.cluster_endpoint
  db_name              = module.aurora.database_name

  frontend_bucket_name        = module.frontend_hosting.bucket_name
  frontend_bucket_arn         = "arn:aws:s3:::${module.frontend_hosting.bucket_name}"
  cloudfront_distribution_id  = module.frontend_hosting.distribution_id
  cloudfront_distribution_arn = module.frontend_hosting.distribution_arn

  api_endpoint = module.api_gateway.api_endpoint

  backend_api_function_name           = module.backend_api_lambda.function_name
  recommendation_engine_function_name = module.recommendation_engine_lambda.function_name
  nightly_scrape_function_name        = module.nightly_scrape_lambda.function_name
  process_trade_message_function_name = module.process_trade_message_lambda.function_name

  lambda_function_arns = [
    module.backend_api_lambda.function_arn,
    module.recommendation_engine_lambda.function_arn,
    module.nightly_scrape_lambda.function_arn,
    module.process_trade_message_lambda.function_arn,
  ]
}
