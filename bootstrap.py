try:
    import itasca as it
    it.command("python-reset-state false")
except:
    pass

import urllib.request
import shutil
import tempfile
import os
from zipfile import ZipFile
import json
import time
import base64
from socket import gethostname
import six
import traceback
from types import ModuleType
import sys

## first we bootstrap the environment
print("Creating a temporary folder...")
new_dir = tempfile.mkdtemp()
os.chdir(new_dir)
print(new_dir)

deps_url = '{{WebsiteURL}}.com/public/cam_deps.bz2'
file_name = os.path.join(new_dir, "cam_deps.bz2")
print("Downloading dependencies...")
with urllib.request.urlopen(deps_url) as response, open(file_name, 'wb') as out_file:
    shutil.copyfileobj(response, out_file)

## not all installs can unzip bzip2 for some reason
try:
    print("Inflating dependencies...")
    with ZipFile(file_name, 'r') as zipObj:
        zipObj.extractall()
except RuntimeError as ex:
    print("Cannot unzip bz2 trying .zip...")
    deps_url = '{{WebsiteURL}}.com/public/cam_deps.zip'
    file_name = os.path.join(new_dir, "cam_deps.zip")
    print("Downloading dependencies...")
    with urllib.request.urlopen(deps_url) as response, open(file_name, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

print("importing dependencies...")
import boto3

# Get the current AWS keys and the aws_backend.py definition.
aws_backend = ModuleType('aws_backend.py', 'AWS interface functions')
six.exec_(six.moves.urllib.request.urlopen('{{WebsiteURL}}/public/aws_backend.py').read(),
          aws_backend.__dict__)
sys.modules['aws_backend'] = aws_backend

# we need this because we do not want to replace everything in {}
def safeformat(str, **kwargs):
    class SafeDict(dict):
        def __missing__(self, key):
            return '{' + key + '}'
    replacements = SafeDict(**kwargs)
    return str.format_map(replacements)

# Main receive message loop
while True:
    message = aws_backend.get_message()
    if message is not None:
        message_id = message.message_id
        print("got job from queue: ", message_id)
        print(message)
        run_data = json.loads(message.body)
        message.delete()
        print(message.body)
        data_file_template = aws_backend.get_text_from_s3(run_data["base_file"])
        parameters = aws_backend.get_JSON_from_s3(run_data["parameter_file"])
        run_data.update({"computer": gethostname(),
                         "start_time": time.time(),
                         "parameters": parameters})
        pending_file = "pending-{}.json".format(message_id)
        aws_backend.put_JSON_on_s3(run_data, pending_file)
        datafile_to_run = safeformat(data_file_template, **parameters)
        try:
            ## try to actually run the file and upload the result
            result = None
            local_ns = locals()
            exec(datafile_to_run, globals(), local_ns)
            print ("result of run", result)
            run_data.update({"result": result,
                             "end_time": time.time()})
            aws_backend.put_JSON_on_s3(run_data, "done-{}.json".format(message_id))
        except Exception as err:
            ## in case of any error report what the problem was along with information.
            run_data.update({"exception": traceback.format_exc(),
                             "traceback": traceback.format_tb(err.__traceback__),
                             "error_time": time.time()})
            aws_backend.put_JSON_on_s3(run_data, "error-{}.json".format(message_id))
            print(err)
        # delete pending file
        aws_backend.delete_s3_file(pending_file)
    else:
        # we are waiting...
        # we could write a file to say we are waiting?
        # do not churn s3 too much...
        time.sleep(100)
