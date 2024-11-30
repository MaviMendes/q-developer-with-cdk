import aws_cdk as cdk
from aws_cdk import (
    Stack,
    SecretValue,
    aws_s3 as s3,
    aws_codebuild as codebuild,
    pipelines
)
from constructs import Construct
from sb_gen_ai.sb_gen_ai_stack import SbGenAiStack

class PipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create an S3 bucket to store synth output and code difference
        artifact_bucket = s3.Bucket(
            self, "ArtifactBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=cdk.RemovalPolicy.RETAIN
        )

        # Define the source of your repository
        source = pipelines.CodePipelineSource.git_hub(
            "MaviMendes/q-developer-with-cdk", 
            "main",
            authentication=SecretValue.secrets_manager("github-token"),
        )

        # Create a custom synth step that uses the buildspec file
        synth = pipelines.CodeBuildStep(
            "Synth",
            input=source,
            env={
                "ARTIFACT_BUCKET": artifact_bucket.bucket_name
            },
            build_environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0,
                privileged=True
            ),
            partial_build_spec=codebuild.BuildSpec.from_source_filename('buildspec.yml'),
            commands=[]  # Commands are now in buildspec.yml
        )

        # Define the pipeline
        pipeline = pipelines.CodePipeline(
            self, "Pipeline",
            synth=synth,
            pipeline_name=f"{id}-pipeline",
            cross_account_keys=False
        )

        # Add stages to the pipeline
        deploy_stage = pipeline.add_stage(DeployStage(self, "Deploy"))

        # Optionally, add manual approval before deployment
        deploy_stage.add_pre(pipelines.ManualApprovalStep("ApproveDeployment"))

        # Grant S3 permissions to the pipeline's role
        artifact_bucket.grant_read_write(pipeline.synth_step.project)


class DeployStage(cdk.Stage):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        SbGenAiStack(self, "SbGenAiStack")
