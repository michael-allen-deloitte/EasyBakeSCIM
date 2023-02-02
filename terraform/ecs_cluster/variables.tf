variable app_name {
  type        = string
  description = "Name used to identify the app in labels and names"
}

variable aws_region {
  type        = string
  default     = "us-east-1"
  description = "Region of AWS to deploy to"
}

variable cluster_name {
  type        = string
  description = "Name of the ECS Cluster"
}

variable ecr_repo_url {
  type        = string
  description = "URL of ECR repo to pull container from"
}

variable subnet_ids {
  type        = list(string)
  description = "List of subnet IDs to assign the LB to"
}

variable container_cpu {
  type        = number
  default     = 256
  description = "The CPU allocated for the container"
}

variable container_memory {
  type        = number
  default     = 512
  description = "The memory allocated for the container"
}

variable container_port {
  type        = number
  default     = 443
  description = "Port the container listens on"
}

variable host_port {
  type        = number
  default     = 443
  description = "Port the host listens on"
}

variable desired_container_count {
  type        = number
  default     = 1
  description = "Number of desired containers"
}

variable target_group_arn {
  type        = string
  description = "ARN of target group to link the service to the lb"
}

variable lb_security_group_id {
  type        = string
  description = "ID of the Load Balancer security group"
}