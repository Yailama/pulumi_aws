### Description

This is infrastructure as code (IaC) project that implements basic infrastructure on AWS that serves front-end and back-end, s3 bucket, SES and RDS. 
Project uses pulumi (python) and comes with the built-in fastapi and react applications for testing purposes.


### Requirements:
 - [python 3.11+](https://www.python.org/downloads/)
 - [node 16+](https://nodejs.org/en/download/package-manager)
 - [poetry](https://python-poetry.org/docs/)
 - [docker](https://www.docker.com/get-started/)

 To install  `pulumi` and all other dependencies, run 

```[bash]
poetry install
```
Make sure you created `AWS user` that `pulumi` can use to manage resources. More details [here](https://www.pulumi.com/docs/clouds/aws/get-started/begin/).

#### Main commands: 
 - `pulumi up` - to create and update resources
 - `pulumi refresh` - if some changes were done manually and you want to synchonise state. this command does no create/delete any resources
 - `pulumi destroy` - to destroy all resources. Notes:
    - when `auto scaling group` is on, no delition of instance will occur, since they will be instantly recreating to reach desired amount. Change desired amount to 0 before deletion
    - S3 bucket is not deleted if there is at least 1 item
    - ECR (Elastic Container Registry) is not deleted if there is at least 1 image




### General Implementation:
 - prior launching, consider to create [key_pair](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html) for `EC2` instances to enable connectino with `SSH`
 - `ECS` cluster with `EC2` launch type (`Fargate` is easier, but requires additional costs)
 - instance type `t3a.small`. `ENI` needed is 4, since there are 2 tasks (front-end and back-end containers). One `ENI` is used on EC2 itself. Additionaly, `lambda functions` may also need `ENI`  **_Consider to_**:
    - deploy containers to two different instances and decrease instance type. Note: `t2.micro` will be still unavailable because of memory limits for task update
    - OR implement trunking for ecs cluster in pulumi template
    - OR optimize ENI amount needed
 - load balancer serves all traffic to `/api*` to back-end container. **_Consider to_**: 
    - buy a domain `<SOME-DOMAIN>` (for example, via Route53)
    - change load balancer rule to forward not to `/api*` subroute but to `api.<SOME-DOMAIN>` subdomain
    - remove `/api` from back-end routing 
    - update health-check path for backend load balancer target group
 - images `tag` is computed based on datetime, so each deployment triggers rebuilding. **_Consider to_**:
    -   refer to commit hash from the VCS of your actual containers
 - `lambda function` input also relates on `tag` so that it is triggered each time `pulumi up` is running. See more information [here](#aws-lambda) **_Consider to_**:
  - change input to commit hash or other meaningful value



### Main Services:
 #### SES: Send email from/to verified address

Notes
 - email address should be verified (you should receive cofirmation link on address specified in pulumi)
 - check "spam" folder as well
 - service is done for single verified address. **_Consider to_**: 
   - verify entire domain



 
 #### RDS: Create and views items created in database
 Default db is postgresql

 #### S3: Load and view items in S3 bucket

Notes:

 - by default, only 1 bucket is created
 - bucket cannot be deleted while at least 1 item is there


### Additional Services:

 #### AWS Lambda
 `Lambda function` is used to reset cache in `CloudFront` each time front-end is deployed to ensure new code is available for all users.