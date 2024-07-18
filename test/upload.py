"""
Tests for secure PGP file upload.

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
from email import message_from_bytes
from typing import Any, Optional
import unittest
from gpg_exchange import Exchange
import requests_mock
from exchange.upload import Uploader

class UploaderTest(unittest.TestCase):
    """
    Tests for client to securely upload PGP files.
    """

    # Fingerprints of GPG keys in test/sample/*.gpg from
    # https://www.ietf.org/archive/id/draft-bre-openpgp-samples-01.html
    # Alice Lovelace <alice@openpgp.example>
    server_key_fpr = 'EB85BB5FA33A75E15E944E63F231550C4F47E38E'
    # Bob Babbage <bob@openpgp.example>
    other_key_fpr = 'D1A66E1A23B182C9980F788CFBFCC82A015E7330'

    def _get_passphrase(self, hint: str, desc: str, prev_bad: int,
                        hook: Optional[Any] = None) -> str:
        # pylint: disable=unused-argument
        return 'pass'

    def setUp(self) -> None:
        args = Namespace()
        args.server = 'https://upload.test'
        args.verify = True
        args.auth = 'digest'
        args.username = 'testuser'
        args.password = 'testpass'
        args.engine = None
        args.home_dir = None
        args.keyring = ''
        args.server_key = self.server_key_fpr
        args.name = 'GROS-EX-TEST'
        args.email = 'example@org.test'
        args.passphrase = 'pass'
        args.files = ['test/sample/upload.txt']
        self.uploader = Uploader(args)

        with open('test/sample/server.gpg', encoding='utf-8') as pubkey_file:
            self.server_pubkey = pubkey_file.read()

        # Pre-generate a key so we can actually make proper encrypted responses
        self.gpg = Exchange(passphrase=self._get_passphrase)
        try:
            self.key = self.gpg.find_key(args.name)
        except KeyError:
            key = self.gpg.generate_key(args.name, args.email,
                                        comment='GROS upload key',
                                        passphrase=args.passphrase)
            self.key = self.gpg.find_key(key.fpr)
        #client_key = gpg.find_key(args.name)
        ciphertext = self.gpg.encrypt_text(self.server_pubkey, self.key,
                                           always_trust=True)

        self.request = requests_mock.Mocker()
        self.request.start()
        self.addCleanup(self.request.stop)
        self.request.post('https://upload.test/exchange', json={
            'pubkey': ciphertext.decode('utf-8') \
                if isinstance(ciphertext, bytes) else ciphertext
        })
        self.request.post('https://upload.test/upload', json={
            'success': True
        })

    def tearDown(self) -> None:
        try:
            self.gpg.delete_key(self.key.fpr, secret=True)
        except KeyError: # pragma: no cover
            pass
        try:
            self.gpg.delete_key(self.server_key_fpr)
        except KeyError: # pragma: no cover
            pass
        try:
            self.gpg.delete_key(self.other_key_fpr)
        except KeyError: # pragma: no cover
            pass
        del self.gpg

    def test_run(self) -> None:
        """
        Test performing the verified key exchange and upload of files.
        """

        self.uploader.run()
        self.assertTrue(self.request.called)
        self.assertEqual(len(self.request.request_history), 2)
        self.assertEqual(self.request.request_history[0].url,
                         'https://upload.test/exchange')
        self.assertEqual(self.request.request_history[1].url,
                         'https://upload.test/upload')

    def test_exchange(self) -> None:
        """
        Test exchanging public keys safely with the server.
        """

        key = self.uploader.exchange()
        self.assertEqual(key.fpr, self.server_key_fpr)
        self.assertTrue(self.request.called)
        if self.request.last_request is None:
            raise AssertionError('No last request')
        self.assertIn('pubkey', self.request.last_request.json())

        self.request.post('https://upload.test/exchange', status_code=500)
        with self.assertRaisesRegex(RuntimeError, 'Invalid response: .*'):
            self.uploader.exchange()

        self.request.post('https://upload.test/exchange', json={'pubkey': '?'})
        with self.assertRaisesRegex(ValueError, 'Data could not be decrypted'):
            self.uploader.exchange()

        with open('test/sample/other.gpg', encoding='utf-8') as pubkey_file:
            other_pubkey = pubkey_file.read()

        other = self.gpg.encrypt_text(other_pubkey,
                                      self.key, always_trust=True)
        self.request.post('https://upload.test/exchange', json={
            'pubkey': other.decode('utf-8') \
                if isinstance(other, bytes) else other
        })
        with self.assertRaisesRegex(RuntimeError,
                                    f'Received incorrect key: {self.other_key_fpr}'):
            self.uploader.exchange()

    def test_upload(self) -> None:
        """
        Test uploading files.
        """

        filename = 'test/sample/upload.txt'
        server_key = self.gpg.import_key(self.server_pubkey)[0]
        self.uploader.upload(server_key, [filename])
        self.assertTrue(self.request.called)
        if self.request.last_request is None:
            raise AssertionError('No last request')

        # Parse the request body to check proper multipart form data.
        body: bytes = b'Content-Type: ' + \
            self.request.last_request.headers['Content-Type'].encode('utf-8') + \
            b'\r\n\r\n' + self.request.last_request.body
        message = message_from_bytes(body)
        self.assertTrue(message.is_multipart())
        parts = 0
        for part in message.walk():
            header = part.get('Content-Disposition')
            if header is None:
                continue

            parts += 1
            self.assertEqual(header,
                             f'form-data; name="files"; filename="{filename}"')
            self.assertEqual(part.get('Content-Type'),
                             self.uploader.PGP_BINARY_MIME)

        self.assertEqual(parts, 1)

        self.request.post('https://upload.test/upload', status_code=500)
        with self.assertRaisesRegex(RuntimeError, 'Invalid response: .*'):
            self.uploader.upload(server_key, [filename])

        self.request.post('https://upload.test/upload', json={'success': False})
        with self.assertRaisesRegex(RuntimeError,
                                    'Server does not indicate success: .*'):
            self.uploader.upload(server_key, [filename])
