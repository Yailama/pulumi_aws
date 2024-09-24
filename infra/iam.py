import json
import pulumi
import pulumi_aws as aws


stack_config = pulumi.Config("cfg")

SES_POLICY = stack_config.require("ses_policy")
SES_ACCESS_POLICY_ATTACH = stack_config.require("ses_access_policy_attach")
SES_IAM = stack_config.require("ses_iam")
TASK_EXECUTION_ROLE_NAME = stack_config.require("task_execution_role_name")
ECS_INSTANCE_ROLE = stack_config.require("ecs_instance_role")
ECS_INSTANCE_ROLE_POLICY_ATTACH = stack_config.require("ecs_instance_role_policy_attach")
LAMBDA_IAM_ROLE = stack_config.require("lambda_iam_role")
LAMBDA_IAM_ROLE_POLICY_ATTACH = stack_config.require("lambda_iam_role_policy_attach")
CLOUDFRONT_ROLE_POLICY_ATTACH = stack_config.require("cloudfront_role_policy_attach")
TASK_EXECUTION_POLICY_ATTACH = stack_config.require("task_execution_policy_attach")
S3_ACCESS_POLICY_ATTACH = stack_config.require("s3_access_policy_attach")
ECR_ACCESS_POLICY_NAME = stack_config.require("ecr_access_policy_name")
ECS_LOGGING_POLICY = stack_config.require("ecs_logging_policy")
CLOUDFRONT_INVALIDATION_POLICY = stack_config.require("cloudfront_invalidation_policy")
ECS_IAM_PROFILE = stack_config.require("ecs_iam_profile")
EMAIL = stack_config.require("email")
LOG_GROUP_NAME = stack_config.require("log_group_name")


resource_prefix = SES_IAM

email_user = aws.iam.User(
    f"{resource_prefix}-ses-user",
    name=f"{resource_prefix}-ses-user-name",
    path="/system/",
    tags={"Purpose": "SES Sending via SMTP"}
)

email_user_policy = aws.iam.UserPolicy(
    f"{resource_prefix}-ses-policy",
    user=email_user.name,
    policy=pulumi.Output.all(EMAIL).apply(
        lambda args: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Action": [
                    "ses:SendEmail",
                    "ses:SendTemplatedEmail",
                    "ses:SendRawEmail",
                    "ses:SendBulkTemplatedEmail"
                ],
                "Effect": "Allow",
                "Resource": "*",
                "Condition": {
                    "StringLike": {
                        "ses:FromAddress": args[0]
                    }
                }
            }]
        }, indent=4)
    )
)

# IAM role and profile for:
# - Instance IAM profile: to allow the EC2 instances permission to join the ECS cluster.
#   Used in the Launch Configuration declaration below.
ecs_instance_role = aws.iam.Role(
    ECS_INSTANCE_ROLE,
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement":
                [
                    {
                        "Sid": "",
                        "Effect": "Allow",
                        "Principal": {"Service": "ec2.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ],
        }
    ),
)

# Generate the SMTP credentials for the IAM user
email_access_key = aws.iam.AccessKey(
    f"{resource_prefix}-ses-access-key",
    user=email_user.name,
)


ses_policy = aws.iam.Policy(
    SES_POLICY,
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": "ses:SendEmail",
            "Resource": "*"
        }]
    })
)

# IAM role for:
# - Task Role: to allow the TaskDefinition to launch tasks on the cluster.
#   Used in the TaskDefinition declaration below.
task_execution_role = aws.iam.Role(
    TASK_EXECUTION_ROLE_NAME,
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement":
                [
                    {
                        "Sid": "",
                        "Effect": "Allow",
                        "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ],
        }
    ),
)


#
ses_policy_attachment = aws.iam.RolePolicyAttachment(
    SES_ACCESS_POLICY_ATTACH,
    role=ecs_instance_role.name,
    policy_arn=ses_policy.arn
)


# Attach a policy to the role for CloudWatch Logs permissions
log_policy = aws.iam.RolePolicy(ECS_LOGGING_POLICY,
                                role=task_execution_role.id,
                                policy=pulumi.Output.all(LOG_GROUP_NAME).apply(lambda args:
                                                                               {
                                                                                   "Version": "2012-10-17",
                                                                                   "Statement": [{
                                                                                       "Action": [
                                                                                           "logs:CreateLogStream",
                                                                                           "logs:PutLogEvents"
                                                                                       ],
                                                                                       "Resource": f"arn:aws:logs:*:*:log-group:{args[0]}:*",
                                                                                       "Effect": "Allow"
                                                                                   }]
                                                                               }
                                                                               ))


ecr_policy = aws.iam.Policy(
    ECR_ACCESS_POLICY_NAME,
    description="Grant ECR access",
    policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:BatchGetImage",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetAuthorizationToken"
                    ],
                    "Resource": "*"
                }
            ]
        }
    )
)

role_policy_attachment = aws.iam.RolePolicyAttachment(
    "role-policy-attachment",
    role=task_execution_role.name,
    policy_arn=ecr_policy.arn
)

task_execution_role_policy_attach = aws.iam.RolePolicyAttachment(
    TASK_EXECUTION_POLICY_ATTACH,
    role=task_execution_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
)


ecs_instance_role_policy_attach = aws.iam.RolePolicyAttachment(
    ECS_INSTANCE_ROLE_POLICY_ATTACH,
    role=ecs_instance_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
)

# Attach the S3 full access policy to the same role
s3_full_access_policy_attachment = aws.iam.RolePolicyAttachment(
    S3_ACCESS_POLICY_ATTACH,
    role=ecs_instance_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonS3FullAccess"
)


ecs_instance_profile = aws.iam.InstanceProfile(ECS_IAM_PROFILE, role=ecs_instance_role.name)


# Create an IAM role for the Lambda function
lambda_role = aws.iam.Role(LAMBDA_IAM_ROLE,
                           assume_role_policy=pulumi.Output.from_input({
                               "Version": "2012-10-17",
                               "Statement": [{
                                   "Action": "sts:AssumeRole",
                                   "Principal": {
                                       "Service": "lambda.amazonaws.com"
                                   },
                                   "Effect": "Allow",
                                   "Sid": "",
                               }],
                           }),
                           )

# Attach the necessary policies to the Lambda role
cloudfront_invalidation_policy = aws.iam.Policy(CLOUDFRONT_INVALIDATION_POLICY,
                                                description="Allows Lambda function to create CloudFront invalidations.",
                                                policy=pulumi.Output.from_input({
                                                    "Version": "2012-10-17",
                                                    "Statement": [{
                                                        "Effect": "Allow",
                                                        "Action": "cloudfront:CreateInvalidation",
                                                        # You may want to narrow down this resource ARN to just your distribution
                                                        "Resource": "*"
                                                    }]
                                                })
                                                )

# This includes permissions to run Lambda and perform CloudFront invalidations
aws.iam.RolePolicyAttachment(LAMBDA_IAM_ROLE_POLICY_ATTACH,
                             policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
                             role=lambda_role.name
                             )

aws.iam.RolePolicyAttachment(CLOUDFRONT_ROLE_POLICY_ATTACH,
                             policy_arn=cloudfront_invalidation_policy.arn,
                             role=lambda_role.name
                             )
