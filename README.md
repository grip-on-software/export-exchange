# Export exchange

This repository includes tools for securely uploading certain files (such as 
database dumps) to a remote server via HTTPS and GPG encryption and 
authenticated key exchanges.

## Requirements

A working version of the [GPG 
exchange](https://github.com/lhelwerd/gpg-exchange) library is required. Follow 
the instructions there to install the GPG dependencies.

Then install all Python dependencies using the following command:

`pip install -r requirements.txt`

## Running

Configure server settings in `settings.cfg` by copying `settings.cfg.example`
and replacing the variables with actual values (or leaving them out if they
should be unset or retrieved from a different source).

Initiate the upload using the following command:

`python exchange/upload.py --files LIST OF ACCEPTABLE FILES`

The `Jenkinsfile` in this repository contains example steps for a Jenkins CI 
deployment to regularly perform a database dump of a Grip on Software database 
via the scripts in the `monetdb-import` repository and the application from 
`monetdb-dumper`, also skipping unencrypted personal data. The files are then 
uploaded using the export exchange tool.
