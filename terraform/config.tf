locals {
    app_name = "EasyBakeSCIM"
    aws_region = "us-east-1"
    availability_zones  = ["us-east-1a", "us-east-1b", "us-east-1c"]
    ecr_repo_url = "865845362383.dkr.ecr.us-east-1.amazonaws.com/ma-scim-pers:latest"
    lb_cert_arn = "arn:aws:acm:us-east-1:865845362383:certificate/eda0dda3-002a-4c82-904f-b4e61d7cdfcb"
}