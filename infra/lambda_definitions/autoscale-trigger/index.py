import boto3
import os
def lambda_handler(event, context):
    asg_client = boto3.client('autoscaling')
    asg_name = os.environ['ASG_NAME']

    # Fetch the current ASG configuration
    response = asg_client.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
    asg = response['AutoScalingGroups'][0]
    current_capacity = asg['DesiredCapacity']
    max_capacity = asg['MaxSize']

    # Increment the desired capacity
    if current_capacity < max_capacity:
        desired_capacity = current_capacity + 1
        asg_client.set_desired_capacity(
            AutoScalingGroupName=asg_name,
            DesiredCapacity=desired_capacity,
            HonorCooldown=True
        )
