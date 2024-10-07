import aws_cdk as core
import aws_cdk.assertions as assertions

from sb_gen_ai.sb_gen_ai_stack import SbGenAiStack

# example tests. To run these tests, uncomment this file along with the example
# resource in sb_gen_ai/sb_gen_ai_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SbGenAiStack(app, "sb-gen-ai")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
