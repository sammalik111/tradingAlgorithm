output "anthropic_api_key_arn" {
  value = aws_secretsmanager_secret.anthropic_api_key.arn
}

output "quiver_quant_api_key_arn" {
  value = aws_secretsmanager_secret.quiver_quant_api_key.arn
}

output "robinhood_credentials_arn" {
  value = aws_secretsmanager_secret.robinhood_credentials.arn
}
