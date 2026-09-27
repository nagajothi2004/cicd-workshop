from dataclasses import dataclass

from constructs import Construct
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
)


@dataclass(frozen=True)
class EnvironmentConfig:
    """Everything that differs between environment tiers."""

    cpu: int
    memory_limit_mib: int
    desired_count: int
    nat_gateways: int
    blue_green_deployments: bool


PRODUCTION = EnvironmentConfig(
    cpu=512,
    memory_limit_mib=1024,
    desired_count=2,
    nat_gateways=2,
    blue_green_deployments=True,
)

DEVELOPMENT = EnvironmentConfig(
    cpu=256,
    memory_limit_mib=512,
    desired_count=1,
    nat_gateways=1,
    blue_green_deployments=False,
)


class InfrastructureStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        ecr_repository,
        environment: EnvironmentConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(
            self,
            "Vpc",
            nat_gateways=environment.nat_gateways,
        )

        ecs_cluster = ecs.Cluster(
            self,
            "EcsCluster",
            vpc=vpc,
        )

        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "FargateService",
            cluster=ecs_cluster,
            cpu=environment.cpu,
            memory_limit_mib=environment.memory_limit_mib,
            desired_count=environment.desired_count,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(ecr_repository),
                container_port=8081,
                container_name="hello-app",
            ),
        )

        service.target_group.configure_health_check(
            healthy_threshold_count=2,
            unhealthy_threshold_count=2,
            timeout=Duration.seconds(10),
            interval=Duration.seconds(11),
        )

        service.target_group.set_attribute(
            "deregistration_delay.timeout_seconds",
            "5",
        )

        self.service = service

        CfnOutput(
            self,
            "TaskDefinitionArn",
            value=self.service.task_definition.task_definition_arn,
        )

        CfnOutput(
            self,
            "TaskDefinitionFamily",
            value=self.service.task_definition.family,
        )

        CfnOutput(
            self,
            "ExecutionRoleArn",
            value=self.service.task_definition.execution_role.role_arn,
        )

    @property
    def ecs_service_data(self):
        return self.service