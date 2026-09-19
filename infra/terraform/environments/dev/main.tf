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
  name_prefix = "snow-ai-dev"

  public_subnet_cidrs = {
    "${var.aws_region}a" = "10.42.0.0/20"
    "${var.aws_region}b" = "10.42.16.0/20"
  }
  private_subnet_cidrs = {
    "${var.aws_region}a" = "10.42.128.0/20"
    "${var.aws_region}b" = "10.42.144.0/20"
  }
  tags = local.tags
}

module "ai_control_tower" {
  source               = "../../modules/ai-control-tower"
  name_prefix          = "snow-ai-dev"
  audit_retention_days = 90
  tags                 = local.tags
}

locals {
  tags = {
    Environment = "dev"
    Project     = "servicenow-staff-ai-engineer-showcase"
    ManagedBy   = "terraform"
  }
}
