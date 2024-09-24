import pulumi_aws as aws
import pulumi

import vpc
import security_groups

stack_config = pulumi.Config("cfg")

LOAD_BALANCER_SG_NAME = stack_config.require("load_balancer_sg_name")
LOAD_BALANCER = stack_config.require("load_balancer")
ALB_LISTENER = stack_config.require("alb_listener")
ALB_BACKEND_LISTENER_RULE = stack_config.require("alb_backend_listener_rule")
ALB_FRONTEND_LISTENER_RULE = stack_config.require("alb_frontend_listener_rule")



load_balancer = aws.lb.LoadBalancer(
    LOAD_BALANCER,
    load_balancer_type="application",
    security_groups=[security_groups.lb_sg.id],
    subnets=vpc.default_vpc_subnets.ids,
    internal=False,
    xff_header_processing_mode="remove"
)