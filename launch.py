import sys
import boto3
import argparse
import json
import botocore
from datetime import datetime

region = "us-east-2"
filename = "cam_stack.yaml"
#filename = "simple.yaml"

cf = boto3.client('cloudformation', region_name=region)
s3 = boto3.client('s3', region_name=region)


#see https://gist.github.com/svrist/73e2d6175104f7ab4d201280acba049c
def stack_exists(stack_name):
    stacks = cf.list_stacks()['StackSummaries']
    for stack in stacks:
        if stack['StackStatus'] == 'DELETE_COMPLETE':
            continue
        if stack_name == stack['StackName']:
            return True
    return False


def _parse_template(template):
    with open(template) as template_fileobj:
        template_data = template_fileobj.read()
    cf.validate_template(TemplateBody=template_data)
    return template_data

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Launch a cloud formation stack for the cruncher automatic mode.')
    parser.add_argument('stack_name', type=str,
                        help='the name of the parameter study')
    args = parser.parse_args()
    stack_name = args.stack_name

    print("launching stack with name {}".format(stack_name))
    if stack_exists(stack_name):
        print("A stack by this name already exists! Exiting")
    else:
        params = {
            'StackName': stack_name,
            'Capabilities' : ['CAPABILITY_IAM'],
            'TemplateBody': _parse_template(filename),
            'Tags' : [{'Key': "Job", 'Value': "cam_{}".format(stack_name)}]
        }
        try:
            print('Creating {}'.format(stack_name))
            stack_result = cf.create_stack(**params)
            waiter = cf.get_waiter('stack_create_complete')
            print("...waiting for stack to be ready, this can take a few minutes...")
            waiter.wait(StackName=stack_name)
        except botocore.exceptions.ClientError as ex:
            error_message = ex.response['Error']['Message']
            if error_message == 'No updates are to be performed.':
                print("No changes")
            else:
                raise
        stack_output = cf.describe_stacks(StackName=stack_result['StackId'])
        stack_output["Stacks"][0]["Outputs"].append({"OutputKey": "region",
                                                     "OutputValue": region})
        with open("{}.json".format(stack_name), "w") as f:
            print("writing stack details to {}".format("{}.json".format(stack_name)))
            json.dump(stack_output, f, indent=2, default=json_serial)
        outputs = stack_output["Stacks"][0]["Outputs"]
        print("done")
