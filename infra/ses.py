import pulumi
import pulumi_aws as aws
import vpc

stack_config = pulumi.Config("cfg")


REGION = stack_config.get("region", "us-east-1")

SES_VPC_ENDPOINT = stack_config.require("ses_vpc_endpoint")
EMAIL_IDENTITY = stack_config.require("email_identity")
EMAIL = stack_config.require("email")
VPC_ENDPOINT_SECURITY_GROUP_NAME = stack_config.require("vpc_endpoint_security_group_name")

ses_vpc_endpoint_sg = aws.ec2.SecurityGroup(VPC_ENDPOINT_SECURITY_GROUP_NAME,
                                            description='SES VPC Endpoint Security Group',
                                            vpc_id=vpc.default_vpc.id,  # replace 'YOUR_VPC_ID' with your actual VPC ID
                                            ingress=[
                                                {
                                                    'from_port': 587,  # SES SMTP with TLS
                                                    'to_port': 587,
                                                    'protocol': 'tcp',
                                                    'cidr_blocks': ['0.0.0.0/0'],
                                                },
                                            ],
                                            egress=[
                                                {
                                                    'from_port': 0,
                                                    'to_port': 0,
                                                    'protocol': '-1',  # allow all
                                                    'cidr_blocks': ['0.0.0.0/0'],
                                                },
                                            ],
                                            )

## SES ##
# Then use this default_route_table.id when creating the VPC Endpoint
# Create the VPC Endpoint for SES.
ses_vpc_endpoint = aws.ec2.VpcEndpoint(SES_VPC_ENDPOINT,
                                       vpc_id=vpc.default_vpc.id,
                                       service_name=f"com.amazonaws.{REGION}.email-smtp",
                                       vpc_endpoint_type="Interface",
                                       subnet_ids=vpc.region_subnet.ids,
                                       private_dns_enabled=True,
                                       security_group_ids=[ses_vpc_endpoint_sg.id]
                                       )

# Verify a specific email address
email_identity = aws.ses.EmailIdentity(EMAIL_IDENTITY, email=EMAIL)



