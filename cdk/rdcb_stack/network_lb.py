from aws_cdk import (
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2
)
from constructs import Construct
from .auto_scaling_group import AutoScalingGroup

class NetworkLB(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        stack_info, # This dictionary is defined on the main stack, and must be managed there
        vpc,
        subnets,
        asg=AutoScalingGroup,
        **kwargs):
        super().__init__(scope, id)

        # ============================= Network Load Balancer (NLB) =============================
        # An AWS Network Load Balancer distributes incoming network traffic across multiple targets (such as Amazon EC2 instances) within a network,
        # and operates at the transport layer (Layer 4) of the OSI model, distributing traffic based on IP addresses and ports.

        # Create the layer 4 (TCP,UDP) Network Load Balancer
        self.nlb = elbv2.NetworkLoadBalancer(
            self,
            f"{stack_info['role']}-nlb",
            internet_facing=False,  # internal
            cross_zone_enabled=True,  # balance connections cross azs
            load_balancer_name=f"{stack_info['role']}-nlb",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=subnets)
        )

        # Create a target group to direct all TCP/UDP traffic on 3389 to the RDCB Autoscaling Group
        nlb_rdp_target_group = elbv2.NetworkTargetGroup(
            self,
            f"{stack_info['role']}-nlb-target-group",
            port=3389,
            protocol=elbv2.Protocol.TCP_UDP,
            targets=[asg],
            target_group_name=f"{stack_info['role']}-nlb-target-group",
            vpc=vpc,
        )

        # Add the listener for port 3389 (RDP) TCP & UDP and direct traffic to the target group created above (GW ASG)
        self.nlb.add_listener(
            f"{stack_info['role']}-nlb-rdp-listener",
            port=3389,
            default_target_groups=[nlb_rdp_target_group],
            protocol=elbv2.Protocol.TCP_UDP
        )

        # Add the listener for TCP port 5985 for WS-Management and PowerShell Remoting
        self.nlb.add_listener(
            f"{stack_info['role']}-nlb-wsm-listener",
            port=5985,
            default_target_groups=[nlb_rdp_target_group],
            protocol=elbv2.Protocol.TCP
        )
