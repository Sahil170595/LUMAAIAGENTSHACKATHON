#!/usr/bin/env python3
"""
Reasoner Agent for Self-Healing Pipeline
Analyzes issues and generates intelligent fix proposals using AI reasoning.
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging with debug level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reasoner_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FixType(Enum):
    CONFIG_CHANGE = "config_change"
    SERVICE_RESTART = "service_restart"
    CODE_FIX = "code_fix"
    DEPENDENCY_UPDATE = "dependency_update"
    INFRASTRUCTURE_CHANGE = "infrastructure_change"
    ROLLBACK = "rollback"

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class FixProposal:
    """Represents a proposed fix for an identified issue."""
    id: str
    issue_id: str
    fix_type: FixType
    title: str
    description: str
    steps: List[str]
    tests: List[str]
    confidence_score: float
    estimated_duration: int  # seconds
    risk_level: str
    prerequisites: List[str]
    rollback_plan: List[str]
    created_at: datetime
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['fix_type'] = self.fix_type.value
        data['created_at'] = self.created_at.isoformat()
        return data

@dataclass
class ReasoningContext:
    """Context information for AI reasoning."""
    issue: Dict
    repo_info: Dict
    historical_fixes: List[Dict]
    environment_context: Dict
    constraints: Dict

class ReasonerAgent:
    """
    AI-powered reasoner that analyzes issues and generates intelligent fix proposals.
    Uses OpenAI API for reasoning and fix generation.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.fix_history: List[Dict] = []
        
        logger.info("🧠 Reasoner Agent initialized")
        logger.debug(f"Config: {self.config}")
        
        if not self.openai_api_key:
            logger.warning("⚠️  No OpenAI API key found. Using mock reasoning.")
    
    def _get_default_config(self) -> Dict:
        """Return default configuration for the reasoner."""
        return {
            "max_fixes_per_issue": 3,
            "confidence_threshold": 0.7,
            "max_reasoning_time": 30,  # seconds
            "ai_model": "gpt-4",
            "fallback_to_mock": True,
            "debug_mode": True
        }
    
    def analyze_issue_and_generate_fixes(self, issue_data: Dict) -> List[FixProposal]:
        """
        Main method to analyze an issue and generate fix proposals.
        
        Args:
            issue_data: Structured issue data from Monitor Agent
            
        Returns:
            List of FixProposal objects
        """
        logger.info(f"🔍 Analyzing issue: {issue_data.get('id', 'unknown')}")
        logger.debug(f"Issue data: {json.dumps(issue_data, indent=2)}")
        
        try:
            # Step 1: Parse and validate input
            parsed_issue = self._parse_issue_data(issue_data)
            logger.debug(f"Parsed issue: {parsed_issue}")
            
            # Step 2: Gather context for reasoning
            context = self._gather_reasoning_context(parsed_issue, issue_data)
            logger.debug(f"Reasoning context gathered: {len(context.historical_fixes)} historical fixes")
            
            # Step 3: Generate fix proposals using AI
            if self.openai_api_key and not self.config.get("force_mock_mode"):
                fix_proposals = self._generate_fixes_with_ai(context)
            else:
                logger.info("🤖 Using mock reasoning (no OpenAI API key or force_mock_mode enabled)")
                fix_proposals = self._generate_mock_fixes(context)
            
            # Step 4: Filter and rank proposals
            filtered_proposals = self._filter_and_rank_proposals(fix_proposals)
            
            logger.info(f"✅ Generated {len(filtered_proposals)} fix proposals")
            return filtered_proposals
            
        except Exception as e:
            logger.error(f"❌ Error analyzing issue: {str(e)}")
            logger.debug("Exception details:", exc_info=True)
            return []
    
    def _parse_issue_data(self, issue_data: Dict) -> Dict:
        """Parse and normalize issue data."""
        logger.debug("📝 Parsing issue data")
        
        parsed = {
            "id": issue_data.get("id", f"issue_{int(time.time())}"),
            "type": issue_data.get("type", "unknown"),
            "severity": issue_data.get("severity", "medium"),
            "title": issue_data.get("title", "Untitled issue"),
            "description": issue_data.get("description", ""),
            "repo_url": issue_data.get("repo_url", ""),
            "commit_hash": issue_data.get("commit_hash", ""),
            "error_logs": issue_data.get("error_logs", []),
            "context": issue_data.get("context", {}),
            "timestamp": issue_data.get("timestamp", datetime.now().isoformat())
        }
        
        logger.debug(f"Parsed issue: {parsed['id']} - {parsed['title']}")
        return parsed
    
    def _gather_reasoning_context(self, issue: Dict, raw_issue_data: Dict) -> ReasoningContext:
        """Gather context information for AI reasoning."""
        logger.debug("🔍 Gathering reasoning context")
        
        # Extract repo information
        repo_info = {
            "url": issue.get("repo_url", ""),
            "name": issue.get("repo_url", "").split("/")[-1] if issue.get("repo_url") else "unknown",
            "language": self._detect_language_from_context(issue),
            "framework": self._detect_framework_from_context(issue)
        }
        
        # Get historical fixes (in a real system, this would query a database)
        historical_fixes = self._get_historical_fixes(issue)
        
        # Environment context
        environment_context = {
            "platform": "linux",  # Default assumption
            "containerized": True,
            "ci_cd_enabled": True,
            "monitoring_enabled": True
        }
        
        # Constraints
        constraints = {
            "max_execution_time": 300,  # 5 minutes
            "allowed_fix_types": [ft.value for ft in FixType],
            "risk_tolerance": "medium"
        }
        
        return ReasoningContext(
            issue=issue,
            repo_info=repo_info,
            historical_fixes=historical_fixes,
            environment_context=environment_context,
            constraints=constraints
        )
    
    def _detect_language_from_context(self, issue: Dict) -> str:
        """Detect programming language from issue context."""
        context = issue.get("context", {})
        error_logs = issue.get("error_logs", [])
        
        # Simple heuristics for language detection
        if any("python" in str(log).lower() for log in error_logs):
            return "python"
        elif any("node" in str(log).lower() or "npm" in str(log).lower() for log in error_logs):
            return "javascript"
        elif any("java" in str(log).lower() for log in error_logs):
            return "java"
        elif any("go" in str(log).lower() for log in error_logs):
            return "go"
        else:
            return "unknown"
    
    def _detect_framework_from_context(self, issue: Dict) -> str:
        """Detect framework from issue context."""
        context = issue.get("context", {})
        error_logs = issue.get("error_logs", [])
        
        # Framework detection heuristics
        if any("django" in str(log).lower() for log in error_logs):
            return "django"
        elif any("flask" in str(log).lower() for log in error_logs):
            return "flask"
        elif any("react" in str(log).lower() for log in error_logs):
            return "react"
        elif any("express" in str(log).lower() for log in error_logs):
            return "express"
        else:
            return "unknown"
    
    def _get_historical_fixes(self, issue: Dict) -> List[Dict]:
        """Get historical fixes for similar issues."""
        # In a real system, this would query a database
        # For now, return mock historical data
        return [
            {
                "issue_type": issue.get("type"),
                "fix_type": "service_restart",
                "success_rate": 0.85,
                "avg_resolution_time": 120
            }
        ]
    
    def _generate_fixes_with_ai(self, context: ReasoningContext) -> List[FixProposal]:
        """Generate fix proposals using OpenAI API."""
        logger.info("🤖 Generating fixes with AI")
        
        try:
            # Import OpenAI (would need to install openai package)
            import openai
            
            openai.api_key = self.openai_api_key
            
            # Create prompt for AI reasoning
            prompt = self._create_reasoning_prompt(context)
            
            logger.debug(f"AI Prompt: {prompt}")
            
            response = openai.ChatCompletion.create(
                model=self.config["ai_model"],
                messages=[
                    {"role": "system", "content": "You are an expert DevOps engineer and software architect. Analyze issues and propose specific, actionable fixes."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content
            logger.debug(f"AI Response: {ai_response}")
            
            # Parse AI response into fix proposals
            proposals = self._parse_ai_response(ai_response, context)
            
            return proposals
            
        except ImportError:
            logger.warning("OpenAI package not installed, falling back to mock reasoning")
            return self._generate_mock_fixes(context)
        except Exception as e:
            logger.error(f"AI reasoning failed: {str(e)}")
            logger.info("Falling back to mock reasoning")
            return self._generate_mock_fixes(context)
    
    def _create_reasoning_prompt(self, context: ReasoningContext) -> str:
        """Create a prompt for AI reasoning."""
        issue = context.issue
        
        prompt = f"""
        Analyze this software issue and propose specific fixes:
        
        Issue Details:
        - ID: {issue['id']}
        - Type: {issue['type']}
        - Severity: {issue['severity']}
        - Title: {issue['title']}
        - Description: {issue['description']}
        - Repository: {issue['repo_url']}
        - Language: {context.repo_info['language']}
        - Framework: {context.repo_info['framework']}
        
        Error Logs:
        {json.dumps(issue.get('error_logs', []), indent=2)}
        
        Context:
        {json.dumps(issue.get('context', {}), indent=2)}
        
        Constraints:
        - Max execution time: {context.constraints['max_execution_time']} seconds
        - Risk tolerance: {context.constraints['risk_tolerance']}
        
        Please propose 1-3 specific, actionable fixes. For each fix, provide:
        1. Fix type (config_change, service_restart, code_fix, dependency_update, infrastructure_change, rollback)
        2. Clear title and description
        3. Step-by-step instructions
        4. Tests to verify the fix
        5. Confidence score (0-1)
        6. Risk level (low, medium, high)
        7. Prerequisites
        8. Rollback plan
        
        Respond in JSON format with a "fixes" array.
        """
        
        return prompt
    
    def _parse_ai_response(self, ai_response: str, context: ReasoningContext) -> List[FixProposal]:
        """Parse AI response into FixProposal objects."""
        try:
            # Try to extract JSON from AI response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                data = json.loads(json_str)
                
                proposals = []
                for i, fix_data in enumerate(data.get("fixes", [])):
                    proposal = FixProposal(
                        id=f"fix_{context.issue['id']}_{i}_{int(time.time())}",
                        issue_id=context.issue['id'],
                        fix_type=FixType(fix_data.get("fix_type", "config_change")),
                        title=fix_data.get("title", "Untitled fix"),
                        description=fix_data.get("description", ""),
                        steps=fix_data.get("steps", []),
                        tests=fix_data.get("tests", []),
                        confidence_score=float(fix_data.get("confidence_score", 0.5)),
                        estimated_duration=int(fix_data.get("estimated_duration", 60)),
                        risk_level=fix_data.get("risk_level", "medium"),
                        prerequisites=fix_data.get("prerequisites", []),
                        rollback_plan=fix_data.get("rollback_plan", []),
                        created_at=datetime.now()
                    )
                    proposals.append(proposal)
                
                return proposals
                
        except Exception as e:
            logger.error(f"Failed to parse AI response: {str(e)}")
        
        # Fallback to mock fixes if parsing fails
        return self._generate_mock_fixes(context)
    
    def _generate_mock_fixes(self, context: ReasoningContext) -> List[FixProposal]:
        """Generate mock fix proposals for testing."""
        logger.info("🎭 Generating mock fix proposals")
        
        issue = context.issue
        issue_type = issue.get("type", "unknown")
        
        # Generate fixes based on issue type
        mock_fixes = []
        
        if issue_type == "service_failure":
            mock_fixes.append(FixProposal(
                id=f"fix_{issue['id']}_restart_{int(time.time())}",
                issue_id=issue['id'],
                fix_type=FixType.SERVICE_RESTART,
                title="Restart Affected Service",
                description="Restart the failing service to resolve temporary issues",
                steps=[
                    "Identify the failing service from logs",
                    "Stop the service gracefully",
                    "Wait 10 seconds for cleanup",
                    "Start the service",
                    "Verify service health"
                ],
                tests=[
                    "curl -f http://localhost:8080/health",
                    "Check service status",
                    "Verify logs show successful startup"
                ],
                confidence_score=0.8,
                estimated_duration=60,
                risk_level="low",
                prerequisites=["Service access permissions"],
                rollback_plan=["Stop service", "Start previous version"],
                created_at=datetime.now()
            ))
        
        elif issue_type == "config_error":
            mock_fixes.append(FixProposal(
                id=f"fix_{issue['id']}_config_{int(time.time())}",
                issue_id=issue['id'],
                fix_type=FixType.CONFIG_CHANGE,
                title="Fix Configuration Error",
                description="Correct the configuration issue causing the problem",
                steps=[
                    "Identify the configuration error",
                    "Backup current config",
                    "Apply corrected configuration",
                    "Restart affected services",
                    "Verify configuration is applied"
                ],
                tests=[
                    "Validate configuration syntax",
                    "Test application startup",
                    "Run smoke tests"
                ],
                confidence_score=0.7,
                estimated_duration=120,
                risk_level="medium",
                prerequisites=["Config backup", "Access to config files"],
                rollback_plan=["Restore backup config", "Restart services"],
                created_at=datetime.now()
            ))
        
        elif issue_type == "dependency_issue":
            mock_fixes.append(FixProposal(
                id=f"fix_{issue['id']}_dependency_{int(time.time())}",
                issue_id=issue['id'],
                fix_type=FixType.DEPENDENCY_UPDATE,
                title="Update Vulnerable Dependency",
                description="Update the vulnerable dependency to the recommended secure version",
                steps=[
                    "Identify vulnerable package and version",
                    "Check for breaking changes in new version",
                    "Update package.json/requirements.txt",
                    "Run dependency installation",
                    "Test application functionality",
                    "Deploy updated version"
                ],
                tests=[
                    "npm audit (or equivalent security scan)",
                    "Run full test suite",
                    "Check for breaking changes",
                    "Verify security vulnerabilities resolved"
                ],
                confidence_score=0.8,
                estimated_duration=300,
                risk_level="low",
                prerequisites=["Package manager access", "Test environment"],
                rollback_plan=["Revert to previous dependency version", "Reinstall dependencies"],
                created_at=datetime.now()
            ))
        
        elif issue_type == "performance_issue":
            mock_fixes.append(FixProposal(
                id=f"fix_{issue['id']}_performance_{int(time.time())}",
                issue_id=issue['id'],
                fix_type=FixType.INFRASTRUCTURE_CHANGE,
                title="Optimize Resource Usage",
                description="Address performance issues through resource optimization",
                steps=[
                    "Analyze current resource usage patterns",
                    "Identify memory leaks or inefficient processes",
                    "Scale resources or restart services",
                    "Implement resource limits",
                    "Monitor performance improvements"
                ],
                tests=[
                    "Monitor memory usage",
                    "Check response times",
                    "Verify error rates",
                    "Run performance benchmarks"
                ],
                confidence_score=0.75,
                estimated_duration=180,
                risk_level="medium",
                prerequisites=["Resource monitoring tools", "Access to scaling controls"],
                rollback_plan=["Revert resource changes", "Restart services"],
                created_at=datetime.now()
            ))
        
        # Default fix for unknown issues
        if not mock_fixes:
            mock_fixes.append(FixProposal(
                id=f"fix_{issue['id']}_generic_{int(time.time())}",
                issue_id=issue['id'],
                fix_type=FixType.ROLLBACK,
                title="Rollback to Previous Working State",
                description="Rollback to the last known working state to resolve the issue",
                steps=[
                    "Identify last working commit/version",
                    "Backup current state",
                    "Rollback to previous version",
                    "Restart services",
                    "Verify functionality"
                ],
                tests=[
                    "Run full test suite",
                    "Check application health",
                    "Verify no regression"
                ],
                confidence_score=0.6,
                estimated_duration=180,
                risk_level="medium",
                prerequisites=["Version control access", "Backup of current state"],
                rollback_plan=["Restore current state", "Restart services"],
                created_at=datetime.now()
            ))
        
        logger.debug(f"Generated {len(mock_fixes)} mock fixes")
        return mock_fixes
    
    def _filter_and_rank_proposals(self, proposals: List[FixProposal]) -> List[FixProposal]:
        """Filter and rank fix proposals by confidence and constraints."""
        logger.debug(f"Filtering and ranking {len(proposals)} proposals")
        
        # Filter by confidence threshold
        filtered = [p for p in proposals if p.confidence_score >= self.config["confidence_threshold"]]
        
        # Sort by confidence score (highest first)
        filtered.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Limit to max fixes per issue
        max_fixes = self.config["max_fixes_per_issue"]
        if len(filtered) > max_fixes:
            filtered = filtered[:max_fixes]
        
        logger.debug(f"Filtered to {len(filtered)} proposals")
        return filtered

def main():
    """Main function for testing the Reasoner Agent."""
    logger.info("🚀 Starting Reasoner Agent test")
    
    # Create reasoner instance
    reasoner = ReasonerAgent()
    
    # Mock issue data for testing
    test_issue = {
        "id": "test_issue_001",
        "type": "service_failure",
        "severity": "high",
        "title": "Authentication service failing",
        "description": "The authentication service is returning 500 errors",
        "repo_url": "https://github.com/example/auth-service",
        "commit_hash": "abc123",
        "error_logs": [
            "ERROR: Connection refused to database",
            "ERROR: Failed to authenticate user",
            "ERROR: Service health check failed"
        ],
        "context": {
            "service_name": "auth-service",
            "affected_endpoints": ["/api/auth/login", "/api/auth/verify"],
            "error_rate": 15.2
        },
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info("🧪 Testing with mock issue data")
    logger.debug(f"Test issue: {json.dumps(test_issue, indent=2)}")
    
    # Generate fixes
    fixes = reasoner.analyze_issue_and_generate_fixes(test_issue)
    
    logger.info(f"✅ Generated {len(fixes)} fix proposals")
    
    for i, fix in enumerate(fixes, 1):
        logger.info(f"Fix {i}: {fix.title} (Confidence: {fix.confidence_score:.2f})")
        logger.debug(f"Fix details: {json.dumps(fix.to_dict(), indent=2)}")
    
    return fixes

if __name__ == "__main__":
    main()
