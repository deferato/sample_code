from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_secretsmanager as asm,
    SecretValue,
    RemovalPolicy,
    Duration
)
from constructs import Construct
import json

class RDSSQLServer(Construct):

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        stack_info, # This dictionary is defined on the main stack, and must be managed from there
        cs_name,
        vpc,
        subnets,
        **kwargs):
        super().__init__(scope, id)

        # ============================= RDS SQL Server =============================
        # RDS SQL Server database to be used in conjunction with the RD Connection Broker
        # For Dev and Test, a single isntance SQL Server Express version will be use
        # For prod a multi-instance with SQL Server Standard edition will be used

        # Create a secret on Secrets Manager to store RDS connection string
        template = {
            'engine': 'sqlserver',
            'port': 1433,
            'username': 'rdcbuser',
            'password': '',
        }

        secret = asm.Secret(
            self,
            f"{stack_info['role']}-rds-secret",
            secret_name=f"{stack_info['role']}-rds-secret",
            description=f"Secret Credentials to access the {stack_info['role']}-rds db",
            generate_secret_string=asm.SecretStringGenerator(
                generate_string_key='password',
                secret_string_template=json.dumps(template),
                exclude_punctuation=True
            )
        )

        security_group = ec2.SecurityGroup(
            self,
            f"{stack_info['role']}-rds-sg",
            vpc=vpc,
            allow_all_outbound=True,
            description=f"The security group used by {stack_info['role']} rds to allow ec2 connections",
            security_group_name=f"{stack_info['role']}-rds-sg",
        )

        # iam role to give access from RDS to the Active Directory
        ad_rds_role = iam.Role(
            self,
            f"{stack_info['role']}-rds-ad-role",
            role_name=f"{stack_info['role']}-rds-ad-role",
            description=f"The role used by {stack_info['role']} to access AD from RDS",
            assumed_by=iam.ServicePrincipal("rds.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonRDSDirectoryServiceAccess")
            ]
        )

        # Define some settings based on the env
        sql_version = rds.SqlServerEngineVersion.VER_15_00_4073_23_V1
        sql_driver = "SQL Server Native Client 11.0"

        rds_settings = {}
        if stack_info["env"] == "prod":
            rds_settings['version'] = rds.DatabaseInstanceEngine.sql_server_se(version=sql_version)
            rds_settings['multi_az'] = True
            rds_settings['license'] = "rds.LicenseModel.LICENSE_INCLUDED"
            rds_settings['instance_type'] = ec2.InstanceType.of(ec2.InstanceClass.STANDARD5, ec2.InstanceSize.LARGE)
            rds_settings['str_listener'] = "listener."
            rds_settings['str_multisubnet'] = "MultiSubnetFailover=True;"

        else: # in case is dev/test
            rds_settings['version'] = rds.DatabaseInstanceEngine.sql_server_ex(version=sql_version)
            rds_settings['multi_az'] = False
            rds_settings['license'] = None
            rds_settings['instance_type'] = ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.SMALL)
            rds_settings['str_listener'] = ""
            rds_settings['str_multisubnet'] = ""

        # Create the Database instance
        self.instance = rds.DatabaseInstance(
            self,
            f"{stack_info['role']}-rds-instance",
            instance_identifier=f"{stack_info['role']}-rds-instance",
            engine=rds_settings['version'],
            multi_az=rds_settings['multi_az'],
            license_model=rds_settings['license'],
            instance_type=rds_settings['instance_type'],
            credentials=rds.Credentials.from_secret(secret),
            port=1433,
            security_groups=[security_group],
            backup_retention=Duration.days(0),
            domain=stack_info['ad_id'],
            domain_role=ad_rds_role,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=subnets
            ),

            removal_policy=RemovalPolicy.DESTROY
        )

        # Creates a connection string with the RDS data and saves it on Secrets Manager
        db_hostname = self.instance.instance_endpoint.hostname
        db_port = self.instance.instance_endpoint.port

        connection_string = f"DRIVER={sql_driver};"
        connection_string += f"SERVER=tcp:{rds_settings['str_listener']}{db_hostname},{db_port};"
        connection_string += f"Database={stack_info['cb_db']};"
        connection_string += f"Trusted_Connection=Yes;APP=RDS Connection Broker;{rds_settings['str_multisubnet']}"

        new_secret = f"{{\"hostname\":\"{db_hostname}\","
        new_secret += f"\"port\": \"{db_port}\","
        new_secret += f"\"username\": \"{secret.secret_value_from_json('username').unsafe_unwrap()}\","
        new_secret += f"\"password\": \"{secret.secret_value_from_json('password').unsafe_unwrap()}\","
        new_secret += f"\"connection_string\": \"{connection_string}\"}}"

        asm.Secret(
            self,
            f"{stack_info['role']}-rds-connection-string",
            secret_name=cs_name,
            description=f"Connection String for the {stack_info['role']} to accesss {stack_info['role']}-rds db",
            secret_string_value=SecretValue.unsafe_plain_text(new_secret)
        )
