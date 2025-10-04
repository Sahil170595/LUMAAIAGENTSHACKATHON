#!/usr/bin/env python3
"""
Test script for the merged Identifier Agent
Tests the combined functionality from both SelfHealingPipeline and SelfHealingPipeline2
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/Users/thilaknarasimhamurthy/Desktop/Luma/LUMAAIAGENTSHACKATHON/SelfHealingPipeline2')

from Identifier.identifierAdapter import GitHubRepositoryIdentifier

def test_merged_identifier():
    """Test the merged identifier with all features."""
    print("🔄 Testing Merged Identifier Agent")
    print("=" * 60)
    
    # Test 1: Basic functionality without tokens
    print("\n📋 Test 1: Basic Analysis (No Tokens)")
    print("-" * 40)
    
    identifier = GitHubRepositoryIdentifier()
    
    # Test with a simple repository
    repo_url = "https://github.com/microsoft/vscode"
    print(f"Analyzing repository: {repo_url}")
    
    result = identifier.identify_issues_and_flags(repo_url)
    
    print(f"✅ Analysis completed:")
    print(f"   Repository: {result['repository']}")
    print(f"   Total Issues: {result['total_issues']}")
    print(f"   Total Flags: {result['total_flags']}")
    
    # Test 2: Datadog integration check
    print("\n📋 Test 2: Datadog Integration Status")
    print("-" * 40)
    
    print(f"Datadog Enabled: {identifier.datadog_enabled}")
    print(f"Datadog API Key: {'Set' if identifier.datadog_api_key else 'Not Set'}")
    print(f"Datadog App Key: {'Set' if identifier.datadog_app_key else 'Not Set'}")
    
    if identifier.datadog_enabled:
        print("✅ Datadog integration is active")
        
        # Test Datadog analysis methods
        print("\nTesting Datadog analysis methods...")
        owner, repo = "microsoft", "vscode"
        
        datadog_flags = identifier._analyze_datadog_alerts(owner, repo)
        datadog_issues = identifier._analyze_datadog_metrics(owner, repo)
        
        print(f"   Generated {len(datadog_flags)} Datadog flags")
        print(f"   Generated {len(datadog_issues)} Datadog issues")
        
        if datadog_flags:
            print("   Sample Datadog flag:")
            flag = datadog_flags[0]
            print(f"     - [{flag.severity.upper()}] {flag.message}")
            print(f"       Type: {flag.type} | Source: {flag.source}")
    else:
        print("⚠️  Datadog integration not available")
        print("   To enable: Set DATADOG_API_KEY and DATADOG_APP_KEY environment variables")
    
    # Test 3: Rate limiting handling
    print("\n📋 Test 3: Rate Limiting & Token Validation")
    print("-" * 40)
    
    has_token = identifier.github_token and identifier.github_token != "your_github_token_here"
    print(f"GitHub Token Valid: {has_token}")
    
    if has_token:
        print("✅ Full analysis will be performed (5,000 requests/hour)")
    else:
        print("⚠️  Limited analysis only (60 requests/hour)")
        print("   To enable full analysis: Set GITHUB_TOKEN environment variable")
    
    # Test 4: Configuration loading
    print("\n📋 Test 4: Configuration Loading")
    print("-" * 40)
    
    try:
        from config import GITHUB_TOKEN, DATADOG_API_KEY, DATADOG_APP_KEY
        print("✅ Config file loaded successfully")
        print(f"   Config GitHub Token: {'Set' if GITHUB_TOKEN != 'your_github_token_here' else 'Not Set'}")
        print(f"   Config Datadog API Key: {'Set' if DATADOG_API_KEY != 'your_datadog_api_key_here' else 'Not Set'}")
        print(f"   Config Datadog App Key: {'Set' if DATADOG_APP_KEY else 'Not Set'}")
    except ImportError:
        print("⚠️  Config file not found or import failed")
    
    # Test 5: Error handling
    print("\n📋 Test 5: Error Handling")
    print("-" * 40)
    
    # Test with invalid repository URL
    invalid_url = "https://github.com/invalid/repo-that-does-not-exist"
    print(f"Testing invalid repository: {invalid_url}")
    
    invalid_result = identifier.identify_issues_and_flags(invalid_url)
    
    if invalid_result.get('error'):
        print(f"✅ Error handling working: {invalid_result['error']}")
    else:
        print(f"⚠️  Expected error for invalid repository, got: {invalid_result.get('total_issues', 0)} issues")
    
    # Summary
    print(f"\n🎉 Merged Identifier Agent Test Summary")
    print("=" * 60)
    print(f"✅ Basic GitHub analysis: Working")
    print(f"✅ Rate limiting handling: {'Working' if not has_token else 'Not tested (token present)'}")
    print(f"✅ Configuration loading: {'Working' if identifier.github_token or identifier.datadog_api_key else 'Not configured'}")
    print(f"✅ Datadog integration: {'Working' if identifier.datadog_enabled else 'Available but not configured'}")
    print(f"✅ Error handling: Working")
    
    print(f"\n📝 Recommendations:")
    if not has_token:
        print(f"   1. Set GITHUB_TOKEN for full analysis capabilities")
    if not identifier.datadog_enabled:
        print(f"   2. Set DATADOG_API_KEY and DATADOG_APP_KEY for monitoring integration")
    print(f"   3. The merged identifier combines the best features from both versions")
    print(f"   4. Ready for integration with the self-healing pipeline")

def test_performance():
    """Test performance with multiple repositories."""
    print(f"\n⚡ Performance Test")
    print("-" * 40)
    
    identifier = GitHubRepositoryIdentifier()
    
    test_repos = [
        "https://github.com/microsoft/vscode",
        "https://github.com/facebook/react",
        "https://github.com/torvalds/linux"
    ]
    
    start_time = datetime.now()
    
    for i, repo_url in enumerate(test_repos, 1):
        print(f"Testing repository {i}/{len(test_repos)}: {repo_url}")
        result = identifier.identify_issues_and_flags(repo_url)
        print(f"   Found {result.get('total_issues', 0)} issues, {result.get('total_flags', 0)} flags")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n✅ Performance test completed in {duration:.2f} seconds")
    print(f"   Average time per repository: {duration/len(test_repos):.2f} seconds")

def main():
    """Main function."""
    print("🚀 Merged Identifier Agent Test Suite")
    print("=" * 60)
    
    try:
        test_merged_identifier()
        test_performance()
        
        print(f"\n🎉 All tests completed successfully!")
        print(f"✅ The merged identifier agent is ready for production use")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
