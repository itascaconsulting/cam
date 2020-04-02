import sys
import boto3
import json
import botocore
from datetime import datetime
import jinja2

import argparse

parser = argparse.ArgumentParser(description='Configure cloud formation stack for the cruncher automatic mode.')
parser.add_argument('stack_json_file', type=str,
                    help='json file describing stack')
args = parser.parse_args()
filename = args.stack_json_file

with open(filename, "r") as f:
    stack_output = json.load(f)

outputs = stack_output["Stacks"][0]["Outputs"]
ret = {}
for item in outputs:
    ret[item["OutputKey"]] = item["OutputValue"]
print(ret)


region = ret["region"]
s3 = boto3.client('s3', region_name=region)

def substitute_values(filename, args):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(filename)
    body = template.render(**args)
    with open("_"+filename, "w") as f:
        f.write(body)

def upload_public_file(local_filename, remote_filename, ctype=None):
    print("uploading ", local_filename)
    args = {'ACL':'public-read'}
    if ctype is not None:
        args['ContentType'] = ctype
    s3.upload_file(local_filename, ret["DataBucketName"], remote_filename, ExtraArgs=args)

substitute_values("index.html", ret)
upload_public_file("_index.html", "index.html", 'text/html')

substitute_values("script.js", ret)
upload_public_file("_script.js", "public/script.js", "text/javascript")

substitute_values("aws_backend.py", ret)
upload_public_file("_aws_backend.py", "public/aws_backend.py", 'text/html')

substitute_values("bootstrap.py", ret)
upload_public_file("_bootstrap.py", "public/bootstrap.py", 'text/html')

1/0
upload_public_file("cam_deps.bz2", "public/cam_deps.bz2")
upload_public_file("cam_deps.zip", "public/cam_deps.zip")
print(ret['WebsiteURL'])
