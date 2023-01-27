output application_load_balancer {
  value       = aws_alb.application_load_balancer
  description = "Application Load Balancer object"
}

output security_group {
  value       = aws_security_group.load_balancer_security_group
  description = "ALB Security Group object"
}

output target_group {
  value       = aws_lb_target_group.target_group
  description = "ALB Target group object"
}