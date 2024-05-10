import sys
import boto3
import argparse
import json
import botocore
from datetime import datetime, timedelta
import time

region = "us-east-2"
cloud_formation = boto3.client('cloudformation', region_name=region)
cloud_front = boto3.client('cloudfront', region_name=region)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Delete CAM cloud formation stack.')
    parser.add_argument('stack_name', type=str,
                        help='the name of the parameter study')
    args = parser.parse_args()
    stack_name = args.stack_name

    print(f'Deleting CloudFormation stack {stack_name}')
    
    response = cloud_formation.delete_stack(StackName=stack_name)
    waiter = cloud_formation.get_waiter('stack_delete_complete')
    print("...waiting for stack to delete, this can take a few minutes...")
    waiter.wait(StackName=stack_name)
    print("CloudFormation stack deleted")
    
    print("Deleting CloudFront distribution...")
    
    distributions = cloud_front.list_distributions()
    for dist_item in distributions['DistributionList']['Items']:
        for origin in dist_item['Origins']['Items']:
            if origin['Id'] == stack_name:
                distribution_id = dist_item['Id']
                
    distribution_config = cloud_front.get_distribution_config(Id = distribution_id)
    if_match = distribution_config['ETag']
    distribution_config['DistributionConfig']['Enabled'] = False
    
    disable_distribition = cloud_front.update_distribution(DistributionConfig=distribution_config['DistributionConfig'], Id = distribution_id, IfMatch = if_match)
    print("...waiting until the distribution is disabled...")
    timeout_mins = 20 
    wait_until = datetime.now() + timedelta(minutes=timeout_mins)
    notFinished = True
    eTag = ""
    while notFinished:
        if wait_until < datetime.now():
            print("Distribution took too long to disable: exiting")
            sys.exit(1)

        status = cloud_front.get_distribution(Id = distribution_id)
        if status['Distribution']['DistributionConfig']['Enabled'] == False and status['Distribution']['Status'] == 'Deployed':
            eTag = status['ETag']
            notFinished = False
            break

        print("...not disabled yet... sleeping for 60 seconds...")
        time.sleep(60) 

    delete_distribution = cloud_front.delete_distribution(Id = distribution_id, IfMatch = eTag)
    
    print("CloudFront distribution deleted")
