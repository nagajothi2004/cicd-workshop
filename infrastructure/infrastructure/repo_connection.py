from constructs import Construct
from aws_cdk import (
    CfnOutput,
    aws_codeconnections as codeconnections,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
)

REPOSITORY_NAME = "cicd-workshop"


class RepoConnection:

    def __init__(self, scope: Construct) -> None:
        self.scope = scope
        self.connection = codeconnections.CfnConnection(
            scope,
            "CICD_Workshop",
            connection_name="CICD_Workshop_Connection",
            provider_type="GitHub",
        )

        CfnOutput(
            scope, "SourceConnectionArn", value=self.connection.attr_connection_arn
        )

        CfnOutput(
            scope,
            "SourceConnectionStatus",
            value=self.connection.attr_connection_status,
        )

    def source_action(
        self, output: codepipeline.Artifact
    ) -> codepipeline_actions.CodeStarConnectionsSourceAction:
        owner = self.scope.node.try_get_context("organizationName")
        if not owner:
            raise ValueError(
                "Set organizationName in the context block of cdk.json to your "
                "GitHub organization or user name"
            )

        return codepipeline_actions.CodeStarConnectionsSourceAction(
            action_name="GitHub",
            owner=owner,
            repo=REPOSITORY_NAME,
            output=output,
            branch="main",
            connection_arn=self.connection.attr_connection_arn,
        )