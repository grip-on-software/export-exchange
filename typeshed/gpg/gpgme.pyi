from typing import List

class _gpgme_key:
    fpr: str = ...

class _gpgme_import_status:
    fpr: str = ...

class _gpgme_op_import_result:
    considered: int = ...
    imported: int = ...
    imports: List[_gpgme_import_status] = ...
