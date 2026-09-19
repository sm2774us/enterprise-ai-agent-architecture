terraform {
  required_version = ">= 1.9.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "network" {
  source      = "../../modules/network"
  name_prefix = "snow-ai-prod"

  public_subnet_cidrs = {
    "${var.aws_region}a" = "10.43.0.0/20"
    "${var.aws_region}b" = "10.43.16.0/20"
    "${var.aws_region}c" = "10.43.32.0/20"
  }
  private_subnet_cidrs = {
    "${var.aws_region}a" = "10.43.128.0/20"
    "${var.aws_region}b" = "10.43.144.0/20"
    "${var.aws_region}c" = "10.43.160.0/20"
  }
  tags = local.tags
}

module "ai_control_tower" {
  source               = "../../modules/ai-control-tower"
  name_prefix          = "snow-ai-prod"
  audit_retention_days = 2555 # 7 years — audit/compliance retention
  tags                 = local.tags
}

locals {
  tags = {
    Environment = "prod"
    Project     = "servicenow-staff-ai-engineer-showcase"
    ManagedBy   = "terraform"
  }
}
