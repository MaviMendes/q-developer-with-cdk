import aws_cdk as cdk
from aws_cdk import (
    Stack,
    SecretValue,
    aws_s3 as s3,
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

        # Define the pipeline with modified synth step
        pipeline = pipelines.CodePipeline(
            self, "Pipeline",
            synth=pipelines.ShellStep(
                "Synth",
                input=source,
                env={
                    "ARTIFACT_BUCKET": artifact_bucket.bucket_name
                },
                commands=[
                    "npm install -g aws-cdk",
                    "pip install -r requirements.txt",
                    "git diff HEAD^ HEAD > code_diff.txt",
                    "cdk synth PipelineStack > pipeline_stack.yaml",
                    "cdk synth SbGenAiStack > sbgenai_stack.yaml",
                    f"aws s3 cp code_diff.txt s3://{artifact_bucket.bucket_name}/code_diff_$CODEBUILD_BUILD_NUMBER.txt",
                    f"aws s3 cp pipeline_stack.yaml s3://{artifact_bucket.bucket_name}/pipeline_stack_$CODEBUILD_BUILD_NUMBER.yaml",
                    f"aws s3 cp sbgenai_stack.yaml s3://{artifact_bucket.bucket_name}/sbgenai_stack_$CODEBUILD_BUILD_NUMBER.yaml",
                    "cdk synth"  # This final synth is required for the pipeline
                ],
                primary_output_directory="cdk.out"
            )
        )

        # Add stages to the pipeline
        deploy_stage = pipeline.add_stage(DeployStage(self, "Deploy"))

        # Optionally, add manual approval before deployment
        deploy_stage.add_pre(pipelines.ManualApprovalStep("ApproveDeployment"))

        # Grant S3 permissions to the pipeline's role
        artifact_bucket.grant_read_write(pipeline.synth_step.build_step.project)


class DeployStage(cdk.Stage):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        SbGenAiStack(self, "SbGenAiStack")
