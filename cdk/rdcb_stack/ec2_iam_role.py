import aws_cdk.aws_iam as iam
from constructs import Construct

class EC2IAMRole(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        stack_info, # This dictionary is defined on the main stack, and must be managed there
        **kwargs):
        super().__init__(scope, id)

        # Create an AMI role so that we can define the permissions on ec2 instance created by the ASG
        self.role = iam.Role(
            self,
            f"{stack_info['role']}-role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description=f"The role used by {stack_info['role']} ec2 instances",
            managed_policies=[
                # Standard AWS managed instance policy for ec2 instances managed by AWS Systems Manager
                iam.ManagedPolicy.from_managed_policy_arn(
                    self,
                    "AmazonSSMManagedInstanceCore",
                    "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
                ),
                # Standard AWS managed instance policy for ec2 instances that need to associate to an AWS Managed Directory
                iam.ManagedPolicy.from_managed_policy_arn(
                    self,
                    "AmazonSSMDirectoryServiceAccess",
                    "arn:aws:iam::aws:policy/AmazonSSMDirectoryServiceAccess",
                ),
            ],
            inline_policies={
                f"{stack_info['role']}-policy": iam.PolicyDocument(
                    statements=[
                        # Allow the instance to execute the 'domain join document'
                        iam.PolicyStatement(
                            actions=["ssm:SendCommand"],
                            resources=[
                                f"arn:aws:ssm:ap-southeast-2:{stack_info['account']}:document/{stack_info['dc_join_doc']}",
                                f"arn:aws:ec2:ap-southeast-2:{stack_info['account']}:instance/*",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                        # Allow the instance to get the status of the 'domain join document execution'
                        iam.PolicyStatement(
                            actions=["ssm:ListCommands"],
                            resources=[
                                f"arn:aws:ssm:ap-southeast-2:{stack_info['account']}:*",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),

                        # Allow the instance to access the install artifacts bucket
                        iam.PolicyStatement(
                            actions=["s3:GetObject","s3:ListBucket"],
                            resources=[
                                f"arn:aws:s3:::{stack_info['af_bucket']}/*",
                                f"arn:aws:s3:::{stack_info['af_bucket']}",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                        # Allow the instance to access the KMS key used to encypt SecureStrings in SSM Parameter Store
                        iam.PolicyStatement(
                            actions=["kms:Decrypt", "kms:CreateGrant", "kms:DescribeKey", "kms:GenerateDataKey"],
                            resources=[
                                f"arn:aws:kms:ap-southeast-2:{stack_info['account']}:key/aws/ssm"
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                        # Allow the instance to access the SecureStrings in SSM Parameter Store for the domain certificate
                        iam.PolicyStatement(
                            actions=["ssm:GetParameters"],
                            resources=[
                                f"arn:aws:ssm:ap-southeast-2:{stack_info['account']}:parameter/etc/certificates/{stack_info['fqdn']}",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                        # Allow the instance to get the Secure String with the AD Credentials
                        iam.PolicyStatement(
                            actions=["secretsmanager:GetSecretValue", "secretsmanager:CreateSecret", "secretsmanager:TagResource", "secretsmanager:RotateSecret"],
                            resources=[
                                f"arn:aws:secretsmanager:ap-southeast-2:{stack_info['account']}:secret:{stack_info['role']}-rds-*",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                        # Allow the instance to get RDS instance status
                        iam.PolicyStatement(
                            actions=["rds:DescribeDBInstances","rds:ModifyDBInstance"],
                            resources=[
                                f"arn:aws:rds:ap-southeast-2:{stack_info['account']}:db:{stack_info['role']}-rds*",
                                f"arn:aws:rds:ap-southeast-2:{stack_info['account']}:og:{stack_info['role']}-rds*",
                                f"arn:aws:rds:ap-southeast-2:{stack_info['account']}:pg:{stack_info['role']}-rds*",
                                f"arn:aws:rds:ap-southeast-2:{stack_info['account']}:secgrp:{stack_info['role']}-rds*",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                        # Allow the instance to tag itself
                        iam.PolicyStatement(
                            actions=["ec2:CreateTags"],
                            resources=[
                                f"arn:aws:ec2:ap-southeast-2:{stack_info['account']}:instance/*",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                        # Allow the instance to change ASG desired size
                        iam.PolicyStatement(
                            actions=["autoscaling:SetDesiredCapacity","autoscaling:CompleteLifecycleAction","autoscaling:RecordLifecycleActionHeartbeat"],
                            resources=[
                                f"arn:aws:autoscaling:ap-southeast-2:{stack_info['account']}:autoScalingGroup:*/{stack_info['role']}-asg",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                        # Allow the instance to Receive SQS Messages
                        iam.PolicyStatement(
                            actions=["sqs:receivemessage","sqs:deletemessage"],
                            resources=[
                                f"arn:aws:sqs:ap-southeast-2:{stack_info['account']}:{stack_info['role']}-*",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                    ]
                ),
            },
            role_name=f"{stack_info['role']}-ec2",
        )
