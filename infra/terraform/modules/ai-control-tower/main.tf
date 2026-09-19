# Declares the AI Control Tower's own governance state as infrastructure:
# an audit-log bucket with object-lock (WORM) for immutable decision
# records, and an SNS topic policy owners can subscribe to for
# deny/require-approval alerts -- the durable side of the in-memory audit
# trail the control-tower service keeps at runtime (see
# services/control-tower/app/governance/policy.py).

resource "aws_s3_bucket" "audit_log" {
  bucket = "${var.name_prefix}-ai-control-tower-audit-log"
  tags   = var.tags
}

resource "aws_s3_bucket_versioning" "audit_log" {
  bucket = aws_s3_bucket.audit_log.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_object_lock_configuration" "audit_log" {
  bucket = aws_s3_bucket.audit_log.id
  rule {
    default_retention {
      mode = "COMPLIANCE"
      days = var.audit_retention_days
    }
  }
}

resource "aws_sns_topic" "governance_alerts" {
  name = "${var.name_prefix}-ai-governance-alerts"
  tags = var.tags
}
