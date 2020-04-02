import pyDOE
import numpy as np
np.random.seed(12344)
import boto3
import json
import random
import hashlib
import base64
import uuid
from io import BytesIO

from _aws_backend import DataBucketName, QueueURL, region
s3 = boto3.client('s3', region_name=region)
sqs = boto3.resource('sqs', region_name=region)




def put_JSON_on_s3(data, object_name):
    s3.upload_fileobj(BytesIO(json.dumps(data).encode()), DataBucketName, object_name)

queue = sqs.Queue(QueueURL)
local_datafile = "prandtls_wedge.py"
remote_datafile = "public/" + local_datafile
s3.upload_file(local_datafile, DataBucketName, remote_datafile)
number_of_unknowns = 5

min_coh, max_coh = 0.5e5, 5e5
assert max_coh > min_coh
delta_coh = max_coh - min_coh

lhc_sizes = range(3, 6)
run_data = {}

for lhc_size in lhc_sizes:
    print("adding cube 2**{}".format(lhc_size))
    hyper_cube = pyDOE.lhs(number_of_unknowns, 2**lhc_size)
    cohesion_hyper_cube = min_coh + hyper_cube*delta_coh

    for i in range(len(hyper_cube)):
        if i % 100 == 0:
            print("sending", i)
        parameters = {"cohesion_array" : cohesion_hyper_cube[i].tolist(),
                      "raw_parameters" : hyper_cube[i].tolist()}
        pfile = "data/pfile-{}.json".format(uuid.uuid4())
        put_JSON_on_s3(parameters, pfile)
        data = {"base_file": remote_datafile,
                "parameter_file": pfile}
        body = json.dumps(data)
        mid = hashlib.sha256(body.encode()).hexdigest()
        reply = queue.send_message(MessageBody=body,
                                   MessageDeduplicationId=mid,
                                   MessageGroupId="main")
        message_id = reply.get('MessageId')

        run_data[message_id] = {"parameters": parameters, "data": data}

put_JSON_on_s3(run_data, "all_runs.json")
