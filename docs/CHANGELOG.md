# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.2] - 2025-06-20

### Fixed
- Unity classes with namespaces (e.g., AI.NavMeshAgent, UI.Button) are now correctly found
- Improved class resolution using search index for accurate URL discovery
- Better handling of Unity classes without explicit namespace in user queries
- Fixed IndentationError in empty except blocks

### Improved  
- **Search accuracy improved from 80% to 100%** by implementing Unity's official search algorithm
- Implemented Unity's scoring system from their JavaScript search implementation
- Simplified namespace handling without hardcoded mappings
- More reliable API documentation retrieval for all Unity classes
- Better error messages suggesting namespace issues when classes are not found

### Added
- Basic functionality tests to prevent syntax/import errors
- Pre-commit hook for automatic test execution
- Test script (`run_tests.sh`) for easy testing

### Developer Experience
- Added pre-commit testing to ensure code quality
- Prevents broken code from being committed

## [0.2.1] - 2025-06-15

### Added
- Automatic property/method type detection from search index
- Type information display in search results [property], [method], [class], [constructor]
- Type-aware URL construction for optimized requests
- Support for Unity property documentation with hyphen notation

### Fixed
- Property documentation fetching (e.g., ContactPoint2D.otherRigidbody)
- Eliminated unnecessary 404 errors for properties

### Improved
- 50% reduction in HTTP requests with direct URL construction
- Search results now include member type information
- More accurate documentation retrieval for all Unity member types

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