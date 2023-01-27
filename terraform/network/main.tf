# Providing a reference to our default VPC
resource "aws_default_vpc" "default_vpc" {
}

# Providing a reference to our default subnets
resource "aws_default_subnet" "default_subnets" {
  for_each = toset(var.availability_zones)
  availability_zone = each.key
}