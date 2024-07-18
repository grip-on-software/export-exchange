"""
Secure PGP file upload.

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

from argparse import Namespace
import logging
import os
import tempfile
from typing import Any, Dict, Optional, Sequence, Union, Type, TYPE_CHECKING
import gpg
from gpg_exchange import Exchange
try:
    import keyring
except ImportError:
    if not TYPE_CHECKING:
        keyring = None
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

class Uploader:
    """
    Client for the secure PGP file upload.
    """

    PGP_ARMOR_MIME = "application/pgp-encrypted"
    PGP_BINARY_MIME = "application/x-pgp-encrypted-binary"

    AUTH_CLASSES: Dict[str, Union[Type[HTTPBasicAuth], Type[HTTPDigestAuth]]] = {
        'basic': HTTPBasicAuth,
        'digest': HTTPDigestAuth
    }

    def __init__(self, args: Namespace):
        self.args = args
        self._gpg = Exchange(home_dir=self.args.home_dir,
                             engine_path=self.args.engine,
                             passphrase=self._get_passphrase)

        self._session = requests.Session()
        self._session.verify = self.args.verify

        self._name = str(self.args.name)
        self._keyring = str(self.args.keyring)

        auth_class = str(self.args.auth)
        if auth_class in self.AUTH_CLASSES:
            username = str(self.args.username)
            if keyring and self._keyring:
                password = keyring.get_password(self._keyring, username)
            else:
                password = str(self.args.password)

            auth = self.AUTH_CLASSES[auth_class]
            self._session.auth = auth(username, password)

    def _get_passphrase(self, hint: str, desc: str, prev_bad: int,
                        hook: Optional[Any] = None) -> str:
        # pylint: disable=unused-argument
        if keyring and self._keyring:
            return keyring.get_password(self._keyring, 'privkey')

        return self.args.passphrase

    def run(self) -> None:
        """
        Perform the verified key exchange and upload of files.
        """

        try:
            # Check if we have our own key and the public key for the server
            self._gpg.find_key(self._name)
            server_key = self._gpg.find_key(self.args.server_key)
        except KeyError:
            logging.info("Exchanging keys...")
            server_key = self.exchange()

        logging.info("Server key: %s", server_key.fpr)
        logging.info("Uploading to server...")
        self.upload(server_key, self.args.files)

        del self._gpg

    def exchange(self) -> gpg.core.gpgme._gpgme_key:
        """
        Exchange public keys safely with the server.
        """

        try:
            # Retrieve existing key
            key = self._gpg.find_key(self._name)
            fpr = key.fpr
        except KeyError:
            key = self._gpg.generate_key(self._name, self.args.email,
                                         comment="GROS upload key",
                                         passphrase=self.args.passphrase)
            fpr = key.fpr

        pubkey: Union[str, bytes, gpg.Data] = ''
        with gpg.Data() as pubkey:
            pubkey = self._gpg.export_key(fpr)
            data = {
                'pubkey': pubkey.decode('utf-8') \
                    if isinstance(pubkey, bytes) else str(pubkey)
            }

        response = self._session.post(f"{self.args.server}/exchange", json=data)

        try:
            response.raise_for_status()
            data = response.json()
        except (requests.exceptions.HTTPError, ValueError) as error:
            raise RuntimeError(f"Invalid response: {response.text}") from error

        try:
            # Decrypt the encrypted message to import the server's public key.
            # Do not verify the signature since we don't have it currently.
            encoded_pubkey = str(data['pubkey']).encode('utf-8')
            server_key = self._gpg.decrypt_text(encoded_pubkey,
                                                verify=False)
            key = self._gpg.import_key(server_key)[0]
        except (gpg.errors.GpgError, ValueError) as error:
            raise ValueError('Data could not be decrypted') from error

        if key.fpr != self.args.server_key:
            raise RuntimeError(f"Received incorrect key: {key.fpr}")

        return key

    def upload(self, server_key: gpg.core.gpgme._gpgme_key,
               filenames: Sequence[str]) -> None:
        """
        Upload files as indicated by a list of `filenames` to the server by
        encrypting them with the server public key object `server_key`.
        """

        file_field = "files"
        files = []
        temp_files = []
        for filename in filenames:
            with open(filename, 'rb') as plaintext:
                upload_file = tempfile.TemporaryFile()
                self._gpg.encrypt_file(plaintext, upload_file, server_key,
                                       always_trust=True, armor=False)

                upload_file.seek(0, os.SEEK_SET)
                files.append((file_field,
                              (filename, upload_file, self.PGP_BINARY_MIME)))
                temp_files.append(upload_file)

        response = self._session.post(f"{self.args.server}/upload", files=files)
        for temp_file in temp_files:
            temp_file.close()
        try:
            response.raise_for_status()
            data = response.json()
        except (requests.exceptions.HTTPError, ValueError) as error:
            raise RuntimeError(f"Invalid response: {response.text}") from error

        if not isinstance(data, dict) or 'success' not in data or \
            not data['success']:
            raise RuntimeError(f"Server does not indicate success: {data}")
