#!/usr/bin/env python3
import os

import aws_cdk as cdk
#import module from sb_gen_ai_stack.py file called SbGenAiStack
from sb_gen_ai.sb_gen_ai_stack import SbGenAiStack


app = cdk.App()
SbGenAiStack(app, "SbGenAiStack",
             env=cdk.Environment(account='058264396254', region='us-east-1'))

app.synth()
