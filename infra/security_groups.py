import pulumi_aws as aws
import pulumi
import ses
import vpc

stack_config = pulumi.Config("cfg")

LOAD_BALANCER_SG_NAME = stack_config.require("load_balancer_sg_name")
CONTAINER_SECURITY_GROUP_NAME = stack_config.require("container_security_group_name")
RDS_SECURITY_GROUP = stack_config.require("rds_security_group")


lb_sg = aws.ec2.SecurityGroup(LOAD_BALANCER_SG_NAME,
                              name=LOAD_BALANCER_SG_NAME,
                              vpc_id=vpc.default_vpc.id,
                              ingress=[
                                  {
                                      'protocol': 'tcp',
                                      'from_port': 80,
                                      'to_port': 80,
                                      'cidr_blocks': ['0.0.0.0/0'],
                                  }
                              ],
                              egress=[
                                  {
                                      'protocol': 'tcp',
                                      'from_port': 80,
                                      'to_port': 80,
                                      'cidr_blocks': ['0.0.0.0/0'],
                                  }
                              ])

sg = aws.ec2.SecurityGroup(
    CONTAINER_SECURITY_GROUP_NAME,
    description="Allow HTTP",
    vpc_id=vpc.default_vpc.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(protocol="tcp", from_port=80, to_port=80, cidr_blocks=["0.0.0.0/0"],
                                         security_groups=[lb_sg.id, ses.ses_vpc_endpoint_sg])
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(protocol=-1, from_port=0, to_port=0, cidr_blocks=["0.0.0.0/0"])
    ]
)

db_sg = aws.ec2.SecurityGroup(
    RDS_SECURITY_GROUP,
    description="Allow traffic to RDS",
    vpc_id=vpc.default_vpc.id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=5432,
            to_port=5432,
            security_groups=[sg.id]
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(protocol=-1, from_port=0, to_port=0, cidr_blocks=["0.0.0.0/0"])
    ]
)

