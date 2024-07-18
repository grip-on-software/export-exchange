# Export exchange

[![PyPI](https://img.shields.io/pypi/v/gros-export-exchange.svg)](https://pypi.python.org/pypi/gros-export-exchange)
[![Build 
status](https://github.com/grip-on-software/export-exchange/actions/workflows/upload-tests.yml/badge.svg)](https://github.com/grip-on-software/export-exchange/actions/workflows/upload-tests.yml)
[![Coverage 
Status](https://coveralls.io/repos/github/grip-on-software/export-exchange/badge.svg?branch=master)](https://coveralls.io/github/grip-on-software/export-exchange?branch=master)
[![Quality Gate
Status](https://sonarcloud.io/api/project_badges/measure?project=grip-on-software_export-exchange&metric=alert_status)](https://sonarcloud.io/project/overview?id=grip-on-software_export-exchange)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.12773659.svg)](https://doi.org/10.5281/zenodo.12773659)

This repository includes tools for securely uploading certain files (such as 
database dumps) to a remote server via HTTPS and GPG encryption and 
authenticated key exchanges. Although available as a package, it is mostly 
meant to run as a standalone program.

## Installation

The [GPG exchange](https://github.com/lhelwerd/gpg-exchange) library is 
required to be in a working state. Follow the instructions there to install the 
GPG dependencies first. Then, to install the latest release version of the 
packaged program from PyPI, run the following command:

```
pip install gros-export-exchange
```

Another option is to build the program from this repository, which allows using 
the most recent development code. Run `make setup` to install the dependencies. 
The uploader itself may then be installed with `make install`, which places the 
package in your current environment. We recommend using a virtual environment 
during development.

## Configuration

Configure server settings in `settings.cfg` by copying `settings.cfg.example`
or the example file below:
```ini
[upload]
server = $UPLOAD_SERVER
verify = $UPLOAD_VERIFY
auth = $UPLOAD_AUTH
keyring = $UPLOAD_KEYRING
username = $UPLOAD_USERNAME
password = $UPLOAD_PASSWORD
engine = $UPLOAD_ENGINE
home_dir = $UPLOAD_HOME_DIR
server_key = $UPLOAD_SERVER_KEY
name = $UPLOAD_NAME
email = $UPLOAD_EMAIL
passphrase = $UPLOAD_PASSPHRASE
```
Replace the variables with actual values (or leave them out if they should be 
unset or retrieved from a different source). The settings file can also be 
chosen by prefixing the command in the [running](#running) section with 
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

```
gros-export-exchange --files LIST OF ACCEPTABLE FILES
```

The `Jenkinsfile` in this repository contains example steps for a Jenkins CI 
deployment to regularly perform a database dump of a Grip on Software (GROS) 
database via the database maintenance scripts in the 
[monetdb-import](https://github.com/grip-on-software/monetdb-import) repository 
and the database export application from 
[monetdb-dumper](https://github.com/grip-on-software/monetdb-dumper), also 
skipping unencrypted personal data. The files are then uploaded using the 
export exchange tool to an endpoint running the [encrypted file upload 
server](https://github.com/grip-on-software/upload).

## Development and testing

To run tests, first install the test dependencies with `make setup_test` which 
also installs all dependencies for the uploader. Then `make coverage` provides 
test results in the output and in XML versions compatible with, e.g., JUnit and 
SonarQube available in the `test-reports/` directory. If you do not need XML 
outputs, then run `make test` to just report on test successes and failures or 
`make cover` to also have the terminal report on hits and misses in statements 
and branches.

[GitHub Actions](https://github.com/grip-on-software/export-exchange/actions) 
is used to run the unit tests and report on coverage on commits and pull 
requests. This includes quality gate scans tracked by 
[SonarCloud](https://sonarcloud.io/project/overview?id=grip-on-software_export-exchange) 
and [Coveralls](https://coveralls.io/github/grip-on-software/export-exchange) 
for coverage history.

The Python module conforms to code style and typing standards which can be 
checked using Pylint with `make pylint` and mypy with `make mypy`, after 
installing the pylint and mypy dependencies using `make setup_analysis`; typing 
reports are XML formats compatible with JUnit and SonarQube placed in the 
`mypy-report/` directory. To also receive the HTML report, use `make mypy_html` 
instead.

We publish releases to [PyPI](https://pypi.org/project/gros-export-exchange/) 
using `make setup_release` to install dependencies and `make release` which 
performs multiple checks: unit tests, typing, lint and version number 
consistency. The release files are also published on 
[GitHub](https://github.com/grip-on-software/export-exchange/releases) and from 
there are archived on [Zenodo](https://zenodo.org/doi/10.5281/zenodo.12773658). 
Noteworthy changes to the module are added to the [changelog](CHANGELOG.md).

## License

GROS export exchange tools for securely uploading files via HTTPS and GPG are 
licensed under the Apache 2.0 License.
