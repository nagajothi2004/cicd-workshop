from constructs import Construct
from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codebuild as codebuild,
    aws_codepipeline_actions as codepipeline_actions,
)

from infrastructure.repo_connection import RepoConnection


class PipelineStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.source = RepoConnection(self)

        pipeline = codepipeline.Pipeline(
            self,
            "Pipeline",
            pipeline_name="CICD_Pipeline",
            cross_account_keys=False,
            pipeline_type=codepipeline.PipelineType.V2,
            execution_mode=codepipeline.ExecutionMode.QUEUED,
        )

        code_quality_build = codebuild.PipelineProject(
            self,
            "CodeQuality",
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec_test.yml"),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxLambdaBuildImage.AMAZON_LINUX_2023_PYTHON_3_12,
                compute_type=codebuild.ComputeType.LAMBDA_10GB,
            )
        )

        source_output = codepipeline.Artifact()
        unit_test_output = codepipeline.Artifact()

        source_action = self.source.source_action(source_output)

        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

        build_action = codepipeline_actions.CodeBuildAction(
            action_name="Unit-Test",
            project=code_quality_build,
            input=source_output,
            outputs=[unit_test_output],
        )

        pipeline.add_stage(
            stage_name="Code-Quality-Testing",
            actions=[build_action]
        )