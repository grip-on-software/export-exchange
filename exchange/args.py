"""
Command line argument parsing.

Copyright 2017-2020 ICTU
Copyright 2017-2022 Leiden University
Copyright 2017-2024 Leon Helwerda

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from argparse import ArgumentParser, Namespace
from configparser import RawConfigParser
from .upload import Uploader

def parse_args(config: RawConfigParser) -> Namespace:
    """
    Parse command line arguments.
    """

    verify = config.get('upload', 'verify')
    if verify == 'true':
        verify = True
    elif verify in ('false', ''):
        verify = False

    parser = ArgumentParser(description='Upload files securely')
    parser.add_argument('--server', default=config.get('upload', 'server'),
                        help='Upload server path')
    parser.add_argument('--verify', nargs='?', const=True, default=verify,
                        help='Verify server CA chain or path to CA to verify')
    parser.add_argument('--no-verify', dest='verify', action='store_false',
                        help='Disable host verification')

    parser.add_argument('--auth', default=config.get('upload', 'auth'),
                        choices=Uploader.AUTH_CLASSES,
                        help='Authentication method to log in to the server')
    parser.add_argument('--no-auth', dest='auth', action='store_false',
                        help='Disable HTTP authentication')
    parser.add_argument('--username', default=config.get('upload', 'username'),
                        help='Username to log in to the server')
    parser.add_argument('--password', default=config.get('upload', 'password'),
                        help='Password to log in to the server')

    parser.add_argument('--engine', default=config.get('upload', 'engine'),
                        help='GPG engine path')
    parser.add_argument('--home-dir', default=config.get('upload', 'home_dir'),
                        dest='home_dir', help='Configuration directory for GPG')

    parser.add_argument('--keyring', default=config.get('upload', 'keyring'),
                        help='Name of keyring containing authentication')
    parser.add_argument('--server-key', dest='server_key',
                        default=config.get('upload', 'server_key'),
                        help='Fingerprint of server public key to verify')
    parser.add_argument('--name', default=config.get('upload', 'name'),
                        help='Name to use in client key pair')
    parser.add_argument('--email', default=config.get('upload', 'email'),
                        help='Email to use in client key pair')
    parser.add_argument('--passphrase',
                        default=config.get('upload', 'passphrase'),
                        help='Passphrase to use to protect client private key')

    parser.add_argument('--files', nargs='*', help='Files to upload')

    log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    parser.add_argument('--log', choices=log_levels, default='INFO',
                        help='Log level (INFO by default)')

    return parser.parse_args()
