import json
import boto3
import base64
from io import BytesIO

data1 = base64.decodebytes(b'TkpEYUpzdWxveG92QWxuMm01S0Q0TEdmV0FFeWdkTVBjTEMxa3ZUUg==\n').decode()
DataBucketName = base64.decodebytes(b'Y2FtLXRlc3QtZGF0YWJ1Y2tldC1oajFqOWJndDMzNnE=\n').decode()
data0 = base64.decodebytes(b'QUtJQTM1M01ZUURTNU5NN05BM0c=\n').decode()
QueueURL = base64.decodebytes(b'aHR0cHM6Ly9zcXMudXMtZWFzdC0yLmFtYXpvbmF3cy5jb20vODIwMDI5OTgwOTAxL2NhbS10ZXN0\nLUpvYlF1ZXVlLVpGU1pWWFpRNkhFUy5maWZv\n').decode()


sqs = boto3.resource('sqs',
                     aws_access_key_id=data0,
                     aws_secret_access_key=data1,
                     region_name='us-east-2')

queue = sqs.Queue(QueueURL)


s3 = boto3.client('s3',
                  aws_access_key_id=data0,
                  aws_secret_access_key=data1,
                  region_name='us-east-2')

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
