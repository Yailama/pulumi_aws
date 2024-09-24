import pulumi_aws as aws

# Get the default VPC.
default_vpc = aws.ec2.get_vpc(default=True)
default_vpc_subnets = aws.ec2.get_subnets(
    filters=[
        aws.ec2.GetSubnetsFilterArgs(
            name='vpc-id',
            values=[default_vpc.id],
        ),
    ],
)

region_subnet = aws.ec2.get_subnets(
    filters=[
        aws.ec2.GetSubnetsFilterArgs(
            name='vpc-id',
            values=[default_vpc.id],
        ),
        aws.ec2.GetSubnetsFilterArgs(
            name='availability-zone',
            values=["us-east-1c"],
        ),

    ],
)

# Fetch the default VPC's main route table ID
default_route_table = aws.ec2.get_route_table(filters=[{
    "name": "vpc-id",
    "values": [default_vpc.id]
}, {
    "name": "association.main",
    "values": ["true"]
}])


# Export resources
__all__ = [default_vpc, default_vpc_subnets, region_subnet]