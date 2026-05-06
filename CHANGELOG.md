# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Crossref URL encoding issues causing 404 errors
- DataCite adapter relation type filtering and confidence levels
- OpenAIRE adapter pagination, inverse lookups, and provider-based confidence scoring
- Enhanced error handling and graceful failure handling across all adapters

### Changed
- Disabled broken adapters: HEPData (403 Forbidden), MDF (404), NOMAD (unsupported API)
- Consolidated project structure: moved all development files to `ignored/` folder
- Improved README with badges, table of contents, and better documentation

### Added
- Comprehensive adapter testing and validation
- Sample output documentation
- Prerequisites section in installation
- Config.json example with annotations