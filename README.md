index.html
script.js

index.html, script.js, and bootstrap.py, aws_backend.py, need to be publicly readable

Refactor for a single bucket


# Automation of distributed parameter studies using Itasca software
Cruncher Automatic Mode

This system uses Amazon Web Services (AWS) to coordinate running large
parameter studies with Itasca Software. The individual cases of the
parameter study are run on local or remote computers, the AWS cloud is
only used to coordinate the cases and gather the data in a central
location.

On the Itasca software side, a single line of Python is used to attach
an instance of FLAC3D, 3DEC, or PFC to the automatic network. Once on
the network the Itasca software checks the cloud for a case to run,
downloads the data file and parameters, runs the case, and uploads the
results to the cloud -- all automatically. A web page shows the
progress of the parameter study and shows and errors that have occurred.


## Overview

S3 bucket
SQS queue

## Requirements
This guide assumes you have the following:
- An AWS account
- Python 3.6 or later
- The Python `pyDOE` library
- The Python `boto3` library installed and configured with sufficient
  permissions to:
  - Launch Cloud Formation stacks
  - Work with an SQS queue
  - Work with S3 buckets
- The `awscli` package installed and configured.
- Access to the AWS web console for debugging and checking the
  individual resources.

## Instructions

### Launching the Cloud Formation stack

$ python launch.py my-study-name

Creating a parametric datafile

Defining parameter study cases

Attaching the Itasca software to the network

Monitoring the progress

Processing the results

Cleaning up

## Limitations
- The way the waiting is done FLAC3D can appear to freeze when waiting
  for messages.
- Messages that are in the queue for more than 14 days get deleted automatically.
- Not all errors are caught, some timeout network errors are not
  handled correctly and the client (the Itasca software) leaves the
  network.
- Security: A publicly readable AWS key set is created to allow the
  necessary operation. Permissions are restricted to only the needed
  operations but a malicious person could interfere with the system.
