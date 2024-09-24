import base64
from datetime import datetime
from uuid import uuid4

import pulumi_docker as docker
import pulumi
import pulumi_aws as aws


tag = datetime.now().strftime('%Y%m-%d%H-%M%S-') + str(uuid4())

stack_config = pulumi.Config("cfg")

BACKEND_DOCKER_IMAGE = stack_config.require("backend_docker_image")
FRONTEND_DOCKER_IMAGE = stack_config.require("frontend_docker_image")
ECR_REPO = stack_config.require("ecr_repo")
APP_LIVECYCLE_POLICY = stack_config.require("app_livecycle_policy")

def get_registry_info(rid):
    creds = aws.ecr.get_credentials(registry_id=rid)
    decoded = base64.b64decode(creds.authorization_token).decode()
    parts = decoded.split(':')
    if len(parts) != 2:
        raise Exception("Invalid credentials")
    return docker.RegistryArgs(password=parts[1], server=creds.proxy_endpoint, username=parts[0])




app_ecr_repo = aws.ecr.Repository(ECR_REPO, image_tag_mutability="MUTABLE")

app_lifecycle_policy = aws.ecr.LifecyclePolicy(APP_LIVECYCLE_POLICY,
                                               repository=app_ecr_repo.name,
                                               policy="""{
        "rules": [
            {
                "rulePriority": 10,
                "description": "Remove untagged images",
                "selection": {
                    "tagStatus": "untagged",
                    "countType": "imageCountMoreThan",
                    "countNumber": 1
                },
                "action": {
                    "type": "expire"
                }
            }
        ]
    }""")

app_registry = app_ecr_repo.registry_id.apply(get_registry_info)

fastapi_image = docker.Image(BACKEND_DOCKER_IMAGE,
                             image_name=app_ecr_repo.repository_url.apply(lambda x: f"{x}:fastapi-{tag}"),
                             build=docker.DockerBuildArgs(
                                 context="../",
                                 dockerfile="./app/backend/Dockerfile",
                                 platform="linux/amd64"
                             ),
                             skip_push=False,
                             registry=app_registry
                             )

frontend_image = docker.Image(FRONTEND_DOCKER_IMAGE,
                              image_name=app_ecr_repo.repository_url.apply(lambda x: f"{x}:react-{tag}"),
                              build=docker.DockerBuildArgs(
                                  context="./app/frontend/react-app/",
                                  dockerfile="./app/frontend/react-app/Dockerfile",
                                  platform="linux/amd64"
                              ),
                              skip_push=False,
                              registry=app_registry
                              )
