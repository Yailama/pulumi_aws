import json
from datetime import datetime
from uuid import uuid4

import pulumi
import pulumi_aws as aws

import load_balancer
import iam
import ecs_cluster

stack_config = pulumi.Config("cfg")

tag = datetime.now().strftime('%Y%m-%d%H-%M%S-') + str(uuid4())


CLOUDFRONT_DISTRIBUTION = stack_config.require("cloudfront_distribution")
LAMBDA_FUNCTION_NAME = stack_config.require("lambda_function_name")
LAMBDA_INVOCATION = stack_config.require("lambda_invocation")

cloudfront_distribution = aws.cloudfront.Distribution(CLOUDFRONT_DISTRIBUTION,
                                                      enabled=True,
                                                      default_cache_behavior={
                                                          "allowedMethods": ["GET", "HEAD", "OPTIONS", "PUT", "POST",
                                                                             "PATCH", "DELETE"],
                                                          "cachedMethods": ["GET", "HEAD", "OPTIONS"],
                                                          "targetOriginId": "myALBOrigin",
                                                          "forwardedValues": {
                                                              "queryString": True,
                                                              "headers": ["*"],
                                                              "cookies": {
                                                                  "forward": "all",
                                                              },
                                                          },
                                                          "viewerProtocolPolicy": "redirect-to-https",
                                                          "minTtl": 0,
                                                          "defaultTtl": 3600,
                                                          "maxTtl": 86400,
                                                      },
                                                      origins=[{
                                                          "domainName": load_balancer.load_balancer.dns_name,
                                                          "originId": "myALBOrigin",
                                                          "customOriginConfig": {
                                                              "httpPort": 80,
                                                              "httpsPort": 443,
                                                              "originProtocolPolicy": "http-only",
                                                              "originSslProtocols": ["TLSv1", "TLSv1.1", "TLSv1.2"],
                                                          },
                                                      }],
                                                      restrictions={
                                                          "geoRestriction": {
                                                              "restrictionType": "none",
                                                          },
                                                      },
                                                      viewer_certificate={
                                                          "cloudfrontDefaultCertificate": True,
                                                      }
                                                      )



lambda_function = aws.lambda_.Function(LAMBDA_FUNCTION_NAME,
                                       role=iam.lambda_role.arn,
                                       handler="index.handler",
                                       runtime="python3.8",
                                       code=pulumi.AssetArchive({
                                           ".": pulumi.FileArchive("lambda_definitions/cache-reset")
                                       }),
                                       environment={
                                           "variables": {
                                               "CLOUDFRONT_DISTRIBUTION_ID": cloudfront_distribution.id,
                                           }
                                       },
                                       opts=pulumi.ResourceOptions(depends_on=[ecs_cluster.frontservice]),
                                       )

pulumi.Output.all(lambda_function.name, tag).apply(
    lambda args: aws.lambda_.Invocation(LAMBDA_INVOCATION,
                                        function_name=args[0],
                                        input=json.dumps({"task-runner-tag": tag})
                                        )
)
