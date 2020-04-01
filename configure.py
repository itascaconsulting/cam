import sys
import boto3
import json
import botocore
from datetime import datetime

region = "us-east-2"
#filename = "cam_stack.yaml"
filename = "simple.yaml"

s3 = boto3.client('s3', region_name=region)

with open("aa-stack.json", "r") as f:
    stack_output = json.load(f)

outputs = stack_output["Stacks"][0]["Outputs"]
ret = {}
for item in outputs:
    ret[item["OutputKey"]] = item["OutputValue"]
print(ret)
s3.upload_file("index.html", ret["DataBucketName"], "index.html",
               ExtraArgs={'ACL':'public-read',
                          'ContentType':'text/html'})

def upload_public_file(filename, ctype=None):
    args = {'ACL':'public-read'}
    if ctype is not None:
        args['ContentType'] = ctype
    s3.upload_file(filename, ret["DataBucketName"], "public/"+filename,
                   ExtraArgs=args)

upload_public_file("script.js", "text/javascript")
