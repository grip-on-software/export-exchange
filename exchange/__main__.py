"""
Entry point for secure PGP file upload.

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

from configparser import RawConfigParser
import logging
import os
from .args import parse_args
from .upload import Uploader

def main() -> None:
    """
    Main entry point.
    """

    if 'GATHERER_SETTINGS_FILE' in os.environ:
        config_file = os.environ['GATHERER_SETTINGS_FILE']
    else:
        config_file = 'settings.cfg'

    config = RawConfigParser()
    config.read(config_file)
    args = parse_args(config)

    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
                        level=getattr(logging, args.log.upper(), None))

    uploader = Uploader(args)
    uploader.run()

if __name__ == "__main__":
    main()
