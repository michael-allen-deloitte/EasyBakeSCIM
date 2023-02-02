resource "aws_alb" "application_load_balancer" {
  name               = "${var.app_name}-lb" # Naming our load balancer
  load_balancer_type = "application"
  subnets = var.lb_subnet_ids
  # Referencing the security group
  security_groups = ["${aws_security_group.load_balancer_security_group.id}"]
}

# Creating a security group for the load balancer:
resource "aws_security_group" "load_balancer_security_group" {
  name = "${var.app_name}-lb-security-group"
  ingress {
    from_port   = var.lb_listen_port
    to_port     = var.app_listen_port
    protocol    = "tcp"
    cidr_blocks = var.lb_in_allowed_ips# Allowing traffic in from all sources
  }

  egress {
    from_port   = 0 # Allowing any incoming port
    to_port     = 0 # Allowing any outgoing port
    protocol    = "-1" # Allowing any outgoing protocol 
    cidr_blocks = ["0.0.0.0/0"] # Allowing traffic out to all IP addresses
  }
}

resource "aws_lb_target_group" "target_group" {
  name        = "${var.app_name}-target-group"
  port        = var.app_listen_port
  protocol    = var.target_group_protocol
  target_type = "ip"
  vpc_id      = "${var.vpc_id}" # Referencing the default VPC
  health_check {
    matcher = "200,301,302"
    path = "/"
    protocol    = var.target_group_protocol
  }
}

resource "aws_lb_listener" "listener" {
  load_balancer_arn = "${aws_alb.application_load_balancer.arn}" # Referencing our load balancer
  port              = "${var.lb_listen_port}"
  protocol          = var.lb_listener_protocol
  certificate_arn   = var.lb_cert_arn
  default_action {
    type             = "forward"
    target_group_arn = "${aws_lb_target_group.target_group.arn}" # Referencing our tagrte group
  }
}