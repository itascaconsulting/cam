import itasca as it
it.command("python-reset-state false")

#assert it.dim() == 3, "FLAC3D is required"
#assert it.dim() == 2, "FLAC2D is required"

it.command("[global v0 = version.code.major]")
it.command("[global v1 = version.code.minor]")
code_major, code_minor = it.fish.get("v0"), it.fish.get("v1")
version_string = "{}.{}".format(code_major, code_minor)

#assert code_major == 910, "FLAC 9.1 is required"


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
import os
import jinja2

def get_computer_name():
    return gethostname() + "_" + os.name + "_" + str(os.getpid())

waiting_file = "data/waiting-" + get_computer_name() + ".json"


print("importing dependencies...")
import boto3

# Get the current AWS keys and the aws_backend.py definition.
aws_backend = ModuleType('aws_backend.py', 'AWS interface functions')
six.exec_(six.moves.urllib.request.urlopen('{{WebsiteURL}}/public/aws_backend').read(),
          aws_backend.__dict__)
sys.modules['aws_backend'] = aws_backend

# Main receive message loop
wait_count = 0
while True:
    messages = aws_backend.get_messages(10)
    if messages is not None:
        print("got {len(messages)} messages")
        runs = []
        for message in messages:
            aws_backend.delete_s3_file(waiting_file)
            wait_count = 0
            print("got job from queue: ", message.message_id)
            print(message)
            runs.append(json.loads(message.body))
            print(message.body)
            message.delete()
        for run_data in runs:
            case_id = run_data["case_id"]
            print("Running case", case_id)
            data_file_template = aws_backend.get_text_from_s3(run_data["base_file"])
            parameters = aws_backend.get_JSON_from_s3(run_data["parameter_file"])
            result_file = run_data["parameter_file"].replace("pfile", "done")
            run_data.update({"computer": get_computer_name(),
                             "version": version_string,
                             "start_time": time.time(),
                             "parameters": parameters})
            pending_file = "data/pending-{}.json".format(case_id)
            aws_backend.put_JSON_on_s3(run_data, pending_file)

            try:
                ## try to actually run the file and upload the result
                datafile_to_run = jinja2.Environment().from_string(data_file_template).render(parameters)
                result = None
                local_ns = locals()
                exec(datafile_to_run, globals(), local_ns)
                print ("result of run", result)
                run_data.update({"result": result,
                                 "end_time": time.time()})
                aws_backend.put_JSON_on_s3(run_data, result_file)
            except Exception as err:
                ## in case of any error report what the problem was along with information.
                run_data.update({"exception": traceback.format_exc(),
                                 "traceback": traceback.format_tb(err.__traceback__),
                                 "error_time": time.time()})
                aws_backend.put_JSON_on_s3(run_data, "data/error-{}.json".format(case_id))
                print(err)
            # delete pending file
            aws_backend.delete_s3_file(pending_file)

    else:
        # we are waiting...
        if wait_count % 5 == 0: # only write the first time and every subsequent 5th time.
            aws_backend.put_JSON_on_s3({"time": time.time()}, waiting_file)

        wait_count += 1
        if wait_count == 1:
            time.sleep(0.01)
        else:
            for s in range(100):
                for cs in range(100):
                    time.sleep(0.01)
