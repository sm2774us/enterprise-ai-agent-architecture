output "audit_log_bucket" {
  value = aws_s3_bucket.audit_log.bucket
}

output "governance_alerts_topic_arn" {
  value = aws_sns_topic.governance_alerts.arn
}
