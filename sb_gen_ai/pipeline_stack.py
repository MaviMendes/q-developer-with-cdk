import aws_cdk as cdk
from aws_cdk import (
    Stack,
    SecretValue,
    aws_s3 as s3,
    aws_codebuild as codebuild,
    aws_iam as iam,
    pipelines
)
from aws_cdk.pipelines import CodePipeline, CodePipelineSource, ShellStep
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

        # Create a CodeBuild project to run synth and save differences
        synth_project = codebuild.PipelineProject(
            self, "SynthProject",
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {
                            "python": "3.9"
                        },
                        "commands": [
                            "npm install -g aws-cdk",
                            "python -m pip install -r requirements.txt"
                        ]
                    },
                    "build": {
                        "commands": [
                            "git diff HEAD^ HEAD > code_diff.txt",
                            "cdk synth",
                            "aws s3 cp code_diff.txt s3://${ARTIFACT_BUCKET}/code_diff_${CODEBUILD_BUILD_NUMBER}.txt",
                            "aws s3 cp cdk.out s3://${ARTIFACT_BUCKET}/synth_${CODEBUILD_BUILD_NUMBER} --recursive"
                        ]
                    }
                },
                "artifacts": {
                    "base-directory": "cdk.out",
                    "files": "**/*"
                }
            }),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0
            ),
            environment_variables={
        "ARTIFACT_BUCKET": codebuild.BuildEnvironmentVariable(value=artifact_bucket.bucket_name)
    }
        )

        # Grant permissions to the CodeBuild project to access the S3 bucket
        artifact_bucket.grant_read_write(synth_project)
    

        # Define the pipeline
        pipeline = CodePipeline(
            self, "Pipeline",
            synth=ShellStep("Synth", 
                input=source,
                commands=[],
                primary_output_directory="cdk.out"
            )
        )

        # Add stages to the pipeline
        deploy_stage = pipeline.add_stage(DeployStage(self, "Deploy"))

        # Optionally, add manual approval before deployment
        deploy_stage.add_pre(cdk.pipelines.ManualApprovalStep("ApproveDeployment"))



class DeployStage(cdk.Stage):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        SbGenAiStack(self, "SbGenAiStack")


