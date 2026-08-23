# Empty placeholders: Terraform creates the secret, a human fills in the
# real value out-of-band (console or `aws secretsmanager put-secret-value`)
# so API keys never pass through Terraform state or a repo.
resource "aws_secretsmanager_secret" "anthropic_api_key" {
  name        = "${var.project}/${var.environment}/anthropic-api-key"
  description = "Claude API key used to generate recommendation rationale"
}

resource "aws_secretsmanager_secret" "quiver_quant_api_key" {
  name        = "${var.project}/${var.environment}/quiver-quant-api-key"
  description = "Optional paid data source; nightly scrape skips it while empty"
}

resource "aws_secretsmanager_secret" "robinhood_credentials" {
  name        = "${var.project}/${var.environment}/robinhood-credentials"
  description = "Unused until backend/integrations/robinhood is implemented"
}
