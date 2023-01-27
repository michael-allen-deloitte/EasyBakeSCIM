output vpc {
  value       = aws_default_vpc.default_vpc
  sensitive   = false
  description = "Default VPC"
}

output subnets {
  value       = aws_default_subnet.default_subnets
  sensitive   = false
  description = "Default Subnets"
}