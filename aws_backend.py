import json
import boto3
from io import BytesIO

data0 = {{ItascaCodeClientAccessKey}}
data1 = {{ItascaCodeClientSecretKey}}
DataBucketName = {{DataBucketName}}
QueueURL = {{QueueURL}}
region = {{region}}

sqs = boto3.resource('sqs',
                     aws_access_key_id=data0,
                     aws_secret_access_key=data1,
                     region_name=region)

queue = sqs.Queue(QueueURL)


s3 = boto3.client('s3',
                  aws_access_key_id=data0,
                  aws_secret_access_key=data1,
                  region_name=region)

def delete_s3_file(file_name):
    s3.delete_object(Bucket=DataBucketName, Key=file_name)

def put_file_on_s3(file_name):
    s3.upload_file(file_name, DataBucketName, file_name)

def put_text_on_s3(data, object_name):
    s3.upload_fileobj(data, DataBucketName, object_name)

def put_JSON_on_s3(data, object_name):
    put_text_on_s3(BytesIO(json.dumps(data).encode()), object_name)

def get_text_from_s3(object_name):
    with BytesIO() as f:
        s3.download_fileobj(DataBucketName, object_name, f)
        f.seek(0)
        return f.read().decode()

def get_JSON_from_s3(object_name):
    return json.loads(get_text_from_s3(object_name))

def get_message():
    messages = queue.receive_messages(MaxNumberOfMessages=1,
                                      VisibilityTimeout=10,
                                      WaitTimeSeconds=0)
    if len(messages)==1:
        message = messages[0]
        return message
    else:
        return None
