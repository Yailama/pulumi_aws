import pulumi_aws as aws
import pulumi
import vpc
stack_config = pulumi.Config("cfg")

LOG_GROUP_NAME = stack_config.require("log_group_name")


# Create a CloudWatch log group
log_group = aws.cloudwatch.LogGroup(LOG_GROUP_NAME)

