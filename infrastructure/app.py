#!/usr/bin/env python3
import aws_cdk as cdk

from infrastructure.infrastructure_stack import InfrastructureStack
from infrastructure.pipeline_stack import PipelineStack

app = cdk.App()

InfrastructureStack(
    app,
    "InfrastructureStack",
)

pipeline_stack = PipelineStack(
    app,
    "PipelineStack",
)

app.synth()