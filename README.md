# Automation of distributed parameter studies using Itasca software: Cruncher Automatic Mode

This system uses Amazon Web Services (AWS) to coordinate running large
parameter studies with Itasca Software. The individual cases of the
parameter study are run on local or remote computers, the AWS cloud is
used to coordinate the cases and gather the data in a central location.

On the Itasca software side, a single line of Python is used to attach
an instance of FLAC3D, 3DEC, or PFC to the automatic network. Once on
the network the Itasca software checks the cloud for a case to run,
downloads the data file and parameters, runs the case, and uploads the
results to the cloud -- all automatically. A web page shows the
progress of the parameter study and shows and errors that have occurred.

This repository contains the required source code and a worked example.

## Overview

An AWS Cloud Formation template is used to set up the cloud resources.
An AWS S3 bucket and an AWS SQS queue are created to manage the
parameter study cases. The Itasca software contains an embedded Python
interpreter which acts as a client, running parameter study cases and
uploading the results. Many computers can join a parameter study and
the cases are processed in a specific order.

## requirements
This guide assumes you have the following:
- FLAC3D, 3DEC, or PFC version 7 or later
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
Launch the Cloud Formation stack with this command.

`python launch.py my-study-name`

This creates the SQS queue, the S3 bucket and gets the permissions set
up. Replace my-study-name with a name for your parameter study. Next,
run this command to configure the website and support files:

`python configure.py my-study-name`

Upon success this command with give the web site for the parameter
study and the S3 bucket name, it will look something like this (your URL will be different):

Website: http://my-study-name-databucket-17c4yhty0nr5a.s3-website.us-east-2.amazonaws.com
S3 Bucket: my-study-name-databucket-17c4yhty0nr5a

### Creating a parametric datafile

Create a Python program to run the cases in your parameter study. See
the example [prandtls_wedge.py](prandtls_wedge.py). For parameters you
want to vary wrap the variables like this:

`cohesion_array = np.array({cohesion_array})`

### Defining parameter study cases

The file [create_cases.py](create_cases.py) defines the range or
properties

`python create_cases.py`

### Attaching the Itasca software to the network
- Open the website given in the configure step. The top of this web
  site contains a one-line Python program. Copy this line.
- Open FLAC3D, 3DEC, or PFC3D
- Open the IPython console via Menu->Python->IPython console
- Paste the one line program into the IPython console window and press return

### Monitoring the progress

View the web site, it gives a summary of the number of jobs remaining
and any errors that have occurred.

### Processing the results

The results are all in the S3 bucket given by the configuration step
in the "data/" subfolder. The results are in JSON format.

### Cleaning up

- Delete all the files in the s3 bucket.
- Run the command `python clean-up.py my-study-name` to delete the
  cloud resources.

## Limitations
- The way the waiting is done FLAC3D can appear to freeze when waiting
  for messages.
- Messages that are in the queue for more than 14 days get deleted automatically.
- Not all errors are caught, some timeout network errors are not
  handled correctly and the client (the Itasca software) leaves the
  network.
- If there is an error in the outer wrapper it can be difficult to debug.
- It would be better to use Jinja2 for the templating, in some cases
  the format string method used to put values into the case file can
  go wrong if you have a dictionary literal `{}` in your case file.

## Security

A publicly readable AWS key set is created to allow the necessary
operation. Permissions are restricted to only the needed operations
but a malicious person could interfere with the system. The data file
that runs the cases is publicly readable, but the results are not
publicly readable. A more restrictive security model in which the
client computer need to know the keys could be implemented.
