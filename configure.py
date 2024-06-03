import sys
import boto3
import json
import botocore
from datetime import datetime
import jinja2
import os.path
import argparse
import time

parser = argparse.ArgumentParser(description='Configure cloud formation stack for the cruncher automatic mode.')
parser.add_argument('stack_name', type=str,
                    help='The name of the parameter study.')
args = parser.parse_args()
filename = args.stack_name

if not os.path.isfile(filename):
    raise RuntimeError("Cannot find {}".format(filename))

with open(filename, "r") as f:
    stack_output = json.load(f)

outputs = stack_output["Stacks"][0]["Outputs"]
study_name = stack_output["Stacks"][0]["StackName"]


print("Creating a Cloud Front distribution...")
cf_distribution = cf.create_distribution(
    DistributionConfig={
        'CallerReference': f'{study_name}_{str(int(time.time()))}',
        'Aliases': {
            'Quantity': 0,
            'Items': []
        },
        'DefaultRootObject': '',
        'Origins': {
            'Quantity': 1,
            'Items': [
                {
                    'Id': study_name,
                    'DomainName': ret['WebsiteURL'].removeprefix('http://'), # python >= 3.9
                    'OriginPath': '',
                    'CustomHeaders': {
                        'Quantity': 0,
                        'Items': []
                    },
                    'CustomOriginConfig': {
                        'HTTPPort': 80,
                        'HTTPSPort': 443,
                        'OriginProtocolPolicy': 'http-only',
                        'OriginSslProtocols': {
                            'Quantity': 4,
                            'Items': [
                                'SSLv3','TLSv1','TLSv1.1','TLSv1.2',
                            ]
                        },
                        'OriginReadTimeout': 30,
                        'OriginKeepaliveTimeout': 5
                    },
                    'ConnectionAttempts': 3,
                    'ConnectionTimeout': 10,
                    'OriginShield': {
                        'Enabled': False
                    },
                    'OriginAccessControlId': ''
                },
            ]
        },
        'OriginGroups': {
            'Quantity': 0,
            'Items': []
        },
        'DefaultCacheBehavior': {
            'TargetOriginId': study_name,
            'TrustedSigners': {
                'Enabled': False,
                'Quantity': 0
            },
            'TrustedKeyGroups': {
                'Enabled': False,
                'Quantity': 0
            },
            'ViewerProtocolPolicy': 'redirect-to-https',
            'AllowedMethods': {
                'Quantity': 7,
                'Items': [
                    'GET','HEAD','POST','PUT','PATCH','OPTIONS','DELETE'
                ],
                'CachedMethods': {
                    'Quantity': 2,
                    'Items': [
                        'GET','HEAD'
                    ]
                }
            },
            'SmoothStreaming': False,
            'CachePolicyId': '658327ea-f89d-4fab-a63d-7e88639e58f6',
            'Compress': True
        },
        'CacheBehaviors': {
            'Quantity': 0
        },
        'CustomErrorResponses': {
            'Quantity': 0,
            'Items': []
        },
        'Comment': f'cloudfront distribution for {study_name}',
        'Logging': {
            'Enabled': False,
            'IncludeCookies': False,
            'Bucket': '',
            'Prefix': ''
        },
        'PriceClass': 'PriceClass_All',
        'Enabled': True,
        'ViewerCertificate': {
            'CloudFrontDefaultCertificate': True
        },
        'Restrictions': {
            'GeoRestriction': {
                'RestrictionType': 'none',
                'Quantity': 0,
                'Items': []
            }
        },
        'WebACLId': '',
        'HttpVersion': 'http2',
        'IsIPV6Enabled': True,
        'ContinuousDeploymentPolicyId': '',
        'Staging': False
    }
)

print('...waiting until CloudFront distribution is deployed - this may take a few minutes...')
waiter = cf.get_waiter('distribution_deployed')
waiter.wait(
    Id = cf_distribution['Distribution']['Id'],
    WaiterConfig = {
        'Delay': 30,
        'MaxAttempts': 50
    }
)
print("CloudFront distribution is deployed")

print(f"Website: https://{cf_distribution['Distribution']['DomainName']}")
print("S3 Bucket: ", ret['DataBucketName'])



ret = {}
for item in outputs:
    ret[item["OutputKey"]] = item["OutputValue"]

# swap in the Cloud front url
assert "WebsiteURL" in ret
ret["WebsiteURL"] = f"https://{cf_distribution['Distribution']['DomainName']}"
print(ret)

region = ret["region"]
s3 = boto3.client('s3', region_name=region)
cf = boto3.client('cloudfront', region_name=region)

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
upload_public_file("_aws_backend.py", "public/aws_backend", 'text/html')

substitute_values("bootstrap.py", ret)
upload_public_file("_bootstrap.py", "public/bootstrap", 'text/html')
