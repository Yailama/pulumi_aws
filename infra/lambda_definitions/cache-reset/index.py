import json
import os
import boto3

def handler(event, context):
    distribution_id = os.environ['CLOUDFRONT_DISTRIBUTION_ID']
    client = boto3.client('cloudfront')
    response = client.create_invalidation(
        DistributionId=distribution_id,
        InvalidationBatch={
            'Paths': {
                'Quantity': 1,
                'Items': ['/*']
            },
            'CallerReference': str(hash(json.dumps(event, sort_keys=True)))  # Use the event's hash as a unique reference
        }
    )
    return {
        "statusCode": 200,
        "body": str(response)
    }
