from aws_cdk import (
    aws_ec2 as ec2,
    Tags
)
from constructs import Construct
from .ec2_iam_role import EC2IAMRole
from utils.ami_lookup import get_best_ami
class LaunchTemplate(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        stack_info, # This dictionary is defined on the main stack, and must be managed there
        vpc,
        asg_name,
        sqs_url,
        **kwargs):
        super().__init__(scope, id)

        # ============================= Launch Template  =============================

        # Create the security group for the ec2 instance created by the ASG for ingress 3389 tcp and udp
        # ports 80 and 443 are created by default
        security_group = ec2.SecurityGroup(
            self,
            f"{stack_info['role']}-asg-sg",
            vpc=vpc,
            allow_all_outbound=True,
            description=f"The security group used by {stack_info['role']} ec2 instances",
            security_group_name=f"{stack_info['role']}-asg-sg",
        )

        vpc_cidr_block = vpc.vpc_cidr_block
        # RDP can operate on TCP and UDP
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(3389),
            description="allow RDP (TCP 3389) traffic from anywhere",
        )
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.udp(3389),
            description="allow RDP (UDP 3389) traffic from anywhere",
        )

        # ICMP protocol
        security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc_cidr_block),
            connection=ec2.Port.all_icmp(),
            description="allow ICMP from the within the VPC",
        )

        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.all_traffic(),
            description="Allow all ingress",
        )

        # List all TCP ports
        all_tcp_ports = [
            443, # HTTPS
            135, 445, # RPC
            5985, 5986, # WINRM
            123, # NTP
            139, # Netbios
            53, # DNS
            88, 389, 636, # Microsoft required
            5504, # RDWeb - EventID 11 Error code: 2147944122
            3391, # RDP/UDP
        ]
        for port in all_tcp_ports:
            security_group.add_ingress_rule(
                peer=ec2.Peer.ipv4(vpc_cidr_block),
                connection=ec2.Port.tcp(port),
                description=f"allow TCP {port} traffic from within the VPC",
            )

        # List all UDP ports
        all_udp_ports = [
            53, # DNS
            88, 389, 636, # Microsoft required,
            3391, # RDP/UDP
        ]
        for port in all_udp_ports:
            security_group.add_ingress_rule(
                peer=ec2.Peer.ipv4(vpc_cidr_block),
                connection=ec2.Port.udp(port),
                description=f"allow UDP {port} traffic from within the VPC",
            )

        # RPC Range
        security_group.add_ingress_rule(
                peer=ec2.Peer.ipv4(vpc_cidr_block),
                connection=ec2.Port.tcp_range(start_port=49150, end_port=65535),
                description=f"allow TCP range 49150-65535 traffic from within the VPC",
            )

        # Tag the security group with the stack qualifier, and the role name as a Name tag
        Tags.of(security_group).add(
            key="Name",
            value= stack_info["qualifier"] + "-" + stack_info["role"] + "-asg",
            apply_to_launched_instances=True,
        )

        # Create EC2 IAM Role Object
        ec2_iam = EC2IAMRole(
            self,
            f"{stack_info['role']}-ec2-iam",
            stack_info=stack_info
        )

        # Create a launch template to define SSH key, AMI, security group, userdata, and other instance configuration
        # Again as above, the machine image defined in the template below, may not nessecarily be the AMI in the launch template

        # All userdata config must be defined on the PowerShell file, here only the reference to config variables
        # Read and prepare the userdata for use in the Launch Template
        userdata_file = open("rdcb_stack/userdata.ps1", "r")
        userdata = userdata_file.read()
        userdata_file.close()
        # Replace some environment specific values in the script
        userdata = userdata.replace("^^[dc_join_doc]^^", stack_info["dc_join_doc"],)
        userdata = userdata.replace("^^[domain_name]^^", stack_info["fqdn"],)
        userdata = userdata.replace("^^[ad_user_secret]^^", stack_info["ad_user_secret"],)
        userdata = userdata.replace("^^[cb_db]^^", stack_info["cb_db"],)
        userdata = userdata.replace("^^[rds_identifier]^^", stack_info["rds_identifier"],)
        userdata = userdata.replace("^^[connection_string]^^", stack_info["connection_string"],)
        userdata = userdata.replace("^^[install_artifacts_bucket]^^", stack_info["af_bucket"],)
        userdata = userdata.replace("^^[role]^^", stack_info["role"],)
        userdata = userdata.replace("^^[asg_name]^^", asg_name,)
        userdata = userdata.replace("^^[sqs_url]^^", sqs_url,)

        # Parse the userdata into a CDK UserData object
        userdata = ec2.UserData.custom(userdata)

        self.lt = ec2.LaunchTemplate(
            self,
            f"{stack_info['role']}-launchtemplate",
            detailed_monitoring=True,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.COMPUTE5, ec2.InstanceSize.LARGE
            ),
            key_name=stack_info["key_name"],
            launch_template_name=f"{stack_info['role']}-launchtemplate",
            machine_image=get_best_ami(self),
            role=ec2_iam.role,
            security_group=security_group,
            user_data=userdata
        )
