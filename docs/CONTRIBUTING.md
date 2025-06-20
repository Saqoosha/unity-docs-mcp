# Contributing to Unity Docs MCP Server

Thank you for your interest in contributing! This document provides guidelines for contributing to the Unity Docs MCP Server project.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- [uv](https://docs.astral.sh/uv/) (recommended for development)
- Git

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/unity-docs-mcp.git
   cd unity-docs-mcp
   ```

2. **Set up the development environment:**
   ```bash
   # Create virtual environment and install dependencies
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install development dependencies
   uv pip install -r requirements-dev.txt
   uv pip install -e .
   ```

3. **Validate the setup:**
   ```bash
   python validate_structure.py
   python -m unittest discover tests -v
   ```

## Development Workflow

### 1. Code Style

We use the following tools for code quality:

- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking

Format your code before committing:
```bash
black src/ tests/
flake8 src/ tests/
mypy src/unity_docs_mcp/ --ignore-missing-imports
```

### 2. Testing

Always write tests for new features and ensure all existing tests pass:

```bash
# Run all tests with coverage
python run_tests.py

# Run specific test file
python -m unittest tests.test_parser -v

# Run search-related tests
python -m pytest tests/test_search_index.py tests/test_scraper_search.py -v

# Test search index performance
python test_search_final.py
```

### 3. Documentation

- Update docstrings for all new functions and classes
- Update the README.md if you add new features
- Add examples for new functionality

## Types of Contributions

### Bug Reports

When filing a bug report, please include:

1. **Unity version** you were trying to access
2. **Error message** or unexpected behavior
3. **Steps to reproduce** the issue
4. **Expected vs actual behavior**
5. **Environment information** (Python version, OS, etc.)
6. **Cache status** - Check if clearing `~/.unity_docs_mcp/cache/` helps

### Feature Requests

For new features, please:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** clearly
3. **Explain the expected behavior**
4. **Consider backward compatibility**

### Code Contributions

#### Areas for Contribution

1. **New Unity versions** - Add support for newer Unity versions
2. **Parser improvements** - Better HTML parsing and markdown conversion
3. **Error handling** - More robust error handling and recovery
4. **Performance** - Search index optimization, caching improvements
5. **Documentation** - Code examples, tutorials
6. **Testing** - More comprehensive test coverage
7. **Search improvements** - Better search ranking algorithm
8. **Cache management** - Smarter cache invalidation

#### Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clean, well-documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Test thoroughly:**
   ```bash
   python validate_structure.py
   python run_tests.py
   black src/ tests/
   flake8 src/ tests/
   ```

4. **Commit with clear messages:**
   ```bash
   git commit -m "Add support for Unity 2024.1 documentation
   
   - Update version list in scraper
   - Add URL patterns for new documentation structure
   - Add tests for new version support"
   ```

5. **Push and create pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

#### Pull Request Guidelines

- **Clear title** describing the change
- **Detailed description** of what was changed and why
- **Reference related issues** using "Fixes #123" or "Related to #456"
- **Include tests** for new functionality
- **Update documentation** if needed
- **Keep changes focused** - one feature per PR

## Architecture Guidelines

### Code Organization

```
src/unity_docs_mcp/
├── server.py       # MCP server implementation - main entry point
├── scraper.py      # Web scraping logic - handles HTTP requests
├── parser.py       # HTML parsing and markdown conversion
├── search_index.py # Local search index implementation
└── __init__.py     # Package initialization
```

### Design Principles

1. **Separation of concerns** - Each module has a clear responsibility
2. **Error handling** - Graceful degradation and clear error messages
3. **Rate limiting** - Respectful to Unity's servers
4. **Testability** - All components should be easily testable
5. **Extensibility** - Easy to add new Unity versions or features

### Adding New Unity Versions

To add support for a new Unity version:

1. **Update `scraper.py`:**
   ```python
   def get_supported_versions(self) -> List[str]:
       return [
           "2024.1",  # Add new version here
           "6000.0",
           "2023.3",
           # ... existing versions
       ]
   ```

2. **Test search index for new version:**
   ```python
   # Test that search index loads for new version
   def test_search_index_new_version(self):
       index = UnitySearchIndex()
       self.assertTrue(index.load_index("2024.1"))
   ```

3. **Test the new version:**
   ```python
   # Add tests in test_scraper.py
   def test_new_version_support(self):
       self.assertTrue(self.scraper.validate_version("2024.1"))
   ```

4. **Update documentation:**
   - Add the version to README.md
   - Update any version-specific examples
   - Note any changes in Unity's documentation structure

### Parser Improvements

When improving the HTML parser:

1. **Test with real Unity pages** - Use actual Unity documentation
2. **Handle edge cases** - Empty pages, malformed HTML, etc.
3. **Preserve formatting** - Maintain code blocks, tables, links
4. **Convert relative URLs** - Make all links absolute
5. **Remove Unity UI elements** - Feedback forms, navigation, etc.
6. **Fix bracket issues** - Remove `<a>` tags before Trafilatura processing

### Search Index Improvements

When working on search functionality:

1. **Download index.js** - Parse Unity's JavaScript search index
2. **Implement ranking** - Score results based on relevance
3. **Handle caching** - Cache index files with expiration
4. **Test performance** - Ensure searches are fast (< 0.1s)
5. **Support offline** - Search works after initial download

## Testing Guidelines

### Test Structure

- **Unit tests** - Test individual components in isolation
- **Integration tests** - Test component interactions
- **Mock external dependencies** - Don't hit Unity's servers in tests

### Writing Good Tests

1. **Clear test names** - Describe what is being tested
2. **Arrange, Act, Assert** - Clear test structure
3. **Test edge cases** - Empty inputs, network errors, malformed data
4. **Use mocks appropriately** - Mock external services, not internal logic

Example test:
```python
def test_parse_api_doc_with_code_blocks(self):
    """Test that code blocks are preserved in markdown conversion."""
    html_with_code = """
    <div class="content">
        <h1>Test Method</h1>
        <pre><code>public void TestMethod() { }</code></pre>
    </div>
    """
    
    result = self.parser.parse_api_doc(html_with_code, "http://test.com")
    
    self.assertIn("```", result["content"])
    self.assertIn("public void TestMethod", result["content"])
```

## Release Process

### Version Numbers

We use [Semantic Versioning](https://semver.org/):

- **MAJOR** - Breaking changes
- **MINOR** - New features, backward compatible
- **PATCH** - Bug fixes, backward compatible

### Creating a Release

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release tag
4. GitHub Actions will handle publishing

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers get started
- Assume good intentions

### Getting Help

- **GitHub Issues** - For bugs and feature requests
- **GitHub Discussions** - For questions and general discussion
- **Documentation** - Check README and code comments first

## Legal

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing to Unity Docs MCP Server! 🚀