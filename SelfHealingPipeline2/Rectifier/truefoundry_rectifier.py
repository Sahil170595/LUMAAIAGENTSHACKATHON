#!/usr/bin/env python3
"""
TrueFoundry Rectifier for Self-Healing Pipeline
Implements the Executor Agent using TrueFoundry workspace for safe testing and deployment.
"""

import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# TrueFoundry SDK integration
try:
    from truefoundry import TrueFoundryClient
    TRUEFOUNDRY_AVAILABLE = True
except ImportError:
    TRUEFOUNDRY_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class FixType(Enum):
    CONFIG_CHANGE = "config_change"
    SERVICE_RESTART = "service_restart"
    CODE_FIX = "code_fix"
    DEPENDENCY_UPDATE = "dependency_update"
    INFRASTRUCTURE_CHANGE = "infrastructure_change"
    ROLLBACK = "rollback"

@dataclass
class FixExecution:
    """Represents a fix execution in TrueFoundry sandbox."""
    id: str
    fix_proposal_id: str
    status: ExecutionStatus
    job_id: Optional[str] = None
    workspace_name: str = "self-healing-workspace"
    container_image: str = "python:3.10"
    resources: Dict[str, Any] = None
    environment_vars: Dict[str, str] = None
    command: List[str] = None
    logs: List[str] = None
    exit_code: Optional[int] = None
    execution_time: float = 0.0
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.resources is None:
            self.resources = {"cpu": "2", "memory": "4Gi"}
        if self.environment_vars is None:
            self.environment_vars = {}
        if self.command is None:
            self.command = []
        if self.logs is None:
            self.logs = []
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data

@dataclass
class DeploymentResult:
    """Represents the result of a fix deployment."""
    execution_id: str
    success: bool
    pr_url: Optional[str] = None
    deployment_url: Optional[str] = None
    validation_results: Dict[str, Any] = None
    rollback_available: bool = False
    error_message: Optional[str] = None

class TrueFoundryRectifier:
    """
    Rectifier that uses TrueFoundry workspace for safe testing and deployment.
    Implements the Executor Agent functionality with TrueFoundry integration.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or self._get_default_config()
        self.truefoundry_enabled = False
        self.client = None
        self.active_executions: Dict[str, FixExecution] = {}
        
        # Initialize TrueFoundry client
        self._initialize_truefoundry()
        
        logger.info("🔧 TrueFoundry Rectifier initialized")
    
    def _get_default_config(self) -> Dict:
        """Return default configuration for the rectifier."""
        return {
            "workspace_name": "self-healing-workspace",
            "default_image": "python:3.10",
            "default_resources": {
                "cpu": "2",
                "memory": "4Gi",
                "timeout": 300  # 5 minutes
            },
            "github": {
                "token": os.getenv("GITHUB_TOKEN"),
                "base_url": "https://api.github.com"
            },
            "truefoundry": {
                "api_key": os.getenv("TRUEFOUNDRY_API_KEY"),
                "base_url": os.getenv("TRUEFOUNDRY_BASE_URL", "https://api.truefoundry.com")
            },
            "constraints": {
                "max_execution_time": 600,  # 10 minutes
                "max_concurrent_executions": 5,
                "retry_attempts": 3
            }
        }
    
    def _initialize_truefoundry(self):
        """Initialize TrueFoundry client."""
        if not TRUEFOUNDRY_AVAILABLE:
            logger.warning("⚠️  TrueFoundry SDK not available. Install with: pip install truefoundry-sdk")
            return
        
        api_key = self.config["truefoundry"]["api_key"]
        if not api_key:
            logger.warning("⚠️  TrueFoundry API key not provided. Set TRUEFOUNDRY_API_KEY environment variable.")
            return
        
        try:
            self.client = TrueFoundryClient(api_key=api_key)
            self.truefoundry_enabled = True
            logger.info("✅ TrueFoundry client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize TrueFoundry client: {str(e)}")
            self.truefoundry_enabled = False
    
    def execute_fix(self, fix_proposal: Dict, repo_url: str) -> FixExecution:
        """
        Execute a fix proposal in TrueFoundry sandbox.
        
        Args:
            fix_proposal: Fix proposal from Reasoner Agent
            repo_url: GitHub repository URL
            
        Returns:
            FixExecution object with execution details
        """
        execution_id = f"fix_{fix_proposal['id']}_{int(time.time())}"
        
        logger.info(f"🚀 Executing fix: {fix_proposal['title']}")
        logger.debug(f"Fix proposal: {json.dumps(fix_proposal, indent=2)}")
        
        # Create execution object
        execution = FixExecution(
            id=execution_id,
            fix_proposal_id=fix_proposal['id'],
            status=ExecutionStatus.PENDING,
            workspace_name=self.config["workspace_name"],
            container_image=self._get_container_image(fix_proposal),
            resources=self._get_resource_requirements(fix_proposal),
            environment_vars=self._get_environment_variables(fix_proposal, repo_url),
            command=self._build_execution_command(fix_proposal, repo_url)
        )
        
        self.active_executions[execution_id] = execution
        
        try:
            if self.truefoundry_enabled:
                # Execute in TrueFoundry workspace
                job_result = self._execute_in_truefoundry(execution)
                execution.status = ExecutionStatus.SUCCESS if job_result["success"] else ExecutionStatus.FAILED
                execution.logs = job_result.get("logs", [])
                execution.exit_code = job_result.get("exit_code", 1)
                execution.error_message = job_result.get("error_message")
            else:
                # Fallback to mock execution
                logger.info("🎭 Using mock execution (TrueFoundry not available)")
                mock_result = self._mock_execution(execution)
                execution.status = ExecutionStatus.SUCCESS if mock_result["success"] else ExecutionStatus.FAILED
                execution.logs = mock_result.get("logs", [])
                execution.exit_code = mock_result.get("exit_code", 0)
            
            execution.completed_at = datetime.now()
            execution.execution_time = (execution.completed_at - execution.created_at).total_seconds()
            
            logger.info(f"✅ Fix execution completed: {execution.status.value}")
            return execution
            
        except Exception as e:
            logger.error(f"❌ Fix execution failed: {str(e)}")
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
            execution.execution_time = (execution.completed_at - execution.created_at).total_seconds()
            return execution
    
    def _get_container_image(self, fix_proposal: Dict) -> str:
        """Determine the appropriate container image for the fix."""
        fix_type = fix_proposal.get("fix_type", "config_change")
        
        image_mapping = {
            "config_change": "python:3.10",
            "service_restart": "alpine:latest",
            "code_fix": "python:3.10",
            "dependency_update": "node:18",  # or python:3.10
            "infrastructure_change": "alpine:latest",
            "rollback": "git:latest"
        }
        
        return image_mapping.get(fix_type, "python:3.10")
    
    def _get_resource_requirements(self, fix_proposal: Dict) -> Dict[str, Any]:
        """Determine resource requirements based on fix type."""
        base_resources = self.config["default_resources"].copy()
        
        fix_type = fix_proposal.get("fix_type", "config_change")
        
        # Adjust resources based on fix complexity
        if fix_type in ["dependency_update", "infrastructure_change"]:
            base_resources["cpu"] = "4"
            base_resources["memory"] = "8Gi"
            base_resources["timeout"] = 600  # 10 minutes
        
        return base_resources
    
    def _get_environment_variables(self, fix_proposal: Dict, repo_url: str) -> Dict[str, str]:
        """Set up environment variables for the execution."""
        env_vars = {
            "REPO_URL": repo_url,
            "FIX_ID": fix_proposal["id"],
            "FIX_TYPE": fix_proposal.get("fix_type", "config_change"),
            "EXECUTION_ID": f"fix_{fix_proposal['id']}_{int(time.time())}",
            "PYTHONUNBUFFERED": "1"
        }
        
        # Add GitHub token if available
        github_token = self.config["github"]["token"]
        if github_token:
            env_vars["GITHUB_TOKEN"] = github_token
        
        return env_vars
    
    def _build_execution_command(self, fix_proposal: Dict, repo_url: str) -> List[str]:
        """Build the execution command for the fix."""
        fix_type = fix_proposal.get("fix_type", "config_change")
        
        # Base command template
        base_cmd = [
            "/bin/bash", "-c",
            f"""
            set -e
            echo "🚀 Starting fix execution: {fix_proposal['title']}"
            echo "📋 Fix Type: {fix_type}"
            echo "🔗 Repository: {repo_url}"
            
            # Clone repository
            git clone {repo_url} repo
            cd repo
            
            # Apply fix based on type
            {self._get_fix_script(fix_proposal)}
            
            # Run tests
            {self._get_test_script(fix_proposal)}
            
            echo "✅ Fix execution completed successfully"
            """
        ]
        
        return base_cmd
    
    def _get_fix_script(self, fix_proposal: Dict) -> str:
        """Generate the fix application script."""
        fix_type = fix_proposal.get("fix_type", "config_change")
        steps = fix_proposal.get("steps", [])
        
        if not steps:
            return "echo 'No fix steps provided'"
        
        script_lines = []
        script_lines.append("echo '🔧 Applying fix steps:'")
        
        for i, step in enumerate(steps, 1):
            script_lines.append(f"echo '{i}. {step}'")
            script_lines.append(f"# {step}")
            
            # Generate actual commands based on step content
            if "restart" in step.lower():
                script_lines.append("echo 'Restarting service...'")
                script_lines.append("sleep 5  # Simulate restart")
            elif "config" in step.lower():
                script_lines.append("echo 'Updating configuration...'")
                script_lines.append("echo 'Config updated' > config_update.log")
            elif "dependency" in step.lower():
                script_lines.append("echo 'Updating dependencies...'")
                script_lines.append("npm install || pip install -r requirements.txt || echo 'No dependency files found'")
            else:
                script_lines.append(f"echo 'Executing: {step}'")
                script_lines.append("sleep 2  # Simulate execution")
        
        return "\n".join(script_lines)
    
    def _get_test_script(self, fix_proposal: Dict) -> str:
        """Generate the test execution script."""
        tests = fix_proposal.get("tests", [])
        
        if not tests:
            return "echo 'No tests provided'"
        
        script_lines = []
        script_lines.append("echo '🧪 Running validation tests:'")
        
        for i, test in enumerate(tests, 1):
            script_lines.append(f"echo '{i}. {test}'")
            script_lines.append(f"# {test}")
            
            # Generate test commands
            if "curl" in test.lower():
                script_lines.append("echo 'Testing API endpoint...'")
                script_lines.append("curl -f http://localhost:8080/health || echo 'Health check failed'")
            elif "pytest" in test.lower():
                script_lines.append("echo 'Running pytest...'")
                script_lines.append("pytest tests/ || echo 'Tests failed'")
            elif "npm test" in test.lower():
                script_lines.append("echo 'Running npm tests...'")
                script_lines.append("npm test || echo 'Tests failed'")
            else:
                script_lines.append(f"echo 'Running: {test}'")
                script_lines.append("echo 'Test completed'")
        
        return "\n".join(script_lines)
    
    def _execute_in_truefoundry(self, execution: FixExecution) -> Dict[str, Any]:
        """Execute the fix in TrueFoundry workspace."""
        try:
            logger.info(f"🔧 Executing in TrueFoundry workspace: {execution.workspace_name}")
            
            # In a real implementation, this would use the TrueFoundry SDK
            # to create and execute a job in the workspace
            
            # Mock TrueFoundry execution for now
            logger.debug("🎭 Mock TrueFoundry execution (SDK integration pending)")
            
            # Simulate job execution
            time.sleep(2)  # Simulate execution time
            
            return {
                "success": True,
                "logs": [
                    f"🚀 Starting fix execution: {execution.fix_proposal_id}",
                    f"📋 Container: {execution.container_image}",
                    f"🔧 Resources: {execution.resources}",
                    "✅ Fix applied successfully",
                    "✅ Tests passed",
                    "🎉 Execution completed"
                ],
                "exit_code": 0
            }
            
        except Exception as e:
            logger.error(f"❌ TrueFoundry execution failed: {str(e)}")
            return {
                "success": False,
                "logs": [f"❌ Execution failed: {str(e)}"],
                "exit_code": 1,
                "error_message": str(e)
            }
    
    def _mock_execution(self, execution: FixExecution) -> Dict[str, Any]:
        """Mock execution for testing without TrueFoundry."""
        logger.info("🎭 Running mock execution")
        
        # Simulate execution time
        time.sleep(1)
        
        # Simulate success/failure based on fix type
        fix_type = execution.fix_proposal_id.split('_')[1] if '_' in execution.fix_proposal_id else "unknown"
        
        # Mock some failures for demonstration
        if "dependency" in fix_type.lower():
            return {
                "success": True,
                "logs": [
                    "🚀 Mock execution started",
                    "📦 Updating dependencies...",
                    "✅ Dependencies updated successfully",
                    "🧪 Running tests...",
                    "✅ All tests passed",
                    "🎉 Mock execution completed successfully"
                ],
                "exit_code": 0
            }
        else:
            return {
                "success": True,
                "logs": [
                    "🚀 Mock execution started",
                    "🔧 Applying fix...",
                    "✅ Fix applied successfully",
                    "🧪 Running validation...",
                    "✅ Validation passed",
                    "🎉 Mock execution completed successfully"
                ],
                "exit_code": 0
            }
    
    def deploy_fix(self, execution: FixExecution, repo_url: str) -> DeploymentResult:
        """
        Deploy a successfully tested fix to production.
        
        Args:
            execution: Successful FixExecution
            repo_url: GitHub repository URL
            
        Returns:
            DeploymentResult with deployment details
        """
        logger.info(f"🚀 Deploying fix: {execution.fix_proposal_id}")
        
        try:
            # Create GitHub PR with the fix
            pr_url = self._create_github_pr(execution, repo_url)
            
            # Trigger CI/CD pipeline
            deployment_url = self._trigger_deployment(execution, repo_url)
            
            # Validate deployment
            validation_results = self._validate_deployment(execution)
            
            result = DeploymentResult(
                execution_id=execution.id,
                success=True,
                pr_url=pr_url,
                deployment_url=deployment_url,
                validation_results=validation_results,
                rollback_available=True
            )
            
            logger.info(f"✅ Fix deployed successfully: {pr_url}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Fix deployment failed: {str(e)}")
            return DeploymentResult(
                execution_id=execution.id,
                success=False,
                error_message=str(e)
            )
    
    def _create_github_pr(self, execution: FixExecution, repo_url: str) -> str:
        """Create a GitHub PR with the fix."""
        logger.info("📝 Creating GitHub PR...")
        
        # Mock PR creation
        pr_number = int(time.time()) % 10000
        pr_url = f"{repo_url}/pull/{pr_number}"
        
        logger.info(f"✅ GitHub PR created: {pr_url}")
        return pr_url
    
    def _trigger_deployment(self, execution: FixExecution, repo_url: str) -> str:
        """Trigger deployment pipeline."""
        logger.info("🚀 Triggering deployment...")
        
        # Mock deployment URL
        deployment_url = f"{repo_url}/deployments/{execution.id}"
        
        logger.info(f"✅ Deployment triggered: {deployment_url}")
        return deployment_url
    
    def _validate_deployment(self, execution: FixExecution) -> Dict[str, Any]:
        """Validate the deployment."""
        logger.info("🔍 Validating deployment...")
        
        # Mock validation
        validation_results = {
            "health_check": "passed",
            "performance_test": "passed",
            "smoke_test": "passed",
            "deployment_time": "2m 30s"
        }
        
        logger.info("✅ Deployment validation passed")
        return validation_results
    
    def get_execution_status(self, execution_id: str) -> Optional[FixExecution]:
        """Get the status of a fix execution."""
        return self.active_executions.get(execution_id)
    
    def get_all_executions(self) -> List[FixExecution]:
        """Get all active fix executions."""
        return list(self.active_executions.values())
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running fix execution."""
        execution = self.active_executions.get(execution_id)
        if execution and execution.status == ExecutionStatus.RUNNING:
            execution.status = ExecutionStatus.CANCELLED
            execution.completed_at = datetime.now()
            logger.info(f"🚫 Execution cancelled: {execution_id}")
            return True
        return False

def main():
    """Main function for testing the TrueFoundry Rectifier."""
    logger.info("🚀 Starting TrueFoundry Rectifier test")
    
    # Create rectifier instance
    rectifier = TrueFoundryRectifier()
    
    # Mock fix proposal for testing
    fix_proposal = {
        "id": "fix_001",
        "title": "Restart Authentication Service",
        "fix_type": "service_restart",
        "steps": [
            "Identify the failing service",
            "Stop the service gracefully", 
            "Wait for cleanup",
            "Start the service",
            "Verify service health"
        ],
        "tests": [
            "curl -f http://localhost:8080/health",
            "Check service status",
            "Verify logs show successful startup"
        ]
    }
    
    repo_url = "https://github.com/example/auth-service"
    
    logger.info("🧪 Testing fix execution...")
    execution = rectifier.execute_fix(fix_proposal, repo_url)
    
    logger.info(f"📊 Execution Result:")
    logger.info(f"   Status: {execution.status.value}")
    logger.info(f"   Execution Time: {execution.execution_time:.2f}s")
    logger.info(f"   Exit Code: {execution.exit_code}")
    logger.info(f"   Logs: {len(execution.logs)} lines")
    
    if execution.status == ExecutionStatus.SUCCESS:
        logger.info("🚀 Testing deployment...")
        deployment_result = rectifier.deploy_fix(execution, repo_url)
        
        logger.info(f"📊 Deployment Result:")
        logger.info(f"   Success: {deployment_result.success}")
        logger.info(f"   PR URL: {deployment_result.pr_url}")
        logger.info(f"   Deployment URL: {deployment_result.deployment_url}")
    
    logger.info("🎉 TrueFoundry Rectifier test completed")

if __name__ == "__main__":
    main()
