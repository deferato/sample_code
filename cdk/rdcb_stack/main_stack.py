"""
    DESCRIPTION
        This stack is used to deploy a new Remote Desktop Connection Broker service
        It's used in conjunction with other stacks to deploy
        a full Remote Desktop service infrastrcture
        We use constructs to split the main stack in to different files
        all on the rdcb_stack folder
"""

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_route53 as r53,
    aws_route53_targets as r53_targets,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
)
from constructs import Construct
from .auto_scaling_group import AutoScalingGroup
from .network_lb import NetworkLB
from .rds_sql_server import RDSSQLServer

import config


class EC2RDCBStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define a dictionary of data to be used in other constructs
        env_name = config.vpc[self.account]["env_name"]
        stack_info = {
            "role": "rdcb",
            "fqdn": config.vpc[self.account]["domain_name"],
            "dc_join_doc": config.vpc[self.account]["domain_join_doc"],
            "ad_id": config.vpc[self.account]["active_directory_id"],
            "ad_user_secret": config.vpc[self.account]["ad_user_secret"],
            "key_name": config.vpc[self.account]["ssh_key"],
            "account": self.account,
            "cb_db": "RDS_RDCB",
            "qualifier": config.STACK_QUALIFIER,
            "env": env_name,
            "af_bucket": config.vpc[self.account]["artifacts_bucket_name"],
        }

        # Lookup the VPC defined in the config.py, and put its CDK constructs into a list to reference later for our ec2s
        vpc = ec2.Vpc.from_lookup(
            self, "VPC", vpc_id=config.vpc[self.account]["vpc_id"]
        )

        # Lookup the subnets defined in the config.py, and put their CDK constructs into a list to reference later for our ec2s
        work_load_subnets = [
            ec2.Subnet.from_subnet_id(
                self, subnet["name"], subnet_id=subnet["subnet_id"]
            )
            for subnet in config.vpc[self.account][
                "work_load_subnets"
            ]  # The 'private' subnets that sit behind the 'protected' subnets
        ]

        # Lookup the hosted zone defined in the config.py, and put its CDK construct into a list to reference later for certificate and r53 record
        hosted_zone = r53.HostedZone.from_hosted_zone_attributes(
            self,
            f"{stack_info['role']}-hosted-zone",
            hosted_zone_id=config.vpc[self.account]["hosted_zone_id"],
            zone_name=stack_info["fqdn"].split(".", 1)[1]
        )

        stack_info["connection_string"] = f"{stack_info['role']}-rds-connection-string"
        # Create a RDS SQL Server database for the Connection Broker
        rdsdb = RDSSQLServer(
            self,
            f"{stack_info['role']}-rdsdb",
            stack_info=stack_info,
            cs_name = stack_info["connection_string"],
            vpc=vpc,
            subnets=work_load_subnets
        )

        stack_info["rds_identifier"] = rdsdb.instance.instance_identifier

        # Deploy the userdata scripts to the artifacts bucket
        s3deploy.BucketDeployment(
            self,
            f"{stack_info['role']}-userdata-main",
            sources=[
                s3deploy.Source.asset(f"./{stack_info['role']}_stack/userdatalib")
            ],
            destination_bucket=s3.Bucket.from_bucket_name(
                                                    self,
                                                    f"{stack_info['role']}-artifacts-bucket",
                                                    bucket_name=stack_info['af_bucket'],
            ),
            destination_key_prefix=f"userdata/{stack_info['role']}",
        )

        # Create the ASG object invoking it's construct
        autoscaling_group = AutoScalingGroup(
            self,
            f"{stack_info['role']}-asg",
            stack_info=stack_info,
            vpc=vpc,
            subnets=work_load_subnets,
        )

        # Grant access to port 1433 from the ASG to the RDS
        rdsdb.instance.connections.allow_from(autoscaling_group.asg, ec2.Port.tcp(1433))

        # Create the Network Load Balancer object invoking it's construct
        network_lb = NetworkLB(
            self,
            f"{stack_info['role']}-nlb",
            stack_info=stack_info,
            vpc=vpc,
            subnets=work_load_subnets,
            asg=autoscaling_group.asg
        )

        # Create a DNS record to direct incoming connections for the domain name to the network load balancer
        r53.ARecord(
            self,
            f"{stack_info['role']}-r53-record",
            zone=hosted_zone,
            target=r53.RecordTarget.from_alias(
                alias_target=r53_targets.LoadBalancerTarget(network_lb.nlb)
            ),
            comment="The r53 address to point users to the network loadbalancer for the Connection Broker",
            record_name=f"{stack_info['role']}.{stack_info['fqdn']}"
        )
