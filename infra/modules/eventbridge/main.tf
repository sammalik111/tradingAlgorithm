data "aws_iam_policy_document" "scheduler_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "scheduler" {
  name               = "${var.project}-${var.environment}-scheduler-role"
  assume_role_policy = data.aws_iam_policy_document.scheduler_assume_role.json
}

resource "aws_iam_role_policy" "scheduler_invoke_lambda" {
  name = "${var.project}-${var.environment}-scheduler-invoke"
  role = aws_iam_role.scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = [var.nightly_scrape_function_arn, var.recommendation_engine_function_arn]
      }
    ]
  })
}

resource "aws_scheduler_schedule" "nightly_scrape" {
  name                         = "${var.project}-${var.environment}-nightly-scrape"
  schedule_expression          = var.scrape_schedule_expression
  schedule_expression_timezone = "UTC"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = var.nightly_scrape_function_arn
    role_arn = aws_iam_role.scheduler.arn

    retry_policy {
      maximum_retry_attempts = 2
    }
  }
}

resource "aws_scheduler_schedule" "recommendation_engine" {
  name                         = "${var.project}-${var.environment}-recommendation-engine"
  schedule_expression          = var.recommendation_schedule_expression
  schedule_expression_timezone = "UTC"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = var.recommendation_engine_function_arn
    role_arn = aws_iam_role.scheduler.arn

    retry_policy {
      maximum_retry_attempts = 2
    }
  }
}

resource "aws_lambda_permission" "scheduler_nightly_scrape" {
  statement_id  = "AllowSchedulerInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.nightly_scrape_function_name
  principal     = "scheduler.amazonaws.com"
  source_arn    = aws_scheduler_schedule.nightly_scrape.arn
}

resource "aws_lambda_permission" "scheduler_recommendation_engine" {
  statement_id  = "AllowSchedulerInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.recommendation_engine_function_name
  principal     = "scheduler.amazonaws.com"
  source_arn    = aws_scheduler_schedule.recommendation_engine.arn
}
