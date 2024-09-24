import pulumi

import vpc
import security_groups
import iam
import load_balancer
import cloudwatch
import ecr
import rds
import ecs_cluster
import cloudfront
import ses
import s3_bucket

default_vpc = vpc.default_vpc
default_vpc_subnets = vpc.default_vpc_subnets
region_subnet = vpc.region_subnet
log_group = cloudwatch.log_group
lb_sg = security_groups.lb_sg
ses_vpc_endpoint_sg = ses.ses_vpc_endpoint_sg
sg = security_groups.sg
task_execution_role = iam.task_execution_role
ecr_policy = iam.ecr_policy
role_policy_attachment = iam.role_policy_attachment
log_policy = iam.log_policy
task_execution_role_policy_attach = iam.task_execution_role_policy_attach
ecs_instance_role = iam.ecs_instance_role
ecs_instance_role_policy_attach = iam.ecs_instance_role_policy_attach
s3_full_access_policy_attachment = iam.s3_full_access_policy_attachment
ses_policy = iam.ses_policy
ses_policy_attachment = iam.ses_policy_attachment
ecs_instance_profile = iam.ecs_instance_profile
ecs_instance_ami = ecs_cluster.ecs_instance_ami
cluster_name = ecs_cluster.cluster.name
launch_config = ecs_cluster.launch_config
auto_scaling = ecs_cluster.auto_scaling
cp = ecs_cluster.cp
cluster = ecs_cluster.cluster
example_cluster_capacity_providers = ecs_cluster.example_cluster_capacity_providers
load_balancer = load_balancer.load_balancer
back_atg = ecs_cluster.back_atg
front_atg = ecs_cluster.front_atg
wl = ecs_cluster.wl
backend_rule = ecs_cluster.backend_rule
frontend_rule = ecs_cluster.frontend_rule
db_sg = security_groups.db_sg
app_ecr_repo = ecr.app_ecr_repo
app_lifecycle_policy = ecr.app_lifecycle_policy
app_registry = ecr.app_registry
fastapi_image = ecr.fastapi_image
frontend_image = ecr.frontend_image
db_instance = rds.db_instance
bucket = s3_bucket.bucket
default_route_table = vpc.default_route_table
s3_vpc_endpoint = s3_bucket.s3_vpc_endpoint
ses_vpc_endpoint = ses.ses_vpc_endpoint
email_identity = ses.email_identity
email_user = iam.email_user
email_user_policy = iam.email_user_policy
email_access_key = iam.email_access_key
bucket_policy = s3_bucket.bucket_policy
back_task_def = ecs_cluster.back_task_def
backservice = ecs_cluster.backservice
front_task_def = ecs_cluster.front_task_def
frontservice = ecs_cluster.frontservice
cloudfront_distribution = cloudfront.cloudfront_distribution
lambda_role = iam.lambda_role
cloudfront_invalidation_policy = iam.cloudfront_invalidation_policy
lambda_function = cloudfront.lambda_function


pulumi.export("app_url", pulumi.Output.concat("http://", load_balancer.dns_name))
pulumi.export('log_group_name', log_group.name)
pulumi.export("db_connection_string", db_instance.endpoint)
pulumi.export("NOTE", "You may have to wait a minute for AWS to spin up the back_service. So if the URL throws a 503 "
                      "error, try again after a bit.")
