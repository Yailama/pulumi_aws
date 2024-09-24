import json
import pulumi
import pulumi_aws as aws

import security_groups

stack_config = pulumi.Config("cfg")

RDS_INSTANCE = stack_config.require("rds_instance")
DB_NAME = stack_config.require("db_name")
DB_USER = stack_config.require("db_user")

def get_db_secrets(db_instance: aws.rds.Instance):
    def get_secret_from_arn(arn: str):
        secret_string = aws.secretsmanager.get_secret_version(secret_id=arn).secret_string
        return json.loads(secret_string)["password"]

    secret_arn = db_instance.master_user_secrets[0]["secret_arn"]
    secret_password = secret_arn.apply(get_secret_from_arn)

    return secret_password


db_instance = aws.rds.Instance(RDS_INSTANCE,
                               allocated_storage=10,
                               db_name=DB_NAME,
                               engine="postgres",
                               instance_class="db.t3.micro",
                               manage_master_user_password=True,
                               skip_final_snapshot=True,
                               vpc_security_group_ids=[security_groups.db_sg.id],
                               username=DB_USER)
