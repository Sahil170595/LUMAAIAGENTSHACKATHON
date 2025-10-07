#!/usr/bin/env python3
"""
Self-Healing Pipeline Demo
Demonstrates the core functionality of the self-healing pipeline
"""

from Identifier.identifierAdapter import GitHubRepositoryIdentifier

def demo_analysis():
    """Demonstrate the self-healing pipeline analysis."""
    
    print("🚀 Self-Healing Pipeline Demo")
    print("=" * 50)
    
    # Repository to analyze
    repo_url = "https://github.com/Sahil170595/Banterblogs"
    
    print(f"📊 Analyzing repository: {repo_url}")
    print("-" * 50)
    
    try:
        # Create identifier
        identifier = GitHubRepositoryIdentifier()
        
        # Analyze repository
        result = identifier.identify_issues_and_flags(repo_url)
        
        # Display results
        print(f"✅ Analysis complete!")
        print(f"Repository: {result['repository']}")
        print(f"Total Issues: {result['total_issues']}")
        print(f"Total Flags: {result['total_flags']}")
        
        if result.get('summary'):
            summary = result['summary']
            print(f"\n📈 Summary:")
            print(f"  Health Score: {100 - result['total_issues'] * 5}")
            print(f"  Severity Breakdown:")
            for severity, count in summary['severity_breakdown'].items():
                if count > 0:
                    print(f"    {severity.capitalize()}: {count}")
            
            if summary.get('recommendations'):
                print(f"\n💡 Recommendations:")
                for i, rec in enumerate(summary['recommendations'], 1):
                    print(f"  {i}. {rec}")
        
        if result.get('issues'):
            print(f"\n🐛 Issues Found:")
            for issue in result['issues']:
                print(f"  - [{issue['severity'].upper()}] {issue['title']}")
        
        if result.get('flags'):
            print(f"\n🚩 Flags Found:")
            for flag in result['flags']:
                print(f"  - [{flag['severity'].upper()}] {flag['message']}")
        
        print(f"\n📊 Data sent to Datadog dashboard!")
        print(f"Dashboard: https://app.datadoghq.com/dashboard/zk8-v5f-ga8/self-healing-analysis---sahil170595banterblogs")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        return False

def main():
    """Main demo function."""
    success = demo_analysis()
    
    if success:
        print(f"\n🎉 Demo completed successfully!")
        print(f"Your self-healing pipeline is working!")
    else:
        print(f"\n❌ Demo failed. Check your configuration.")

if __name__ == "__main__":
    main()
