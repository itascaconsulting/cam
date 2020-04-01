import sys
import boto3
import argparse
import json
import botocore
from datetime import datetime

region = "us-east-2"
cf = boto3.client('cloudformation', region_name=region)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Delete CAM cloud formation stack.')
    parser.add_argument('stack_name', type=str,
                        help='the name of the parameter study')
    args = parser.parse_args()
    stack_name = args.stack_name

    print('Deleting {}'.format(stack_name))
    response = cf.delete_stack(StackName=stack_name)
    waiter = cf.get_waiter('stack_delete_complete')
    print("...waiting for stack to delete, this can take a few minutes...")
    waiter.wait(StackName=stack_name)
    print("done")
