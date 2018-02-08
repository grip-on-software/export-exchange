Tools for securely uploading certain files to a remote server via HTTPS and GPG
encryption and authenticated key exchanges.

# Requirements

A working version of the [GPG 
exchange](https://github.com/lhelwerd/gpg-exchange) library is required. Follow 
the instructions there to install the GPG dependencies.

Then install all PYthon dependencies using the following command:

`pip install -r requirements.txt`

# Running

Configure server settings in `settings.cfg` by copying `settings.cfg.example`
and replacing the variables with actual values (or leaving them out if they
should be unset or retrieved from a different source).

Initiate the upload using the following command:

`python upload.py --files LIST OF ACCEPTABLE FILES`
