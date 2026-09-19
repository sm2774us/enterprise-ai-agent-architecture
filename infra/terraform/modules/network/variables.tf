variable "name_prefix" {
  type        = string
  description = "Prefix applied to every resource name for this environment."
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC."
  default     = "10.42.0.0/16"
}

variable "public_subnet_cidrs" {
  type        = map(string)
  description = "Map of availability_zone => CIDR for public subnets."
}

variable "private_subnet_cidrs" {
  type        = map(string)
  description = "Map of availability_zone => CIDR for private subnets."
}

variable "tags" {
  type        = map(string)
  description = "Common resource tags."
  default     = {}
}
