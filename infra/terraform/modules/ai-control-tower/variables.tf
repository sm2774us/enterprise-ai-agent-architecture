variable "name_prefix" {
  type        = string
  description = "Prefix applied to every resource name for this environment."
}

variable "audit_retention_days" {
  type        = number
  description = "Minimum immutable retention period for audit records, in days."
  default     = 365
}

variable "tags" {
  type        = map(string)
  description = "Common resource tags."
  default     = {}
}
