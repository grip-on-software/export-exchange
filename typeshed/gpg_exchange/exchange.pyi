from types import TracebackType
from typing import Any, Callable, IO, Optional, Sequence, Tuple, Type, Union
import gpg

Passphrase = Callable[[str, str, int, Optional[Any]], str]

class Exchange:
    def __init__(self, armor: bool = True, home_dir: Optional[str] = None,
                 engine_path: Optional[str] = None,
                 passphrase: Optional[Passphrase] = None): ...
    def __enter__(self) -> 'Exchange': ...
    def __exit__(self, exc_type: Optional[Type[BaseException]],
                 exc_value: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> None: ...
    def generate_key(self, name: str, email: str,
                     comment: str = 'exchange generated key',
                     passphrase: Optional[str] = None) -> gpg.core.gpgme._gpgme_key: ...
    def find_key(self, pattern: str) -> gpg.core.gpgme._gpgme_key: ...
    def delete_key(self, pattern: str, secret: bool = False) -> gpg.core.gpgme._gpgme_key: ...
    def _get_imported_key(self, import_result: gpg.core.gpgme._gpgme_op_import_result) -> gpg.core.gpgme._gpgme_key: ...
    def import_key(self, pubkey: Union[str, bytes]) -> Tuple[gpg.core.gpgme._gpgme_key, gpg.core.gpgme._gpgme_op_import_result]: ...
    def export_key(self, pattern: str) -> Union[str, bytes]: ...
    @staticmethod
    def _read_data(data: gpg.Data) -> Union[str, bytes]: ...
    def _encrypt(self, plaintext: gpg.Data, ciphertext: gpg.Data,
                 recipients: Optional[Union[gpg.core.gpgme._gpgme_key,
                                            Sequence[gpg.core.gpgme._gpgme_key]]],
                 passphrase: Optional[Passphrase], always_trust: bool) -> None: ...
    def encrypt_text(self, data: Union[str, bytes],
                     recipients: Optional[Union[gpg.core.gpgme._gpgme_key,
                                                Sequence[gpg.core.gpgme._gpgme_key]]] = None,
                     passphrase: Optional[Passphrase] = None,
                     always_trust: bool = False) -> Union[str, bytes]: ...
    def encrypt_file(self, input_file: IO, output_file: IO,
                     recipients: Optional[Union[gpg.core.gpgme._gpgme_key,
                                                Sequence[gpg.core.gpgme._gpgme_key]]] = None,
                     passphrase: Optional[Passphrase] = None,
                     always_trust: bool = False,
                     armor: Optional[bool] = None) -> Union[str, bytes]: ...
    def _decrypt(self, ciphertext: gpg.Data, plaintext: gpg.Data,
                 passphrase: Optional[Passphrase] = None,
                 verify: bool = True) -> None: ...
    def decrypt_text(self, data: bytes, passphrase: Optional[Passphrase] = None,
                     verify: bool = True) -> Union[str, bytes]: ...
    def decrypt_file(self, input_file: IO, output_file: IO,
                     passphrase: Optional[Passphrase] = None,
                     verify: bool = True, armor: Optional[bool] = None) -> None: ...
