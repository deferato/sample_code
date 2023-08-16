from aws_cdk import (
    aws_ec2 as ec2,
    aws_autoscaling as autoscaling,
    aws_sqs as sqs,
    aws_autoscaling_hooktargets as asg_hook,
    Duration,
    Tags
)
from constructs import Construct
from .launch_template import LaunchTemplate

class AutoScalingGroup(Construct):

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        stack_info, # This dictionary is defined on the main stack, and must be managed from there
        vpc,
        subnets,
        **kwargs):
        super().__init__(scope, id)

        # ============================= Autoscaling Group (ASG) =============================
        # An AWS Autoscaling Group automatically adjusts the number of ec2 instances in a group based on the current demand,
        # by creating images based on an AMI, and triggering other startup processes using the userdata (script run on start-up),
        # and SNS notifications.
        # It helps ensure that the desired number of instances are available to handle the workload,
        # and can scale both up and down dynamically. An Autoscaling Group requires launch templates to define the instance configurations,
        # scaling policies to specify the scaling behavior, and an associated load balancer or target group to distribute traffic among the instances.

        # Create a SNS for ASG to notify when an instance is terminated
        # SNS will then put a message on a SQS queue, that a PS function
        # on a running instance will consume and do the after terminated instance
        sqs_queue = sqs.Queue(
            self,
            f"{stack_info['role']}-asg-queue",
            queue_name=f"{stack_info['role']}-asg-queue",
        )

        asg_name = f"{stack_info['role']}-asg"

        # Create the Launch Template object
        asg_lt = LaunchTemplate(
            self,
            f"{stack_info['role']}-lt",
            stack_info=stack_info,
            vpc=vpc,
            asg_name=asg_name,
            sqs_url=sqs_queue.queue_url
        )

        # Create the autoscaling group
        self.asg = autoscaling.AutoScalingGroup(
            self,
            f"{stack_info['role']}-asg",
            vpc=vpc,
            min_capacity=0,
            desired_capacity=3,
            max_capacity=3,
            vpc_subnets=ec2.SubnetSelection(
                subnets=subnets
            ),  # autoscaling group should create instances on the 'private' subnets
            auto_scaling_group_name=asg_name,
            launch_template=asg_lt.lt,
        )

        self.asg.add_lifecycle_hook(
            f"{stack_info['role']}-launch-hook",
            lifecycle_transition=autoscaling.LifecycleTransition.INSTANCE_LAUNCHING,
            default_result=autoscaling.DefaultResult.ABANDON,
            heartbeat_timeout=Duration.minutes(30),
            lifecycle_hook_name=f"{stack_info['role']}-launch-hook",
            notification_metadata=None,
            notification_target=None,
            role=None
        )

        self.asg.add_lifecycle_hook(
            f"{stack_info['role']}-terminate-hook",
            lifecycle_hook_name=f"{stack_info['role']}-terminate-hook",
            lifecycle_transition=autoscaling.LifecycleTransition.INSTANCE_TERMINATING,
            default_result=autoscaling.DefaultResult.ABANDON,
            notification_target=asg_hook.QueueHook(sqs_queue),
            heartbeat_timeout=Duration.seconds(60)
        )

        # Tag the autoscaling group with the stack qualifier, and the role name as a Name tag (rather than having a randomly created CDK name)
        Tags.of(self.asg).add(
            key="Name",
            value= stack_info["qualifier"] + "-" + stack_info["role"],
            apply_to_launched_instances=True,  # Tag any ec2 instances launched by this ASG with this tag, so their ASG membership is more apparent
        )

