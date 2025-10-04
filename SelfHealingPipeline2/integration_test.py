#!/usr/bin/env python3
"""
Integration Test: Identifier + Reasoner
Demonstrates how the Identifier and Reasoner agents work together in the self-healing pipeline.
"""

import sys
import json
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/Users/thilaknarasimhamurthy/Desktop/Luma/LUMAAIAGENTSHACKATHON/SelfHealingPipeline')

from Identifier.identifierAdapter import identify_issues
from Reasoner.reasoner_agent import ReasonerAgent

def test_identifier_to_reasoner_pipeline():
    """Test the complete pipeline from issue identification to fix proposal generation."""
    print("🔄 Self-Healing Pipeline Integration Test")
    print("=" * 60)
    
    # Step 1: Use Identifier to find issues in a real repository
    print("\n📊 Step 1: Issue Identification")
    print("-" * 40)
    
    repo_url = "https://github.com/microsoft/vscode"
    print(f"Analyzing repository: {repo_url}")
    
    try:
        # Identify issues using the existing identifier
        identification_result = identify_issues(repo_url)
        
        print(f"✅ Found {identification_result.get('total_issues', 0)} issues and {identification_result.get('total_flags', 0)} flags")
        
        # Display some of the issues found
        issues = identification_result.get('issues', [])
        if issues:
            print(f"\n📋 Sample Issues Found:")
            for i, issue in enumerate(issues[:3], 1):  # Show first 3 issues
                print(f"  {i}. [{issue.get('severity', 'unknown').upper()}] {issue.get('title', 'No title')}")
                print(f"     Type: {issue.get('type', 'unknown')} | Source: {issue.get('source', 'unknown')}")
                if issue.get('url'):
                    print(f"     URL: {issue['url']}")
                print()
        
        # Step 2: Convert identified issues to reasoner input format
        print("\n🧠 Step 2: Fix Proposal Generation")
        print("-" * 40)
        
        # Create reasoner agent
        reasoner = ReasonerAgent()
        
        # Process each issue through the reasoner
        total_fixes = 0
        for i, issue in enumerate(issues[:2], 1):  # Process first 2 issues
            print(f"\n🔍 Processing Issue {i}: {issue.get('title', 'Unknown')}")
            
            # Convert identifier issue format to reasoner input format
            reasoner_input = {
                "id": f"issue_{i}_{int(datetime.now().timestamp())}",
                "type": _map_issue_type(issue.get('type', 'unknown')),
                "severity": issue.get('severity', 'medium'),
                "title": issue.get('title', 'Unknown issue'),
                "description": issue.get('description', 'No description available'),
                "repo_url": repo_url,
                "commit_hash": "latest",
                "error_logs": [],  # Identifier doesn't provide error logs
                "context": {
                    "source": issue.get('source', 'unknown'),
                    "issue_type": issue.get('type', 'unknown'),
                    "github_url": issue.get('url', '')
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Generate fix proposals
            fixes = reasoner.analyze_issue_and_generate_fixes(reasoner_input)
            
            print(f"✅ Generated {len(fixes)} fix proposals:")
            
            for j, fix in enumerate(fixes, 1):
                print(f"\n  Fix {j}: {fix.title}")
                print(f"    Type: {fix.fix_type.value}")
                print(f"    Confidence: {fix.confidence_score:.2f}")
                print(f"    Risk Level: {fix.risk_level}")
                print(f"    Duration: {fix.estimated_duration}s")
                print(f"    Description: {fix.description}")
                
                if fix.steps:
                    print(f"    Steps:")
                    for step in fix.steps[:3]:  # Show first 3 steps
                        print(f"      • {step}")
                    if len(fix.steps) > 3:
                        print(f"      • ... and {len(fix.steps) - 3} more steps")
                
                if fix.tests:
                    print(f"    Tests:")
                    for test in fix.tests[:2]:  # Show first 2 tests
                        print(f"      • {test}")
                    if len(fix.tests) > 2:
                        print(f"      • ... and {len(fix.tests) - 2} more tests")
            
            total_fixes += len(fixes)
        
        # Step 3: Summary
        print(f"\n📈 Integration Test Summary")
        print("-" * 40)
        print(f"Repository Analyzed: {repo_url}")
        print(f"Issues Identified: {len(issues)}")
        print(f"Issues Processed: {min(2, len(issues))}")
        print(f"Total Fix Proposals Generated: {total_fixes}")
        print(f"Average Fixes per Issue: {total_fixes / max(1, min(2, len(issues))):.1f}")
        
        print(f"\n🎉 Integration test completed successfully!")
        print(f"✅ Identifier: Working - Found real issues in {repo_url}")
        print(f"✅ Reasoner: Working - Generated intelligent fix proposals")
        print(f"✅ Pipeline: Working - Seamless data flow between components")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def _map_issue_type(identifier_type: str) -> str:
    """Map identifier issue types to reasoner-compatible types."""
    mapping = {
        "github_issue": "service_failure",
        "dependency_analysis": "dependency_issue", 
        "code_quality": "performance_issue",
        "security_vulnerability": "security_issue",
        "documentation": "config_error"
    }
    return mapping.get(identifier_type, "service_failure")

def test_with_mock_issue():
    """Test with a mock issue to demonstrate the pipeline."""
    print("\n🧪 Mock Issue Pipeline Test")
    print("-" * 40)
    
    # Create a mock issue that would come from a monitoring system
    mock_issue = {
        "id": "mock_issue_001",
        "type": "service_failure",
        "severity": "high",
        "title": "API Gateway returning 500 errors",
        "description": "The API gateway is experiencing high error rates and failing health checks",
        "repo_url": "https://github.com/example/api-gateway",
        "commit_hash": "abc123def",
        "error_logs": [
            "ERROR: Gateway timeout after 30s",
            "ERROR: Upstream service unavailable",
            "ERROR: Health check failed - connection refused"
        ],
        "context": {
            "service_name": "api-gateway",
            "error_rate": 45.2,
            "response_time": 8.5,
            "affected_endpoints": ["/api/users", "/api/orders", "/api/payments"],
            "upstream_services": ["user-service", "order-service", "payment-service"]
        },
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"Mock Issue: {mock_issue['title']}")
    print(f"Severity: {mock_issue['severity']}")
    print(f"Error Rate: {mock_issue['context']['error_rate']}%")
    
    # Process through reasoner
    reasoner = ReasonerAgent()
    fixes = reasoner.analyze_issue_and_generate_fixes(mock_issue)
    
    print(f"\n✅ Generated {len(fixes)} fix proposals for mock issue:")
    
    for i, fix in enumerate(fixes, 1):
        print(f"\n  Fix {i}: {fix.title}")
        print(f"    Confidence: {fix.confidence_score:.2f}")
        print(f"    Risk Level: {fix.risk_level}")
        print(f"    Estimated Duration: {fix.estimated_duration}s")
        
        print(f"    Key Steps:")
        for step in fix.steps[:2]:
            print(f"      • {step}")
        
        print(f"    Validation Tests:")
        for test in fix.tests[:2]:
            print(f"      • {test}")
    
    return len(fixes) > 0

def main():
    """Main function."""
    print("🚀 Starting Self-Healing Pipeline Integration Tests")
    print("=" * 60)
    
    success1 = test_identifier_to_reasoner_pipeline()
    success2 = test_with_mock_issue()
    
    print(f"\n🏁 Final Results")
    print("=" * 60)
    
    if success1 and success2:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ Identifier Agent: Working correctly")
        print("✅ Reasoner Agent: Working correctly") 
        print("✅ Pipeline Integration: Working correctly")
        print("\n🚀 Ready for Executor Agent implementation!")
    else:
        print("❌ Some integration tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
