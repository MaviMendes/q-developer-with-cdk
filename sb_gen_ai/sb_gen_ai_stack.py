from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3_deployment as s3deploy,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct

class SbGenAiStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a private S3 bucket to store the HTML file
        website_bucket = s3.Bucket(
            self, "WebsiteBucketmariasme",
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Create an Origin Access Identity for CloudFront
        origin_access_identity = cloudfront.OriginAccessIdentity(
            self, "OriginAccessIdentity",
            comment="Allow CloudFront to access the S3 bucket"
        )

        # Grant read permissions to CloudFront
        website_bucket.grant_read(origin_access_identity)

        # Create a CloudFront distribution
        distribution = cloudfront.Distribution(
            self, "WebsiteDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    website_bucket,
                    origin_access_identity=origin_access_identity
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
            ),
            default_root_object="index.html"
        )

        # Deploy the HTML file to the S3 bucket
        s3deploy.BucketDeployment(
            self, "DeployWebsite",
            sources=[s3deploy.Source.asset(".\website")],
            destination_bucket=website_bucket,
            distribution=distribution,
            retain_on_delete=False
        )

        # Output the CloudFront distribution URL
        CfnOutput(
            self, "DistributionUrl",
            value=f"https://{distribution.distribution_domain_name}",
            description="Website URL"
        )


