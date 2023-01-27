provider aws {
    region = local.aws_region
}

module network {
  source = "./network"
  availability_zones  = local.availability_zones
}

locals {
  subnet_ids = [for subnet in module.network.subnets: subnet.id]
  depends_on = [module.network.subnets]
}

module load_balancer {
  source = "./load_balancer"
  app_name  = local.app_name
  vpc_id    = module.network.vpc.id
  lb_subnet_ids    = local.subnet_ids
  lb_cert_arn = local.lb_cert_arn
  depends_on = [module.network.vpc, 
  local.subnet_ids]
}

module ecs_cluster {
  source = "./ecs_cluster"
  app_name  = local.app_name
  cluster_name = "${local.app_name}-cluster"
  ecr_repo_url = local.ecr_repo_url
  subnet_ids = local.subnet_ids
  target_group_arn = module.load_balancer.target_group.arn
  lb_security_group_id = module.load_balancer.security_group.id
  depends_on = [local.subnet_ids, 
    module.load_balancer.target_group, 
    module.load_balancer.security_group]
}