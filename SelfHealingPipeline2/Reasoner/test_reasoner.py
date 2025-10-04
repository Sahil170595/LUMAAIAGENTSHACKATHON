#!/usr/bin/env python3
"""
Test script for the Reasoner Agent
Tests the reasoner with various issue scenarios.
"""

import sys
import json
import os
from datetime import datetime
from reasoner_agent import ReasonerAgent

def test_reasoner_with_mock_issues():
    """Test the reasoner with various mock issue scenarios."""
    print("🧠 Testing Reasoner Agent")
    print("=" * 50)
    
    # Create reasoner instance
    reasoner = ReasonerAgent()
    
    # Test cases
    test_cases = [
        {
            "name": "Service Failure Issue",
            "issue": {
                "id": "issue_001",
                "type": "service_failure",
                "severity": "high",
                "title": "Authentication service down",
                "description": "The auth service is returning 500 errors and failing health checks",
                "repo_url": "https://github.com/example/auth-service",
                "commit_hash": "abc123",
                "error_logs": [
                    "ERROR: Database connection timeout",
                    "ERROR: Service health check failed",
                    "ERROR: Authentication failed for user requests"
                ],
                "context": {
                    "service_name": "auth-service",
                    "error_rate": 25.5,
                    "affected_endpoints": ["/api/auth/login", "/api/auth/verify"],
                    "last_working_time": "2025-01-04T10:00:00Z"
                },
                "timestamp": datetime.now().isoformat()
            }
        },
        {
            "name": "Configuration Error Issue",
            "issue": {
                "id": "issue_002",
                "type": "config_error",
                "severity": "medium",
                "title": "Invalid configuration causing startup failure",
                "description": "Application fails to start due to configuration validation error",
                "repo_url": "https://github.com/example/web-app",
                "commit_hash": "def456",
                "error_logs": [
                    "ERROR: Invalid configuration: missing required field 'database_url'",
                    "ERROR: Configuration validation failed",
                    "ERROR: Application startup aborted"
                ],
                "context": {
                    "config_file": "config/app.yaml",
                    "missing_fields": ["database_url", "api_key"],
                    "environment": "production"
                },
                "timestamp": datetime.now().isoformat()
            }
        },
        {
            "name": "Dependency Issue",
            "issue": {
                "id": "issue_003",
                "type": "dependency_issue",
                "severity": "medium",
                "title": "Outdated dependency causing security vulnerability",
                "description": "Security scan detected vulnerable dependency",
                "repo_url": "https://github.com/example/api-service",
                "commit_hash": "ghi789",
                "error_logs": [
                    "WARNING: Security vulnerability in lodash@4.17.15",
                    "WARNING: CVE-2021-23337 detected",
                    "ERROR: Security scan failed"
                ],
                "context": {
                    "vulnerable_package": "lodash",
                    "current_version": "4.17.15",
                    "recommended_version": "4.17.21",
                    "severity": "high"
                },
                "timestamp": datetime.now().isoformat()
            }
        },
        {
            "name": "Performance Issue",
            "issue": {
                "id": "issue_004",
                "type": "performance_issue",
                "severity": "high",
                "title": "High memory usage causing service degradation",
                "description": "Memory usage spiked to 95% causing slow response times",
                "repo_url": "https://github.com/example/data-processor",
                "commit_hash": "jkl012",
                "error_logs": [
                    "WARNING: Memory usage at 95%",
                    "WARNING: Response time degraded to 5s",
                    "ERROR: Service timeout errors increasing"
                ],
                "context": {
                    "memory_usage": 95.2,
                    "cpu_usage": 78.5,
                    "response_time": 5.2,
                    "error_rate": 12.3
                },
                "timestamp": datetime.now().isoformat()
            }
        }
    ]
    
    # Run tests
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}: {test_case['name']}")
        print("-" * 40)
        
        issue = test_case['issue']
        print(f"Issue: {issue['title']}")
        print(f"Type: {issue['type']}")
        print(f"Severity: {issue['severity']}")
        
        # Generate fixes
        fixes = reasoner.analyze_issue_and_generate_fixes(issue)
        
        print(f"✅ Generated {len(fixes)} fix proposals:")
        
        for j, fix in enumerate(fixes, 1):
            print(f"\n  Fix {j}: {fix.title}")
            print(f"    Type: {fix.fix_type.value}")
            print(f"    Confidence: {fix.confidence_score:.2f}")
            print(f"    Risk Level: {fix.risk_level}")
            print(f"    Estimated Duration: {fix.estimated_duration}s")
            print(f"    Description: {fix.description}")
            
            if fix.steps:
                print(f"    Steps:")
                for step in fix.steps:
                    print(f"      • {step}")
            
            if fix.tests:
                print(f"    Tests:")
                for test in fix.tests:
                    print(f"      • {test}")
        
        print("\n" + "="*50)
    
    return True

def test_reasoner_with_json_input():
    """Test reasoner with JSON input from command line."""
    if len(sys.argv) < 2:
        print("Usage: python test_reasoner.py <json_file>")
        print("Or run without arguments for mock tests")
        return False
    
    json_file = sys.argv[1]
    
    try:
        with open(json_file, 'r') as f:
            issue_data = json.load(f)
        
        print(f"📄 Testing with JSON input: {json_file}")
        print("=" * 50)
        
        reasoner = ReasonerAgent()
        fixes = reasoner.analyze_issue_and_generate_fixes(issue_data)
        
        print(f"✅ Generated {len(fixes)} fix proposals:")
        
        for i, fix in enumerate(fixes, 1):
            print(f"\nFix {i}: {fix.title}")
            print(json.dumps(fix.to_dict(), indent=2))
        
        return True
        
    except FileNotFoundError:
        print(f"❌ File not found: {json_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_sample_json():
    """Create a sample JSON file for testing."""
    sample_issue = {
        "id": "sample_issue_001",
        "type": "service_failure",
        "severity": "high",
        "title": "Database connection timeout",
        "description": "Application cannot connect to database after recent deployment",
        "repo_url": "https://github.com/example/my-app",
        "commit_hash": "latest",
        "error_logs": [
            "ERROR: Database connection timeout after 30s",
            "ERROR: Connection pool exhausted",
            "ERROR: Service health check failed"
        ],
        "context": {
            "service_name": "my-app",
            "database_host": "db.example.com",
            "connection_pool_size": 10,
            "timeout": 30,
            "affected_endpoints": ["/api/users", "/api/orders"]
        },
        "timestamp": datetime.now().isoformat()
    }
    
    with open("sample_issue.json", "w") as f:
        json.dump(sample_issue, f, indent=2)
    
    print("📄 Created sample_issue.json for testing")
    print("Usage: python test_reasoner.py sample_issue.json")

def main():
    """Main function."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--create-sample":
            create_sample_json()
            return
        else:
            success = test_reasoner_with_json_input()
    else:
        success = test_reasoner_with_mock_issues()
    
    if success:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
