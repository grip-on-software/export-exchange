"""
Secure PGP file upload.
"""

import argparse
import configparser
import os
import tempfile
import gpg
from gpg_exchange import Exchange
import keyring
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

class Uploader(object):
    """
    Client for the secure PGP file upload.
    """

    AUTH_CLASSES = {
        'basic': HTTPBasicAuth,
        'digest': HTTPDigestAuth
    }

    def __init__(self, args):
        self.args = args
        self._gpg = Exchange(home_dir=self.args.home_dir,
                             engine_path=self.args.engine,
                             passphrase=self._get_passphrase)

        self._session = requests.Session()
        self._session.verify = self.args.verify

        if self.args.auth in self.AUTH_CLASSES:
            if self.args.keyring:
                password = keyring.get_password(self.args.keyring,
                                                self.args.username)
            else:
                password = self.args.password

            auth = self.AUTH_CLASSES[self.args.auth]
            self._session.auth = auth(self.args.username, password)

    def _get_passphrase(self, hint, desc, prev_bad, hook=None):
        # pylint: disable=unused-argument
        if self.args.keyring:
            return keyring.get_password(self.args.keyring, 'privkey')

        return self.args.passphrase

    def run(self):
        """
        Perform the verified key exchange and upload of files.
        """

        try:
            # Check if we have our own key and the public key for the server
            self._gpg.find_key(self.args.name)
            server_key = self._gpg.find_key(self.args.server_key)
        except KeyError:
            print "Exchanging keys..."
            server_key = self.exchange()

        print "Server key: {}".format(server_key.fpr)
        print "Uploading to server..."
        self.upload(server_key, self.args.files)

        self._gpg = None

    def exchange(self):
        """
        Exchange public keys safely with the server.
        """

        try:
            # Retrieve existing key
            key = self._gpg.find_key(self.args.name)
            fpr = key.fpr
        except KeyError:
            key = self._gpg.generate_key(self.args.name, self.args.email,
                                         comment="GROS upload key",
                                         passphrase=self.args.passphrase)
            fpr = key.fpr

        with gpg.Data() as pubkey:
            pubkey = self._gpg.export_key(fpr)
            data = {
                'pubkey': pubkey
            }

        response = self._session.post(self.args.server + "/exchange", json=data)

        try:
            response.raise_for_status()
            data = response.json()
        except (requests.exceptions.HTTPError, ValueError) as error:
            raise RuntimeError("Invalid response: {}\n{}".format(error, response.text))

        try:
            # Decrypt the encrypted message to import the server's public key.
            # Do not verify the signature since we don't have it currently.
            server_key = self._gpg.decrypt_text(str(data['pubkey']),
                                                verify=False)
            key, result = self._gpg.import_key(server_key)
        except (gpg.errors.GpgError, ValueError) as error:
            raise ValueError('Data could not be decrypted: {}'.format(str(error)))

        if result.imported != 1:
            raise RuntimeError("Invalid public key from server")

        if key.fpr != self.args.server_key:
            raise RuntimeError("Received incorrect key: {}".format(key.fpr))

        return key

    def upload(self, server_key, filenames):
        """
        Upload files as indicated by a list of `filenames` to the server by
        encrypting them with the server public key object `server_key`.
        """

        files = []
        for filename in filenames:
            with open(filename) as plaintext:
                upload_file = tempfile.TemporaryFile()
                self._gpg.encrypt_file(plaintext, upload_file, server_key,
                                       always_trust=True)

                upload_file.seek(0, os.SEEK_SET)
                files.append(("files", (filename, upload_file)))

        response = self._session.post(self.args.server + "/upload", files=files)
        try:
            response.raise_for_status()
            data = response.json()
        except (requests.exceptions.HTTPError, ValueError) as error:
            raise RuntimeError("Invalid response: {}\n{}".format(error, response.text))

        if 'success' not in data or not data['success']:
            raise RuntimeError("Server does not indicate success: {}".format(data))

def parse_args(config):
    """
    Parse command line arguments
    """

    verify = config.get('upload', 'verify')
    if verify == 'true':
        verify = True
    elif verify == 'false' or verify == '':
        verify = False

    parser = argparse.ArgumentParser(description='Upload files securely')
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

    return parser.parse_args()

def main():
    """
    Main entry point.
    """

    if 'GATHERER_SETTINGS_FILE' in os.environ:
        config_file = os.environ['GATHERER_SETTINGS_FILE']
    else:
        config_file = 'settings.cfg'

    config = configparser.RawConfigParser()
    config.read(config_file)
    args = parse_args(config)

    uploader = Uploader(args)
    uploader.run()

if __name__ == "__main__":
    main()
