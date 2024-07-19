# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) 
and we adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Unit tests added.
- Optional `keyring` dependency can be installed with the extra `keyring`, 
  using `pip install gros-export-exchange[keyring]`.

### Changed

- The entry point of the program is now a Python script `gros-export-exchange` 
  after installation instead of a singular file.

### Fixed

- Unexpected data types (binary or Unicode-encoded strings) from internal GPG 
  methods are handled better.
- Upload left temporary files that were not closed.

## [0.0.3] - 2024-07-18

### Added

- Initial release of version as used during the GROS research project. 
  Previously, versions were rolling releases based on Git commits.

[Unreleased]: 
https://github.com/grip-on-software/export-exchange/compare/v0.0.3...HEAD
[0.0.3]: 
https://github.com/grip-on-software/export-exchange/releases/tag/v0.0.3
