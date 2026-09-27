from constructs import Construct
from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codebuild as codebuild,
    aws_codepipeline_actions as codepipeline_actions,
    aws_iam as iam,
)

from infrastructure.repo_connection import RepoConnection


class PipelineStack(Stack):

    def __init__(
        self,
        scope: Construct,
        id: str,
        ecr_repository,
        test_app_fargate,
        prod_app_fargate,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.source = RepoConnection(self)

        # -----------------------------------------
        # Create CodePipeline
        # -----------------------------------------
        pipeline = codepipeline.Pipeline(
            self,
            "Pipeline",
            pipeline_name="CICD_Pipeline",
            cross_account_keys=False,
            pipeline_type=codepipeline.PipelineType.V2,
            execution_mode=codepipeline.ExecutionMode.QUEUED,
        )

        # -----------------------------------------
        # Code Quality / Unit Test
        # -----------------------------------------
        code_quality_build = codebuild.PipelineProject(
            self,
            "CodeQuality",
            build_spec=codebuild.BuildSpec.from_source_filename(
                "buildspec_test.yml"
            ),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxLambdaBuildImage.AMAZON_LINUX_2023_PYTHON_3_12,
                compute_type=codebuild.ComputeType.LAMBDA_10GB,
            ),
        )

        # -----------------------------------------
        # Docker Build and Push to ECR
        # -----------------------------------------
        docker_build = codebuild.PipelineProject(
            self,
            "DockerBuild",
            build_spec=codebuild.BuildSpec.from_source_filename(
                "buildspec_docker.yml"
            ),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                privileged=True,
            ),
            environment_variables={
                "IMAGE_REPO_URI": codebuild.BuildEnvironmentVariable(
                    value=ecr_repository.repository_uri
                ),
                "IMAGE_TAG": codebuild.BuildEnvironmentVariable(
                    value="latest"
                ),
            },
        )

        # -----------------------------------------
        # Allow CodeBuild to push Docker image to ECR
        # -----------------------------------------
        docker_build.role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "ecr:PutImage",
                    "ecr:InitiateLayerUpload",
                    "ecr:UploadLayerPart",
                    "ecr:CompleteLayerUpload",
                ],
                resources=["*"],
            )
        )

        # -----------------------------------------
        # Artifacts
        # -----------------------------------------
        source_output = codepipeline.Artifact()
        unit_test_output = codepipeline.Artifact()
        docker_build_output = codepipeline.Artifact()

        # -----------------------------------------
        # Source Action
        # -----------------------------------------
        source_action = self.source.source_action(source_output)

        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action],
        )

        # -----------------------------------------
        # Code Quality Testing Stage
        # -----------------------------------------
        build_action = codepipeline_actions.CodeBuildAction(
            action_name="Unit-Test",
            project=code_quality_build,
            input=source_output,
            outputs=[unit_test_output],
        )

        pipeline.add_stage(
            stage_name="Code-Quality-Testing",
            actions=[build_action],
        )

        # -----------------------------------------
        # Docker Build & Push Stage
        # -----------------------------------------
        docker_build_action = codepipeline_actions.CodeBuildAction(
            action_name="Docker-Build-Push",
            project=docker_build,
            input=source_output,
            outputs=[docker_build_output],
        )

        pipeline.add_stage(
            stage_name="Docker-Push-ECR",
            actions=[docker_build_action],
        )

        # -----------------------------------------
        # Deploy to Test Environment
        # -----------------------------------------
        pipeline.add_stage(
            stage_name="Deploy-Test",
            actions=[
                codepipeline_actions.EcsDeployAction(
                    action_name="Deploy-Fargate-Test",
                    service=test_app_fargate.service,
                    input=docker_build_output,
                )
            ],
        )

        # -----------------------------------------
        # Deploy to Production Environment
        # -----------------------------------------
        pipeline.add_stage(
            stage_name="Deploy-Production",
            actions=[
                codepipeline_actions.ManualApprovalAction(
                    action_name="Approve-Deploy-Prod",
                    run_order=1,
                ),
                codepipeline_actions.EcsDeployAction(
                    action_name="Deploy-Fargate-Prod",
                    service=prod_app_fargate.service,
                    input=docker_build_output,
                    run_order=2,
                ),
            ],
        )