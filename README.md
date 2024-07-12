# Export exchange

This repository includes tools for securely uploading certain files (such as 
database dumps) to a remote server via HTTPS and GPG encryption and 
authenticated key exchanges.

## Requirements

A working version of the [GPG 
exchange](https://github.com/lhelwerd/gpg-exchange) library is required. Follow 
the instructions there to install the GPG dependencies first.

Installation of the Python dependencies is done with the following command:

`pip install -r requirements.txt`

## Configuration

Configure server settings in `settings.cfg` by copying `settings.cfg.example`
and replacing the variables with actual values (or leaving them out if they
should be unset or retrieved from a different source). The settings file can 
also be chosen by prefixing the command in the [running](#running) section with 
`GATHERER_SETTINGS_FILE=path/to/settings.cfg`. Despite the environment variable 
name, there is no overlap between this configuration and the [data-gathering 
configuration](https://gros.liacs.nl/data-gathering/configuration.html).

The following configuration items are recognized in the `upload` section of the 
settings file, but command-line arguments may override them:

- `server`: URL (with the base path) to the upload server endpoint.
- `verify`: Verification of the HTTPS certificate of the endpoint. This can be 
  `true` to enable verification against the installed certificates, `false` or 
  empty to disable verification, or a path to verify against a specific 
  certificate file available locally.
- `auth`: Authentication class to use for the endpoint. This can be `basic` or 
  `digest`. The reference implementation of the upload endpoint uses `digest`.
- `keyring`: Name of a keyring domain to use to retrieve the password for the 
  upload user to authenticate with. If left empty, then the password must be 
  provided via the `password` setting or argument, which is less secure.
- `username`: Username to authenticate with at the endpoint.
- `password`: Password to authenticate with at the endpoint. If the `keyring` 
  is provided, then this is ignored.
- `engine`: Path to the GPG engine binary. Example: `/usr/bin/gpg2`.
- `home_dir`: Path to the configuration directory of the GPG engine. Example: 
  `/home/agent/.gnupg`, where `agent` is the current user (for example in the 
  Docker image).
- `name`: Name to use to generate or find the keypair with. This should be 
  identifiable as to which source is uploading the exported files.
- `email`: Email address to generate the keypair with. This should typically 
  refer to the person responsible for the exported files at the organization.
- `passphrase`: Passphrase to use to protect the client's private key. This is 
  used to set the passphrase during generation and, if there is no `keyring`, 
  when data is encrypted or decrypted during the exchange. Preferably, the 
  passphrase argument is passed in only during generation and stored in the 
  keyring for future use.

The keyring backend should store two credentials if used:

- Under the `username` provided as setting or argument, store the password used 
  for the digest authentication at the endpoint.
- Under the "privkey" username, store the private key's passphrase.

## Running

Initiate the upload using the following command:

`python exchange/upload.py --files LIST OF ACCEPTABLE FILES`

The `Jenkinsfile` in this repository contains example steps for a Jenkins CI 
deployment to regularly perform a database dump of a Grip on Software database 
via the database maintenance scripts in the 
[monetdb-import](https://github.com/grip-on-software/monetdb-import) repository 
and the database export application from 
[monetdb-dumper](https://github.com/grip-on-software/monetdb-dumper), also 
skipping unencrypted personal data. The files are then uploaded using the 
export exchange tool to an endpoint running the [encrypted file upload 
server](https://github.com/grip-on-software/upload).
