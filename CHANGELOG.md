# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-06-15

### Added
- Local search index implementation for fast, reliable search
- Search index caching with configurable expiration (default 24 hours)
- Cache directory at `~/.unity_docs_mcp/cache/`
- Support for exact, prefix, and substring search matching
- Comprehensive search index tests
- Performance tests for search functionality

### Changed
- Search now uses local JavaScript index instead of web scraping
- Improved search performance (searches complete in < 0.1s)
- Search works offline after initial index download
- Better search ranking algorithm with scoring system

### Fixed
- Fixed Unity search page JavaScript execution issues
- Fixed "Searching Script Reference, please wait." loading spinner problem
- Improved error handling for search operations

## [0.1.0] - Initial Release

### Added
- Basic Unity documentation retrieval
- Search functionality via web scraping
- Support for multiple Unity versions (6000.0, 2023.x, 2022.x, 2021.3)
- Class name suggestions
- Comprehensive test suite
- MCP server implementation
- Rate limiting for respectful web scraping
- Clean markdown output with Unity-specific formatting fixes