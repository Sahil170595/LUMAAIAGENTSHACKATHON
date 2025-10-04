#!/usr/bin/env python3
"""
Test script for the GitHub Repository Identifier
Demonstrates how to use the identifier to analyze public GitHub repositories.
"""

import sys
import json
from Identifier.identifierAdapter import GitHubRepositoryIdentifier, identify_issues

def test_identifier(repo_url: str, output_format: str = "pretty"):
    """
    Test the identifier with a GitHub repository URL.
    
    Args:
        repo_url: GitHub repository URL
        output_format: Output format ('pretty', 'json', 'summary')
    """
    print(f"🔍 Testing GitHub Repository Identifier")
    print(f"Repository: {repo_url}")
    print("-" * 60)
    
    try:
        # Create identifier instance
        identifier = GitHubRepositoryIdentifier()
        
        # Analyze the repository
        result = identifier.identify_issues_and_flags(repo_url)
        
        if output_format == "json":
            print(json.dumps(result, indent=2))
        elif output_format == "summary":
            print_summary(result)
        else:  # pretty format
            print_pretty_output(result)
            
    except Exception as e:
        print(f"❌ Error analyzing repository: {str(e)}")
        return False
    
    return True

def print_pretty_output(result: dict):
    """Print results in a pretty format."""
    print(f"\n📊 ANALYSIS RESULTS")
    print("=" * 50)
    print(f"Repository: {result['repository']}")
    print(f"Analysis Time: {result.get('analysis_timestamp', 'N/A')}")
    print(f"Total Issues: {result['total_issues']}")
    print(f"Total Flags: {result['total_flags']}")
    
    if result.get('error'):
        print(f"❌ Error: {result['error']}")
        return
    
    # Summary information
    if result.get('summary'):
        summary = result['summary']
        print(f"\n📈 SUMMARY")
        print("-" * 30)
        
        if summary.get('severity_breakdown'):
            print("Severity Breakdown:")
            for severity, count in summary['severity_breakdown'].items():
                if count > 0:
                    emoji = {"high": "🔴", "medium": "🟡", "low": "🟢", "info": "ℹ️"}.get(severity, "⚪")
                    print(f"  {emoji} {severity.capitalize()}: {count}")
        
        if summary.get('issue_types'):
            print(f"\nIssue Types:")
            for issue_type, count in summary['issue_types'].items():
                print(f"  • {issue_type}: {count}")
        
        if summary.get('flag_types'):
            print(f"\nFlag Types:")
            for flag_type, count in summary['flag_types'].items():
                print(f"  • {flag_type}: {count}")
        
        if summary.get('recommendations'):
            print(f"\n💡 RECOMMENDATIONS")
            print("-" * 30)
            for i, rec in enumerate(summary['recommendations'], 1):
                print(f"  {i}. {rec}")
    
    # Detailed issues
    if result.get('issues'):
        print(f"\n🐛 ISSUES FOUND")
        print("-" * 30)
        for issue in result['issues']:
            severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢", "info": "ℹ️"}.get(issue['severity'], "⚪")
            print(f"  {severity_emoji} [{issue['severity'].upper()}] {issue['title']}")
            print(f"     Type: {issue['type']} | Source: {issue['source']}")
            if issue.get('url'):
                print(f"     URL: {issue['url']}")
            print()
    
    # Detailed flags
    if result.get('flags'):
        print(f"\n🚩 FLAGS FOUND")
        print("-" * 30)
        for flag in result['flags']:
            severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢", "info": "ℹ️"}.get(flag['severity'], "⚪")
            print(f"  {severity_emoji} [{flag['severity'].upper()}] {flag['message']}")
            print(f"     Type: {flag['type']} | Source: {flag['source']}")
            print(f"     Timestamp: {flag['timestamp']}")
            print()

def print_summary(result: dict):
    """Print a brief summary of results."""
    print(f"Repository: {result['repository']}")
    print(f"Issues: {result['total_issues']}, Flags: {result['total_flags']}")
    
    if result.get('summary'):
        summary = result['summary']
        critical = summary.get('critical_issues', 0)
        if critical > 0:
            print(f"⚠️  {critical} critical issues found!")
        else:
            print("✅ No critical issues found")

def main():
    """Main function for testing."""
    if len(sys.argv) < 2:
        print("Usage: python test_identifier.py <github_repo_url> [output_format]")
        print("Output formats: pretty (default), json, summary")
        print("\nExamples:")
        print("  python test_identifier.py https://github.com/microsoft/vscode")
        print("  python test_identifier.py https://github.com/facebook/react json")
        print("  python test_identifier.py https://github.com/torvalds/linux summary")
        sys.exit(1)
    
    repo_url = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "pretty"
    
    if output_format not in ["pretty", "json", "summary"]:
        print("Invalid output format. Use: pretty, json, or summary")
        sys.exit(1)
    
    success = test_identifier(repo_url, output_format)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
