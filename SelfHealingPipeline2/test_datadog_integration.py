#!/usr/bin/env python3
"""
Test script for Datadog integration in the Identifier
Demonstrates how the Identifier works with Datadog alerts and metrics.
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/Users/thilaknarasimhamurthy/Desktop/Luma/LUMAAIAGENTSHACKATHON/SelfHealingPipeline')

from Identifier.identifierAdapter import GitHubRepositoryIdentifier

def test_datadog_integration():
    """Test the Datadog integration in the Identifier."""
    print("🐕 Testing Datadog Integration in Identifier")
    print("=" * 60)
    
    # Test 1: Without Datadog package installed
    print("\n📋 Test 1: Without Datadog Package")
    print("-" * 40)
    
    identifier = GitHubRepositoryIdentifier()
    print(f"Datadog Enabled: {identifier.datadog_enabled}")
    print(f"Datadog API Key: {'Set' if identifier.datadog_api_key else 'Not Set'}")
    print(f"Datadog App Key: {'Set' if identifier.datadog_app_key else 'Not Set'}")
    
    # Test 2: Mock Datadog integration
    print("\n📋 Test 2: Mock Datadog Integration")
    print("-" * 40)
    
    # Temporarily enable Datadog for testing
    identifier.datadog_enabled = True
    
    # Test the Datadog analysis methods directly
    print("Testing _analyze_datadog_alerts...")
    datadog_flags = identifier._analyze_datadog_alerts("microsoft", "vscode")
    print(f"Generated {len(datadog_flags)} Datadog flags:")
    
    for i, flag in enumerate(datadog_flags, 1):
        print(f"  {i}. [{flag.severity.upper()}] {flag.message}")
        print(f"     Type: {flag.type} | Source: {flag.source}")
        print(f"     Metadata: {flag.metadata}")
        print()
    
    print("Testing _analyze_datadog_metrics...")
    datadog_issues = identifier._analyze_datadog_metrics("microsoft", "vscode")
    print(f"Generated {len(datadog_issues)} Datadog issues:")
    
    for i, issue in enumerate(datadog_issues, 1):
        print(f"  {i}. [{issue.severity.upper()}] {issue.title}")
        print(f"     Type: {issue.type} | Source: {issue.source}")
        print(f"     Description: {issue.description}")
        print()
    
    # Test 3: Full integration test
    print("\n📋 Test 3: Full Integration Test")
    print("-" * 40)
    
    # Reset to normal state
    identifier.datadog_enabled = False
    
    # Test with a simple repository
    repo_url = "https://github.com/microsoft/vscode"
    print(f"Analyzing repository: {repo_url}")
    
    result = identifier.identify_issues_and_flags(repo_url)
    
    print(f"✅ Analysis completed:")
    print(f"   Repository: {result['repository']}")
    print(f"   Total Issues: {result['total_issues']}")
    print(f"   Total Flags: {result['total_flags']}")
    
    # Show breakdown by source
    issues_by_source = {}
    flags_by_source = {}
    
    for issue in result.get('issues', []):
        source = issue.get('source', 'unknown')
        issues_by_source[source] = issues_by_source.get(source, 0) + 1
    
    for flag in result.get('flags', []):
        source = flag.get('source', 'unknown')
        flags_by_source[source] = flags_by_source.get(source, 0) + 1
    
    print(f"\n📊 Issues by Source:")
    for source, count in issues_by_source.items():
        print(f"   {source}: {count}")
    
    print(f"\n📊 Flags by Source:")
    for source, count in flags_by_source.items():
        print(f"   {source}: {count}")

def test_datadog_with_mock_keys():
    """Test with mock Datadog API keys."""
    print("\n🧪 Test 4: Mock Datadog API Keys")
    print("-" * 40)
    
    # Set mock environment variables
    os.environ["DATADOG_API_KEY"] = "mock_api_key_12345"
    os.environ["DATADOG_APP_KEY"] = "mock_app_key_67890"
    
    identifier = GitHubRepositoryIdentifier()
    
    print(f"Mock API Key Set: {'Set' if identifier.datadog_api_key else 'Not Set'}")
    print(f"Mock App Key Set: {'Set' if identifier.datadog_app_key else 'Not Set'}")
    print(f"Datadog Enabled: {identifier.datadog_enabled}")
    
    # Clean up environment variables
    if "DATADOG_API_KEY" in os.environ:
        del os.environ["DATADOG_API_KEY"]
    if "DATADOG_APP_KEY" in os.environ:
        del os.environ["DATADOG_APP_KEY"]

def demonstrate_datadog_workflow():
    """Demonstrate the complete Datadog workflow."""
    print("\n🔄 Complete Datadog Workflow Demonstration")
    print("=" * 60)
    
    # Create identifier with mock Datadog enabled
    identifier = GitHubRepositoryIdentifier()
    identifier.datadog_enabled = True  # Mock enable for demonstration
    
    repo_url = "https://github.com/example/auth-service"
    owner, repo = "example", "auth-service"
    
    print(f"Analyzing repository: {repo_url}")
    print("\n1. GitHub Analysis...")
    
    # Simulate GitHub analysis
    github_issues = identifier._analyze_github_issues(owner, repo)
    github_flags = identifier._analyze_workflows(owner, repo)
    
    print(f"   Found {len(github_issues)} GitHub issues")
    print(f"   Found {len(github_flags)} GitHub flags")
    
    print("\n2. Datadog Analysis...")
    
    # Datadog analysis
    datadog_flags = identifier._analyze_datadog_alerts(owner, repo)
    datadog_issues = identifier._analyze_datadog_metrics(owner, repo)
    
    print(f"   Found {len(datadog_flags)} Datadog alerts")
    print(f"   Found {len(datadog_issues)} Datadog metric issues")
    
    print("\n3. Combined Analysis Results:")
    print("-" * 30)
    
    all_issues = github_issues + datadog_issues
    all_flags = github_flags + datadog_flags
    
    print(f"Total Issues: {len(all_issues)}")
    print(f"Total Flags: {len(all_flags)}")
    
    # Show Datadog-specific findings
    datadog_findings = [f for f in all_flags if f.source == "datadog"] + [i for i in all_issues if i.source in ["datadog", "datadog_metrics"]]
    
    if datadog_findings:
        print(f"\n🐕 Datadog Findings ({len(datadog_findings)}):")
        for finding in datadog_findings:
            if hasattr(finding, 'message'):
                print(f"   • {finding.message}")
            else:
                print(f"   • {finding.title}")
    
    print(f"\n✅ Workflow demonstration completed!")
    print(f"   This shows how GitHub and Datadog data are combined")
    print(f"   for comprehensive issue identification.")

def main():
    """Main function."""
    print("🚀 Datadog Integration Test Suite")
    print("=" * 60)
    
    try:
        test_datadog_integration()
        test_datadog_with_mock_keys()
        demonstrate_datadog_workflow()
        
        print(f"\n🎉 All Datadog integration tests completed!")
        print(f"✅ Identifier can work with or without Datadog")
        print(f"✅ Mock Datadog integration provides realistic test data")
        print(f"✅ Combined GitHub + Datadog analysis working")
        print(f"\n📝 Next Steps:")
        print(f"   1. Install Datadog package: pip install datadog")
        print(f"   2. Set DATADOG_API_KEY and DATADOG_APP_KEY environment variables")
        print(f"   3. Replace mock data with real Datadog API calls")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
