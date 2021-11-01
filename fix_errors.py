import boto3
import json
import hashlib
import datetime
import _aws_backend
from _aws_backend import QueueURL, DataBucketName, get_JSON_from_s3, delete_s3_file, region
import botocore

# list pending and look at start time
# list errors
# remove problem pending files
# resubmit to queue

sqs = boto3.resource('sqs', region_name=region)

# monkey patch with our local credientials
s3 = _aws_backend.s3 = boto3.client('s3', region_name=region)

queue = sqs.Queue(QueueURL)

def get_matching_s3_keys(bucket, prefix='', suffix=''):
    """
    Generate the keys in an S3 bucket.

    :param bucket: Name of the S3 bucket.
    :param prefix: Only fetch keys that start with this prefix (optional).
    :param suffix: Only fetch keys that end with this suffix (optional).
    """
    kwargs = {'Bucket': bucket, 'Prefix': prefix}
    while True:
        resp = s3.list_objects_v2(**kwargs)
        if not 'Contents' in resp:
            break
        for obj in resp['Contents']:
            key = obj['Key']
            yield key

        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break

def resend_case(base_file, parameter_file, case_id):
    new_data = {"base_file": base_file,
                "parameter_file": parameter_file,
                "case_id": case_id
    }
    body = json.dumps(new_data)
    mid = hashlib.sha256(body.encode()).hexdigest()
    reply = queue.send_message(MessageBody=body,
                               MessageDeduplicationId=mid,
                               MessageGroupId="main")
    message_id = reply.get('MessageId')
    s3.delete_object(Bucket=DataBucketName, Key=key)
    print(message_id)


# list pending and error
for key in get_matching_s3_keys(DataBucketName, "data/error"):
    data = get_JSON_from_s3(key)
    del data["exception"]
    del data["traceback"]
    print("re-sending", key, data["parameter_file"])
    resend_case(data["base_file"], data["parameter_file"], data["case_id"])

for key in get_matching_s3_keys(DataBucketName, "data/pending"):
    try:
        data = get_JSON_from_s3(key)
        date = datetime.datetime.fromtimestamp(data["start_time"])
        time_delta_hours = (datetime.datetime.now()-date).total_seconds()/60/60.0
        if time_delta_hours > 1:
            print("re-sending ({} hours old)".format(int(time_delta_hours)), key, data["parameter_file"])
            resend_case(data["base_file"], data["parameter_file"], data["case_id"])
    except botocore.exceptions.ClientError as error:
        pass



# the waiting files are refreshed every 500 seconds, so anything older than that we can remove
for key in get_matching_s3_keys(DataBucketName, "data/waiting"):
    try:
        data = get_JSON_from_s3(key)
        date = datetime.datetime.fromtimestamp(data["time"])
        time_delta_seconds = (datetime.datetime.now()-date).total_seconds()
        if time_delta_seconds > 600:
            print("waiting computer (last ping {} seconds ago) - clearing this file".format(int(time_delta_hours)), key)
            s3.delete_object(Bucket=DataBucketName, Key=key)
    except botocore.exceptions.ClientError as error:
        pass
