from aws_cdk import (
    Stack,
    aws_sqs as sqs,
)
from constructs import Construct

class EC2RDSHSQSStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        sqs_queue = sqs.Queue(
                self,
                "rdsh-asg-queue",
                queue_name="rdsh-asg-queue",
        )

        # We assign the sqs arn to a local variable for the Object.
        self.sqs_arn = sqs_queue.queue_arn

    # Using the property decorator
    @property
    def queue_arn(self):
        return self.sqs_arn
