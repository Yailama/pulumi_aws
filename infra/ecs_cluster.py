import json
import pulumi
import pulumi_aws as aws
import vpc
import load_balancer
import ses
import iam
import ecr
import rds
import s3_bucket
import cloudwatch
import security_groups

stack_config = pulumi.Config("cfg")
BACKEND_TASK_DEFINITION = stack_config.require("backend_task_definition")
BACKEND_TASK_DEFINITION_FAMILY = stack_config.require("backend_task_definition_family")
BACKEND_TASK_RUNNER = stack_config.require("backend_task_runner")

FRONTEND_TASK_DEFINITION = stack_config.require("frontend_task_definition")
FRONTEND_TASK_DEFINITION_FAMILY = stack_config.require("frontend_task_definition_family")
FRONTEND_TASK_RUNNER = stack_config.require("frontend_task_runner")

CLUSTER_NAME = stack_config.require("cluster_name")
ECS_LAUNCH_CONFING = stack_config.require("ecs_launch_confing")
AUTOSCALE_GROUP = stack_config.require("autoscale_group")
CAPACITY_PROVIDER = stack_config.require("capacity_provider")
BACKEND_TARGET_GROUP = stack_config.require("backend_target_group")
FRONTEND_TARGET_GROUP = stack_config.require("frontend_target_group")
ASG_SIZE = int(stack_config.require("autoscaling_group_size"))
INSTANCE_TYPE = stack_config.require("instance_type")
KEY_NAME = stack_config.get("key_name")

ALB_BACKEND_LISTENER_RULE = stack_config.require("alb_backend_listener_rule")
ALB_FRONTEND_LISTENER_RULE = stack_config.require("alb_frontend_listener_rule")

REGION = stack_config.get("region", "us-east-1")
AVAIL_ZONE = REGION + "a"  # e.g. us-east-1a

ALB_LISTENER = stack_config.require("alb_listener")


ecs_instance_ami = aws.ec2.get_ami(
    most_recent="true",
    owners=["amazon"],
    filters=[
        {
            "name": "name",
            "values": ["amzn2-ami-ecs-hvm-*-x86_64-*"]
        }
    ]
)

user_data = '''#!/bin/bash
echo ECS_CLUSTER={cluster_nm} >> /etc/ecs/ecs.config'''.format(cluster_nm=CLUSTER_NAME)

launch_config = aws.ec2.LaunchConfiguration(
    ECS_LAUNCH_CONFING,
    image_id=ecs_instance_ami.id,
    instance_type=INSTANCE_TYPE,
    associate_public_ip_address=True,
    key_name=KEY_NAME,
    iam_instance_profile=iam.ecs_instance_profile.name,
    user_data=user_data,
)

auto_scaling = aws.autoscaling.Group(
    AUTOSCALE_GROUP,
    availability_zones=[AVAIL_ZONE],
    launch_configuration=launch_config.name,
    min_size=ASG_SIZE,
    max_size=ASG_SIZE + 1,
    protect_from_scale_in=False
)

cp = aws.ecs.CapacityProvider(
    CAPACITY_PROVIDER,
    auto_scaling_group_provider=aws.ecs.CapacityProviderAutoScalingGroupProviderArgs(
        auto_scaling_group_arn=auto_scaling.arn,
        managed_termination_protection="DISABLED",
        managed_scaling=aws.ecs.CapacityProviderAutoScalingGroupProviderManagedScalingArgs(
            status="DISABLED"
        )
    ),
)

cluster = aws.ecs.Cluster(
    "cluster",
    name=CLUSTER_NAME,
)

example_cluster_capacity_providers = aws.ecs.ClusterCapacityProviders("exampleClusterCapacityProviders",
                                                                      cluster_name=cluster.name,
                                                                      capacity_providers=[cp.name],
                                                                      )
back_atg = aws.lb.TargetGroup(
    BACKEND_TARGET_GROUP,
    port=80,
    protocol="HTTP",
    target_type="ip",
    vpc_id=vpc.default_vpc.id,
    health_check={
        "path": "/api/"
    }
)

front_atg = aws.lb.TargetGroup(FRONTEND_TARGET_GROUP,
                               port=80,
                               protocol="HTTP",
                               target_type="ip",
                               vpc_id=vpc.default_vpc.id
                               )


back_task_def = aws.ecs.TaskDefinition(
    BACKEND_TASK_DEFINITION,
    family=BACKEND_TASK_DEFINITION_FAMILY,
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["EC2"],
    execution_role_arn=iam.task_execution_role.arn,
    container_definitions=pulumi.Output.all(port=80,
                                            app_name=BACKEND_TASK_DEFINITION,
                                            image_name=ecr.fastapi_image.image_name.apply(lambda x: f"{x}"),
                                            db_server=rds.db_instance.endpoint,
                                            db_name=rds.DB_NAME,
                                            db_user=rds.DB_USER,
                                            db_password=rds.get_db_secrets(rds.db_instance),
                                            bucket_name=s3_bucket.bucket.id,
                                            log_group_name=cloudwatch.log_group.name,
                                            region=REGION,
                                            smtp_secret=iam.email_access_key.id,
                                            smtp_password=iam.email_access_key.ses_smtp_password_v4,
                                            smtp_server=ses.ses_vpc_endpoint.dns_entries.apply(
                                                lambda x: ", ".join([y["dns_name"] for y in x]))
                                            )
    .apply(lambda args: json.dumps([{
        "name": args["app_name"],
        "image": args["image_name"],
        "portMappings": [{
            "containerPort": 80,
            "hostPort": 80,
            "protocol": "tcp"
        }],
        'logConfiguration': {
            'logDriver': 'awslogs',
            'options': {
                'awslogs-group': args["log_group_name"],
                'awslogs-region': 'us-east-1',
                'awslogs-stream-prefix': 'ecs',
            }
        },
        "environment": [
            {"name": "DB_SERVER",
             "value": args["db_server"]
             },
            {
                "name": "DB_NAME",
                "value": args["db_name"]
            },
            {
                "name": "DB_USER",
                "value": args["db_user"]
            },
            {
                "name": "DB_PASSWORD",
                "value": args["db_password"]
            },
            {
                "name": "S3_BUCKET",
                "value": args["bucket_name"]
            },
            {
                "name": "REGION",
                "value": args["region"]
            },
            {
                "name": "SMTP_SECRET",
                "value": args["smtp_secret"]
            },
            {
                "name": "SMTP_PASSWORD",
                "value": args["smtp_password"]
            },
            {
                "name": "SMTP_SERVER",
                "value": args["smtp_server"]
            }

        ]
    }])),
    opts=pulumi.ResourceOptions(depends_on=[cluster, rds.db_instance])
)

backservice = aws.ecs.Service(
    BACKEND_TASK_RUNNER,
    cluster=cluster.arn,
    launch_type="EC2",
    desired_count=1,
    deployment_maximum_percent=100,
    deployment_minimum_healthy_percent=50,
    task_definition=back_task_def.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=False,
        subnets=vpc.default_vpc_subnets.ids,
        security_groups=[security_groups.sg.id],
    ),
    load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
        target_group_arn=back_atg.arn,
        container_name=BACKEND_TASK_DEFINITION,
        container_port=80,
    )],
    opts=pulumi.ResourceOptions(depends_on=[])
)

front_task_def = aws.ecs.TaskDefinition(
    FRONTEND_TASK_DEFINITION,
    family=FRONTEND_TASK_DEFINITION_FAMILY,
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["EC2"],
    execution_role_arn=iam.task_execution_role.arn,
    container_definitions=pulumi.Output.all(port=80,
                                            app_name=FRONTEND_TASK_DEFINITION,
                                            image_name=ecr.frontend_image.image_name.apply(lambda x: f"{x}"),
                                            log_group_name=cloudwatch.log_group.name.apply(lambda x: f"{x}"),
                                            region=REGION,
                                            base_url=pulumi.Output.concat("http://", load_balancer.load_balancer.dns_name)
                                            )
    .apply(lambda args: json.dumps([{
        "name": args["app_name"],
        "image": args["image_name"],
        "portMappings": [{
            "containerPort": 80,
            "hostPort": 80,
            "protocol": "tcp"
        }],
        'logConfiguration': {
            'logDriver': 'awslogs',
            'options': {
                'awslogs-group': args["log_group_name"],
                'awslogs-region': 'us-east-1',
                'awslogs-stream-prefix': 'ecs',
            }
        },
        "environment": [{
            "name": "BASE_URL",
            "value": args["base_url"]
        }]
    }])),
    opts=pulumi.ResourceOptions(depends_on=[cluster])
)

frontservice = aws.ecs.Service(
    FRONTEND_TASK_RUNNER,
    cluster=cluster.arn,
    launch_type="EC2",
    desired_count=1,
    deployment_maximum_percent=100,
    deployment_minimum_healthy_percent=50,
    task_definition=front_task_def.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=False,
        subnets=vpc.default_vpc_subnets.ids,
        security_groups=[security_groups.sg.id],
    ),
    load_balancers=[aws.ecs.ServiceLoadBalancerArgs(
        target_group_arn=front_atg.arn,
        container_name=FRONTEND_TASK_DEFINITION,
        container_port=80,
    )],
    opts=pulumi.ResourceOptions(depends_on=[backservice]),
)


wl = aws.lb.Listener(
    ALB_LISTENER,
    load_balancer_arn=load_balancer.load_balancer.arn,
    port=80,
    default_actions=[aws.lb.ListenerDefaultActionArgs(type="forward", target_group_arn=back_atg.arn)]
)

backend_rule = aws.lb.ListenerRule(ALB_BACKEND_LISTENER_RULE,
                                   listener_arn=wl.arn,
                                   actions=[aws.lb.ListenerRuleActionArgs(
                                       type="forward",
                                       target_group_arn=back_atg.arn,
                                   )],
                                   conditions=[
                                       aws.lb.ListenerRuleConditionArgs(
                                           path_pattern=aws.lb.ListenerRuleConditionPathPatternArgs(
                                               values=["/api/*"],
                                           ),
                                       ),
                                   ],
                                   priority=1
                                   )


frontend_rule = aws.lb.ListenerRule(ALB_FRONTEND_LISTENER_RULE,
                                    listener_arn=wl.arn,
                                    actions=[aws.lb.ListenerRuleActionArgs(
                                        type="forward",
                                        target_group_arn=front_atg.arn,
                                    )],
                                    conditions=[
                                        aws.lb.ListenerRuleConditionArgs(
                                            path_pattern=aws.lb.ListenerRuleConditionPathPatternArgs(
                                                values=["/*"],
                                            ),
                                        ),
                                    ],
                                    priority=2
                                    )
