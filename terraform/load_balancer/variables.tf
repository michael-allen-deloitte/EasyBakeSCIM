variable app_name {
  type        = string
  description = "Name used to identify the app in labels and names"
}

variable vpc_id {
  type        = string
  description = "ID for the vpc for the target group"
}

variable lb_listen_port {
  type        = number
  default     = 443
  description = "Port the Load Balancer will listen on"
}

variable app_listen_port {
  type        = number
  default     = 443
  description = "Port the App listens on"
}

variable lb_in_allowed_ips {
  type        = list(string)
  default     = ["0.0.0.0/0"]
  description = "List of IPs allowed inbound connetions to the LB"
}

variable lb_subnet_ids {
  type        = list(string)
  description = "List of subnet IDs to assign the LB to"
}

variable target_group_protocol {
  type        = string
  default     = "HTTPS"
  description = "Protocol for container"
}

variable lb_listener_protocol {
  type        = string
  default     = "HTTPS"
  description = "Protocol for LB"
}

variable lb_cert_arn {
  type        = string
  default     = null
  description = "ARN for the cert to be used for HTTPS"
}
