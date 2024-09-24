import json
import pulumi
import pulumi_aws as aws

import vpc
import iam

stack_config = pulumi.Config("cfg")

S3_VPC_ENDPOINT = stack_config.require("s3_vpc_endpoint")
BUCKET_NAME = stack_config.require("bucket_name")


bucket = aws.s3.Bucket(BUCKET_NAME)

s3_vpc_endpoint = aws.ec2.VpcEndpoint(S3_VPC_ENDPOINT,
                                      vpc_id=vpc.default_vpc.id,
                                      service_name="com.amazonaws.us-east-1.s3",
                                      route_table_ids=[vpc.default_route_table.id]
                                      )


bucket_policy = aws.s3.BucketPolicy(f'{BUCKET_NAME}-policy',
                                    bucket=bucket.id,
                                    policy=pulumi.Output.all(bucket.arn, iam.ecs_instance_role.arn, vpc.default_vpc.id).apply(
                                        lambda args: json.dumps({
                                            "Version": "2012-10-17",
                                            "Statement": [
                                                {
                                                    "Effect": "Allow",
                                                    "Principal": {
                                                        "AWS": args[1]
                                                    },
                                                    "Action": "s3:*",
                                                    "Resource": [f"{args[0]}/*", args[0]],
                                                    "Condition": {
                                                        "StringEquals": {
                                                            "aws:sourceVpce": args[2]
                                                        }
                                                    }
                                                }
                                            ]
                                        })
                                    )
                                    )
