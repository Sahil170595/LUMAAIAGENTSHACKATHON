#!/usr/bin/env python3
"""
GitHub Repository Issue Identifier
Analyzes public GitHub repositories to identify issues, flags, and potential problems.
"""

import os
import requests
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Issue:
    """Represents an identified issue."""
    id: str
    type: str
    severity: str
    title: str
    description: str
    source: str  # 'github', 'workflow', 'dependencies', 'code_quality'
    url: Optional[str] = None
    created_at: Optional[str] = None
    labels: List[str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []

@dataclass
class Flag:
    """Represents a monitoring flag or alert."""
    id: str
    type: str
    severity: str
    message: str
    source: str  # 'datadog', 'github_actions', 'dependencies'
    timestamp: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class GitHubRepositoryIdentifier:
    """
    Identifies issues and flags in GitHub repositories by analyzing:
    - Open issues and pull requests
    - GitHub Actions workflow runs
    - Dependencies and security vulnerabilities
    - Code quality metrics
    - Recent commits and changes
    """
    
    def __init__(self, github_token: Optional[str] = None, datadog_api_key: Optional[str] = None, datadog_app_key: Optional[str] = None):
        # Try to load from config file first
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from config import GITHUB_TOKEN as CONFIG_GITHUB_TOKEN, DATADOG_API_KEY as CONFIG_DATADOG_API_KEY, DATADOG_APP_KEY as CONFIG_DATADOG_APP_KEY
            
            self.github_token = github_token or CONFIG_GITHUB_TOKEN or os.getenv("GITHUB_TOKEN")
            self.datadog_api_key = datadog_api_key or CONFIG_DATADOG_API_KEY or os.getenv("DATADOG_API_KEY")
            self.datadog_app_key = datadog_app_key or CONFIG_DATADOG_APP_KEY or os.getenv("DATADOG_APP_KEY")
        except ImportError:
            # Fallback to environment variables
            self.github_token = github_token or os.getenv("GITHUB_TOKEN")
            self.datadog_api_key = datadog_api_key or os.getenv("DATADOG_API_KEY")
            self.datadog_app_key = datadog_app_key or os.getenv("DATADOG_APP_KEY")
        self.session = requests.Session()
        
        if self.github_token and self.github_token != "your_github_token_here":
            self.session.headers.update({
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            })
            logger.info("GitHub token loaded successfully")
        else:
            self.session.headers.update({
                "Accept": "application/vnd.github.v3+json"
            })
            logger.warning("No valid GitHub token provided. Rate limits may apply.")
        
        # Initialize Datadog if keys are provided
        if self.datadog_api_key and self.datadog_app_key and self.datadog_api_key != "your_datadog_api_key_here":
            try:
                from datadog import initialize
                initialize(
                    api_key=self.datadog_api_key,
                    app_key=self.datadog_app_key
                )
                logger.info("Datadog integration initialized successfully")
            except ImportError:
                logger.warning("Datadog package not installed. Install with: pip install datadog")
            except Exception as e:
                logger.warning(f"Failed to initialize Datadog: {e}")
        else:
            logger.info("No valid Datadog credentials provided. Skipping Datadog integration.")
    
    def identify_issues_and_flags(self, repo_url: str) -> Dict[str, Any]:
        """
        Main entry point to identify issues and flags in a GitHub repository.
        
        Args:
            repo_url: GitHub repository URL (e.g., https://github.com/owner/repo)
            
        Returns:
            Dictionary containing identified issues and flags
        """
        try:
            owner, repo = self._parse_github_url(repo_url)
            logger.info(f"🔍 Analyzing repository: {owner}/{repo}")
            
            # Collect all data
            issues = []
            flags = []
            
            # Determine analysis strategy based on rate limits
            has_token = self.github_token and self.github_token != "your_github_token_here"
            
            if has_token:
                logger.info("GitHub token detected - running full analysis")
                # Full analysis with token (5,000 requests/hour)
                github_issues = self._analyze_github_issues(owner, repo)
                issues.extend(github_issues)
                
                workflow_flags = self._analyze_workflows(owner, repo)
                flags.extend(workflow_flags)
                
                dependency_issues = self._analyze_dependencies(owner, repo)
                issues.extend(dependency_issues)
                
                commit_flags = self._analyze_recent_commits(owner, repo)
                flags.extend(commit_flags)
                
                quality_issues = self._analyze_code_quality(owner, repo)
                issues.extend(quality_issues)
                
                security_issues = self._analyze_security(owner, repo)
                issues.extend(security_issues)
            else:
                logger.info("No GitHub token - running limited analysis (max 1 request)")
                # Limited analysis without token (1 request only)
                # Only analyze dependencies (no API calls needed)
                dependency_issues = self._analyze_dependencies(owner, repo)
                issues.extend(dependency_issues)
            
            # Generate summary
            summary = self._generate_summary(owner, repo, issues, flags)
            
            # Prepare result
            result = {
                "repository": f"{owner}/{repo}",
                "analysis_timestamp": datetime.now().isoformat(),
                "summary": summary,
                "issues": [asdict(issue) for issue in issues],
                "flags": [asdict(flag) for flag in flags],
                "total_issues": len(issues),
                "total_flags": len(flags)
            }
            
            # Send to Datadog dashboard if configured
            if self.datadog_api_key and self.datadog_app_key and self.datadog_api_key != "your_datadog_api_key_here":
                try:
                    # Send metrics directly to Datadog
                    self._send_metrics_to_datadog(result, f"{owner}/{repo}")
                    logger.info("Analysis data sent to Datadog dashboard")
                except Exception as e:
                    logger.warning(f"Failed to send to Datadog dashboard: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze repository {repo_url}: {str(e)}")
            return {
                "repository": repo_url,
                "error": str(e),
                "issues": [],
                "flags": [],
                "total_issues": 0,
                "total_flags": 0
            }
    
    def _parse_github_url(self, repo_url: str) -> tuple[str, str]:
        """Parse GitHub URL to extract owner and repository name."""
        try:
            path = urlparse(repo_url).path.strip("/")
            parts = path.split("/")
            if len(parts) < 2:
                raise ValueError("Invalid GitHub URL format")
            return parts[0], parts[1]
        except Exception as e:
            raise ValueError(f"Invalid GitHub repo URL: {repo_url}") from e
    
    def _analyze_github_issues(self, owner: str, repo: str) -> List[Issue]:
        """Analyze open GitHub issues."""
        issues = []
        
        try:
            # Get open issues
            response = self.session.get(f"https://api.github.com/repos/{owner}/{repo}/issues")
            response.raise_for_status()
            github_issues = response.json()
            
            for issue_data in github_issues:
                # Skip pull requests (they have pull_request field)
                if "pull_request" in issue_data:
                    continue
                
                severity = self._determine_issue_severity(issue_data)
                
                issue = Issue(
                    id=f"gh_issue_{issue_data['number']}",
                    type="github_issue",
                    severity=severity,
                    title=issue_data["title"],
                    description=issue_data["body"] or "No description",
                    source="github",
                    url=issue_data["html_url"],
                    created_at=issue_data["created_at"],
                    labels=[label["name"] for label in issue_data.get("labels", [])]
                )
                issues.append(issue)
                
        except Exception as e:
            logger.error(f"Failed to analyze GitHub issues: {str(e)}")
        
        return issues
    
    def _analyze_workflows(self, owner: str, repo: str) -> List[Flag]:
        """Analyze GitHub Actions workflow runs."""
        flags = []
        
        try:
            # Get recent workflow runs
            response = self.session.get(f"https://api.github.com/repos/{owner}/{repo}/actions/runs")
            response.raise_for_status()
            workflow_data = response.json()
            
            for run in workflow_data.get("workflow_runs", [])[:10]:  # Last 10 runs
                if run["conclusion"] == "failure":
                    flag = Flag(
                        id=f"workflow_failure_{run['id']}",
                        type="workflow_failure",
                        severity="high",
                        message=f"Workflow '{run['name']}' failed",
                        source="github_actions",
                        timestamp=run["created_at"],
                        metadata={
                            "workflow_name": run["name"],
                            "run_id": run["id"],
                            "conclusion": run["conclusion"],
                            "url": run["html_url"]
                        }
                    )
                    flags.append(flag)
                elif run["conclusion"] == "cancelled":
                    flag = Flag(
                        id=f"workflow_cancelled_{run['id']}",
                        type="workflow_cancelled",
                        severity="medium",
                        message=f"Workflow '{run['name']}' was cancelled",
                        source="github_actions",
                        timestamp=run["created_at"],
                        metadata={
                            "workflow_name": run["name"],
                            "run_id": run["id"],
                            "conclusion": run["conclusion"]
                        }
                    )
                    flags.append(flag)
                    
        except Exception as e:
            logger.error(f"Failed to analyze workflows: {str(e)}")
        
        return flags
    
    def _analyze_dependencies(self, owner: str, repo: str) -> List[Issue]:
        """Analyze dependency issues."""
        issues = []
        
        try:
            # Check for dependency files
            dependency_files = ["package.json", "requirements.txt", "Pipfile", "composer.json", "pom.xml"]
            
            for dep_file in dependency_files:
                try:
                    response = self.session.get(f"https://api.github.com/repos/{owner}/{repo}/contents/{dep_file}")
                    if response.status_code == 200:
                        # File exists, could analyze dependencies here
                        # For now, just note that dependencies exist
                        issue = Issue(
                            id=f"deps_{dep_file}",
                            type="dependency_analysis",
                            severity="info",
                            title=f"Dependency file found: {dep_file}",
                            description=f"Repository uses {dep_file} for dependency management",
                            source="dependencies"
                        )
                        issues.append(issue)
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to analyze dependencies: {str(e)}")
        
        return issues
    
    def _analyze_recent_commits(self, owner: str, repo: str) -> List[Flag]:
        """Analyze recent commits for potential issues."""
        flags = []
        
        try:
            # Get recent commits with rate limiting
            response = self.session.get(f"https://api.github.com/repos/{owner}/{repo}/commits")
            
            # Handle rate limiting
            if response.status_code == 403 and "rate limit exceeded" in response.text.lower():
                logger.warning("GitHub rate limit exceeded. Skipping commit analysis.")
                return flags
            
            response.raise_for_status()
            commits = response.json()
            
            for commit in commits[:5]:  # Last 5 commits
                commit_message = commit["commit"]["message"].lower()
                
                # Look for concerning patterns in commit messages
                if any(keyword in commit_message for keyword in ["fix", "bug", "error", "issue", "hotfix"]):
                    flag = Flag(
                        id=f"commit_{commit['sha'][:7]}",
                        type="commit_pattern",
                        severity="medium",
                        message=f"Recent commit suggests bug fix: {commit['commit']['message'][:50]}...",
                        source="commits",
                        timestamp=commit["commit"]["author"]["date"],
                        metadata={
                            "commit_sha": commit["sha"],
                            "author": commit["commit"]["author"]["name"],
                            "message": commit["commit"]["message"]
                        }
                    )
                    flags.append(flag)
                    
        except Exception as e:
            logger.error(f"Failed to analyze commits: {str(e)}")
        
        return flags
    
    def _analyze_code_quality(self, owner: str, repo: str) -> List[Issue]:
        """Analyze code quality metrics."""
        issues = []
        
        try:
            # Get repository information with rate limiting
            response = self.session.get(f"https://api.github.com/repos/{owner}/{repo}")
            
            # Handle rate limiting
            if response.status_code == 403 and "rate limit exceeded" in response.text.lower():
                logger.warning("GitHub rate limit exceeded. Skipping code quality analysis.")
                return issues
            
            response.raise_for_status()
            repo_data = response.json()
            
            # Check for common code quality indicators
            if repo_data.get("size", 0) > 100000:  # Large repository
                issue = Issue(
                    id="large_repo",
                    type="code_quality",
                    severity="medium",
                    title="Large repository size",
                    description=f"Repository size is {repo_data['size']} KB, consider modularization",
                    source="code_quality"
                )
                issues.append(issue)
            
            # Check for README
            try:
                readme_response = self.session.get(f"https://api.github.com/repos/{owner}/{repo}/readme")
                if readme_response.status_code != 200:
                    issue = Issue(
                        id="no_readme",
                        type="documentation",
                        severity="low",
                        title="Missing README",
                        description="Repository lacks a README file",
                        source="code_quality"
                    )
                    issues.append(issue)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Failed to analyze code quality: {str(e)}")
        
        return issues
    
    def _analyze_security(self, owner: str, repo: str) -> List[Issue]:
        """Analyze security-related issues."""
        issues = []
        
        try:
            # Check for security advisories (requires GitHub token with security permissions)
            if self.github_token:
                try:
                    response = self.session.get(f"https://api.github.com/repos/{owner}/{repo}/dependabot/alerts")
                    if response.status_code == 200:
                        alerts = response.json()
                        for alert in alerts:
                            issue = Issue(
                                id=f"security_{alert['number']}",
                                type="security_vulnerability",
                                severity="high",
                                title=f"Security alert: {alert['security_advisory']['summary']}",
                                description=alert["security_advisory"]["description"],
                                source="security",
                                url=alert["html_url"]
                            )
                            issues.append(issue)
                except:
                    pass  # Security alerts might not be available
                    
        except Exception as e:
            logger.error(f"Failed to analyze security: {str(e)}")
        
        return issues
    
    def _determine_issue_severity(self, issue_data: Dict) -> str:
        """Determine issue severity based on labels and content."""
        labels = [label["name"].lower() for label in issue_data.get("labels", [])]
        
        if any(severity in labels for severity in ["critical", "urgent", "high", "bug"]):
            return "high"
        elif any(severity in labels for severity in ["medium", "enhancement", "feature"]):
            return "medium"
        else:
            return "low"
    
    def _generate_summary(self, owner: str, repo: str, issues: List[Issue], flags: List[Flag]) -> Dict[str, Any]:
        """Generate a summary of the analysis."""
        issue_types = {}
        flag_types = {}
        severity_counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
        
        for issue in issues:
            issue_types[issue.type] = issue_types.get(issue.type, 0) + 1
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        for flag in flags:
            flag_types[flag.type] = flag_types.get(flag.type, 0) + 1
            severity_counts[flag.severity] = severity_counts.get(flag.severity, 0) + 1
        
        return {
            "repository": f"{owner}/{repo}",
            "total_issues": len(issues),
            "total_flags": len(flags),
            "issue_types": issue_types,
            "flag_types": flag_types,
            "severity_breakdown": severity_counts,
            "critical_issues": severity_counts.get("high", 0),
            "recommendations": self._generate_recommendations(issues, flags)
        }
    
    def _generate_recommendations(self, issues: List[Issue], flags: List[Flag]) -> List[str]:
        """Generate recommendations based on identified issues."""
        recommendations = []
        
        high_severity_issues = [i for i in issues if i.severity == "high"]
        if high_severity_issues:
            recommendations.append("Address high-severity issues immediately")
        
        workflow_failures = [f for f in flags if f.type == "workflow_failure"]
        if workflow_failures:
            recommendations.append("Fix failing GitHub Actions workflows")
        
        security_issues = [i for i in issues if i.type == "security_vulnerability"]
        if security_issues:
            recommendations.append("Review and fix security vulnerabilities")
        
        if not issues and not flags:
            recommendations.append("Repository appears healthy with no critical issues")
        
        return recommendations
    
    def _send_metrics_to_datadog(self, result: Dict, repository: str):
        """Send metrics directly to Datadog API."""
        try:
            import requests
            
            # Prepare metrics data
            timestamp = int(time.time())
            total_issues = result.get('total_issues', 0)
            total_flags = result.get('total_flags', 0)
            
            # Calculate health score
            health_score = 100 - (total_issues * 5) - (total_flags * 3)
            health_score = max(health_score, 0)
            
            # Prepare metrics
            metrics_data = {
                "series": [
                    {
                        "metric": "self_healing.repository.health_score",
                        "points": [[timestamp, health_score]],
                        "tags": [f"repo:{repository}"],
                        "type": "gauge"
                    },
                    {
                        "metric": "self_healing.repository.issues_count",
                        "points": [[timestamp, total_issues]],
                        "tags": [f"repo:{repository}"],
                        "type": "gauge"
                    },
                    {
                        "metric": "self_healing.repository.flags_count",
                        "points": [[timestamp, total_flags]],
                        "tags": [f"repo:{repository}"],
                        "type": "gauge"
                    }
                ]
            }
            
            # Add severity breakdown if available
            if result.get('summary'):
                summary = result['summary']
                severity_breakdown = summary.get('severity_breakdown', {})
                
                for severity, count in severity_breakdown.items():
                    if count > 0:
                        metrics_data["series"].append({
                            "metric": f"self_healing.repository.{severity}_issues",
                            "points": [[timestamp, count]],
                            "tags": [f"repo:{repository}", f"severity:{severity}"],
                            "type": "gauge"
                        })
            
            # Send to Datadog API
            url = "https://api.datadoghq.com/api/v1/series"
            headers = {
                "Content-Type": "application/json",
                "DD-API-KEY": self.datadog_api_key,
                "DD-APPLICATION-KEY": self.datadog_app_key
            }
            
            response = requests.post(url, headers=headers, json=metrics_data)
            
            if response.status_code == 202:
                logger.info(f"Metrics sent to Datadog: {total_issues} issues, {total_flags} flags, health: {health_score}")
            else:
                logger.warning(f"Failed to send metrics: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending metrics to Datadog: {e}")

# Convenience function for backward compatibility
def identify_issues(repo_url: str) -> Dict[str, Any]:
    """
    Convenience function to identify issues in a GitHub repository.
    
    Args:
        repo_url: GitHub repository URL
        
    Returns:
        Dictionary containing identified issues and flags
    """
    identifier = GitHubRepositoryIdentifier()
    return identifier.identify_issues_and_flags(repo_url)

# Main execution for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python identifierAdapter.py <github_repo_url>")
        sys.exit(1)
    
    repo_url = sys.argv[1]
    result = identify_issues(repo_url)
    
    print("\n" + "="*50)
    print("REPOSITORY ANALYSIS RESULTS")
    print("="*50)
    print(f"Repository: {result['repository']}")
    print(f"Total Issues: {result['total_issues']}")
    print(f"Total Flags: {result['total_flags']}")
    
    if result.get('summary'):
        summary = result['summary']
        print(f"\nSeverity Breakdown:")
        for severity, count in summary['severity_breakdown'].items():
            if count > 0:
                print(f"  {severity.capitalize()}: {count}")
        
        if summary.get('recommendations'):
            print(f"\nRecommendations:")
            for i, rec in enumerate(summary['recommendations'], 1):
                print(f"  {i}. {rec}")
    
    if result.get('issues'):
        print(f"\nIssues Found:")
        for issue in result['issues']:
            print(f"  - [{issue['severity'].upper()}] {issue['title']} ({issue['type']})")
    
    if result.get('flags'):
        print(f"\nFlags Found:")
        for flag in result['flags']:
            print(f"  - [{flag['severity'].upper()}] {flag['message']} ({flag['type']})")
