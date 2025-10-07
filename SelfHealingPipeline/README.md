# Self-Healing Pipeline

A comprehensive self-healing application that analyzes GitHub repositories, identifies issues and flags, and integrates with Datadog for monitoring and visualization.

## 🚀 Features

- **GitHub Repository Analysis**: Identifies issues, flags, and potential problems
- **Datadog Integration**: Sends metrics and events to Datadog dashboard
- **Rate-Limited Analysis**: Works within GitHub's API limits
- **Real-time Monitoring**: Live dashboard with health scores and metrics

## 📁 Project Structure

```
SelfHealingPipeline/
├── config.py                    # Configuration file
├── requirements.txt             # Python dependencies
├── README.md                   # This file
├── Identifier/
│   ├── identifierAdapter.py    # Main identifier component
│   └── test_identifier.py     # Test script
├── Executioner/               # Sandbox testing (future)
└── Rectifier/                 # Production fixes (future)
```

## 🛠️ Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `config.py` with your API keys:

```python
# GitHub API Configuration
GITHUB_TOKEN = "your_github_token_here"  # Optional

# Datadog API Configuration  
DATADOG_API_KEY = "your_datadog_api_key_here"
DATADOG_APP_KEY = "your_datadog_app_key_here"
```

### 3. Run Analysis

```bash
# Basic analysis
python Identifier/test_identifier.py https://github.com/owner/repo

# Different output formats
python Identifier/test_identifier.py https://github.com/owner/repo json
python Identifier/test_identifier.py https://github.com/owner/repo summary
```

## 📊 Datadog Dashboard

The identifier automatically sends data to your Datadog dashboard:

- **Repository Health Score**: 0-100 health rating
- **Total Issues**: Number of identified issues
- **Total Flags**: Number of monitoring flags
- **Severity Breakdown**: High/Medium/Low issue counts

### Dashboard URL
Your dashboard is available at: `https://app.datadoghq.com/dashboard/zk8-v5f-ga8/self-healing-analysis---sahil170595banterblogs`

## 🔧 Configuration

### GitHub Token (Optional)
- **Without Token**: 60 requests/hour (rate limited)
- **With Token**: 5,000 requests/hour + security alerts
- **Get Token**: https://github.com/settings/tokens

### Datadog Keys (Required)
- **API Key**: https://app.datadoghq.com/organization-settings/api-keys
- **App Key**: https://app.datadoghq.com/organization-settings/application-keys

## 📈 Output Format

```json
{
  "repository": "owner/repo",
  "analysis_timestamp": "2024-01-01T12:00:00",
  "summary": {
    "total_issues": 3,
    "total_flags": 1,
    "severity_breakdown": {
      "high": 0,
      "medium": 2,
      "low": 1
    },
    "recommendations": [
      "Address medium-severity issues",
      "Repository appears healthy overall"
    ]
  },
  "issues": [...],
  "flags": [...]
}
```

## 🎯 Usage Examples

### Python Integration

```python
from Identifier.identifierAdapter import GitHubRepositoryIdentifier

# Create identifier
identifier = GitHubRepositoryIdentifier()

# Analyze repository
result = identifier.identify_issues_and_flags("https://github.com/owner/repo")

# Process results
print(f"Health Score: {100 - result['total_issues'] * 5}")
print(f"Issues Found: {result['total_issues']}")
print(f"Flags Found: {result['total_flags']}")
```

### Command Line

```bash
# Analyze any public repository
python Identifier/test_identifier.py https://github.com/microsoft/vscode

# Get JSON output for integration
python Identifier/test_identifier.py https://github.com/facebook/react json

# Quick summary
python Identifier/test_identifier.py https://github.com/torvalds/linux summary
```

## 🔍 Analysis Types

### Issues Identified
- **GitHub Issues**: Open issues with severity classification
- **Dependencies**: Dependency management files and analysis
- **Code Quality**: Repository size, documentation, structure
- **Security**: Vulnerabilities and security alerts

### Flags Detected
- **Workflow Failures**: Failed GitHub Actions
- **Commit Patterns**: Recent commits suggesting issues
- **Rate Limiting**: API limit warnings
- **Security Alerts**: Security-related flags

## 🚀 Future Enhancements

- **Executioner Component**: Sandbox testing of fixes
- **Rectifier Component**: Production fix application
- **Machine Learning**: AI-powered issue classification
- **Automated Fixes**: Self-healing capabilities
- **Real-time Monitoring**: Continuous analysis

## 📝 License

This project is part of the AI Agents Hackathon at NYU.