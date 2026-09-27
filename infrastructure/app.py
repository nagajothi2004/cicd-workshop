#!/usr/bin/env python3
import aws_cdk as cdk

from infrastructure.ecr_stack import EcrStack
from infrastructure.infrastructure_stack import (
    InfrastructureStack,
    DEVELOPMENT,
    PRODUCTION,
)
from infrastructure.pipeline_stack import PipelineStack


app = cdk.App()

ecr_stack = EcrStack(
    app,
    "EcrStack",
)

test_env_stack = InfrastructureStack(
    app,
    "TestEnvStack",
    ecr_repository=ecr_stack.ecr_data,
    environment=DEVELOPMENT,
)

pipeline_stack = PipelineStack(
    app,
    "PipelineStack",
    ecr_repository=ecr_stack.ecr_data,
)

app.synth()