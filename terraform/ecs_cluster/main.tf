# taken from https://medium.com/avmconsulting-blog/how-to-deploy-a-dockerised-node-js-application-on-aws-ecs-with-terraform-3e6bceb48785

# cluster creation
resource "aws_ecs_cluster" "my_cluster" {
  name = var.cluster_name
}

# task creation
resource "aws_ecs_task_definition" "ecs_task_def" {
  family                   = "${var.app_name}-task" 
  container_definitions    = <<DEFINITION
  [
    {
      "name": "${var.app_name}-task",
      "image": "${var.ecr_repo_url}",
      "essential": true,
      "portMappings": [
        {
          "containerPort": ${var.container_port},
          "hostPort": ${var.host_port}
        }
      ],
      "memory": ${var.container_memory},
      "cpu": ${var.container_cpu},
      "logConfiguration": 
      {
        "logDriver": "awslogs",
        "options": 
        {
          "awslogs-group": "/ecs/${var.app_name}-task",
          "awslogs-region": "${var.aws_region}",
          "awslogs-stream-prefix": "ecs"
        }
      } 
    }
  ]
  DEFINITION
  requires_compatibilities = ["FARGATE"] # Stating that we are using ECS Fargate
  network_mode             = "awsvpc"    # Using awsvpc as our network mode as this is required for Fargate
  memory                   = var.container_memory         # Specifying the memory our container requires
  cpu                      = var.container_cpu         # Specifying the CPU our container requires
  execution_role_arn       = "${aws_iam_role.ecsTaskExecutionRole.arn}"
}

resource "aws_iam_role" "ecsTaskExecutionRole" {
  name               = "${var.app_name}-ecsTaskExecutionRole"
  assume_role_policy = "${data.aws_iam_policy_document.assume_role_policy.json}"
}

resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRole_policy" {
  role       = "${aws_iam_role.ecsTaskExecutionRole.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# service creation
resource "aws_security_group" "service_security_group" {
  name = "${var.app_name}-service-security-group"
  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    # Only allowing traffic in from the load balancer security group
    security_groups = [var.lb_security_group_id]
  }

  egress {
    from_port   = 0 # Allowing any incoming port
    to_port     = 0 # Allowing any outgoing port
    protocol    = "-1" # Allowing any outgoing protocol 
    cidr_blocks = ["0.0.0.0/0"] # Allowing traffic out to all IP addresses
  }
}

resource "aws_ecs_service" "ecs_service" {
  name            = "${var.app_name}-service"                     # Naming our first service
  cluster         = "${aws_ecs_cluster.my_cluster.id}"            # Referencing our created Cluster
  task_definition = "${aws_ecs_task_definition.ecs_task_def.arn}" # Referencing the task our service will spin up
  launch_type     = "FARGATE"
  desired_count   = var.desired_container_count

  load_balancer {
    target_group_arn = var.target_group_arn # Referencing our target group
    container_name   = "${aws_ecs_task_definition.ecs_task_def.family}"
    container_port   = var.container_port # Specifying the container port
  }

  network_configuration {
    subnets          = var.subnet_ids
    assign_public_ip = true # Providing our containers with public IPs
    security_groups  = ["${aws_security_group.service_security_group.id}"] # Setting the security group
  }
}