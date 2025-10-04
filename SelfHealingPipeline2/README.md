# Self-Healing Pipeline - GitHub Repository Identifier

A comprehensive tool for analyzing public GitHub repositories to identify issues, flags, and potential problems that could benefit from automated healing.

## Features

The identifier analyzes repositories for:

- **GitHub Issues**: Open issues with severity classification
- **GitHub Actions**: Failed or cancelled workflow runs
- **Dependencies**: Dependency management files and potential issues
- **Code Quality**: Repository size, documentation, and quality metrics
- **Security**: Security vulnerabilities and alerts (with GitHub token)
- **Recent Activity**: Commit patterns that suggest ongoing issues

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Basic Usage

```python
from Identifier.identifierAdapter import identify_issues

# Analyze a repository
result = identify_issues("https://github.com/microsoft/vscode")
print(f"Found {result['total_issues']} issues and {result['total_flags']} flags")
```

### 3. Command Line Usage

```bash
# Basic analysis
python Identifier/identifierAdapter.py https://github.com/facebook/react

# Using the test script with different output formats
python test_identifier.py https://github.com/microsoft/vscode
python test_identifier.py https://github.com/torvalds/linux json
python test_identifier.py https://github.com/facebook/react summary
```

## Output Format

The identifier returns a comprehensive analysis including:

```json
{
  "repository": "owner/repo",
  "analysis_timestamp": "2024-01-01T12:00:00",
  "summary": {
    "total_issues": 5,
    "total_flags": 2,
    "severity_breakdown": {
      "high": 1,
      "medium": 3,
      "low": 1
    },
    "recommendations": [
      "Address high-severity issues immediately",
      "Fix failing GitHub Actions workflows"
    ]
  },
  "issues": [...],
  "flags": [...]
}
```

## Issue Types

- **github_issue**: Open GitHub issues
- **dependency_analysis**: Dependency management files found
- **code_quality**: Code quality concerns (large repos, missing docs)
- **security_vulnerability**: Security alerts and vulnerabilities
- **documentation**: Missing or inadequate documentation

## Flag Types

- **workflow_failure**: Failed GitHub Actions workflows
- **workflow_cancelled**: Cancelled GitHub Actions workflows
- **commit_pattern**: Recent commits suggesting bug fixes
- **security_alert**: Security-related flags

## Severity Levels

- **high**: Critical issues requiring immediate attention
- **medium**: Important issues that should be addressed
- **low**: Minor issues or suggestions
- **info**: Informational findings

## GitHub Token (Optional)

For enhanced analysis including security alerts and higher rate limits:

```bash
export GITHUB_TOKEN=your_github_token_here
```

## Examples

### Analyze a Popular Repository

```bash
python test_identifier.py https://github.com/microsoft/vscode
```

### Get JSON Output

```bash
python test_identifier.py https://github.com/facebook/react json
```

### Quick Summary

```bash
python test_identifier.py https://github.com/torvalds/linux summary
```

## Integration

The identifier is designed to be integrated into larger self-healing pipelines:

```python
from Identifier.identifierAdapter import GitHubRepositoryIdentifier

# Create identifier
identifier = GitHubRepositoryIdentifier()

# Analyze repository
result = identifier.identify_issues_and_flags("https://github.com/owner/repo")

# Process results
for issue in result['issues']:
    if issue['severity'] == 'high':
        print(f"Critical issue: {issue['title']}")

for flag in result['flags']:
    if flag['type'] == 'workflow_failure':
        print(f"Workflow failed: {flag['message']}")
```

## Limitations

- Rate limited by GitHub API (60 requests/hour without token)
- Security analysis requires GitHub token with appropriate permissions
- Analysis is based on publicly available information
- Some advanced features require specific repository permissions

## Future Enhancements

- Integration with Datadog for monitoring data
- Machine learning-based issue classification
- Automated fix suggestion generation
- Integration with CI/CD pipelines
- Real-time monitoring and alerting
