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
import os
import jinja2

def get_computer_name():
    return gethostname() + "_" + os.name + "_" + str(os.getpid())

waiting_file = "data/waiting-" + get_computer_name() + ".json"


## first we bootstrap the environment
print("Creating a temporary folder...")
new_dir = tempfile.mkdtemp()
os.chdir(new_dir)
print(new_dir)

deps_url = '{{WebsiteURL}}/public/cam_deps.bz2'
file_name = os.path.join(new_dir, "cam_deps.bz2")
print("Downloading dependencies...")
with urllib.request.urlopen(deps_url) as response, open(file_name, 'wb') as out_file:
    shutil.copyfileobj(response, out_file)

## not all installs can unzip bzip2 for some reason
try:
    print("Inflating bz2 dependencies...")
    with ZipFile(file_name, 'r') as zipObj:
        zipObj.extractall()
    print("success")
except RuntimeError as ex:
    print("Cannot unzip bz2 trying .zip...")
    deps_url = '{{WebsiteURL}}/public/cam_deps.zip'
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

# Main receive message loop
wait_count = 0
while True:
    message = aws_backend.get_message()
    if message is not None:
        aws_backend.delete_s3_file(waiting_file)
        wait_count = 0
        print("got job from queue: ", message.message_id)
        print(message)
        run_data = json.loads(message.body)
        print(message.body)
        message.delete()
        case_id = run_data["case_id"]
        print("Case ID is: ", case_id)
        data_file_template = aws_backend.get_text_from_s3(run_data["base_file"])
        parameters = aws_backend.get_JSON_from_s3(run_data["parameter_file"])
        result_file = run_data["parameter_file"].replace("pfile", "done")
        run_data.update({"computer": get_computer_name(),
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
        for s in range(100):  # check queue every 100 seconds
            # these loops prevents blocking in the GUI
            for cs in range(100):
                time.sleep(0.01)
