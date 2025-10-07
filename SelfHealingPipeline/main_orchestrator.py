#!/usr/bin/env python3
"""
Self-Healing Pipeline Orchestrator
Main entry point for the self-healing application that coordinates
between Identifier, Executioner, and Rectifier components.
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Import our pipeline components
from Identifier.identifierAdapter import identify_issues
from Executioner.sandbox_executor import SandboxExecutor
from Rectifier.production_rectifier import ProductionRectifier
from utils.constraint_manager import ConstraintManager
from utils.monitoring import MonitoringSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('self_healing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PipelineStatus(Enum):
    IDENTIFYING = "identifying"
    TESTING = "testing"
    RECTIFYING = "rectifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CONSTRAINED = "constrained"

@dataclass
class HealingSession:
    """Represents a single healing session with all its metadata."""
    session_id: str
    repo_url: str
    start_time: datetime
    status: PipelineStatus
    issues_identified: List[Dict]
    solutions_tested: List[Dict]
    fixes_applied: List[Dict]
    constraints_triggered: List[str]
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)

class SelfHealingOrchestrator:
    """
    Main orchestrator for the self-healing pipeline.
    Manages the flow between identification, testing, and rectification.
    """
    
    def __init__(self, config_path: str = "config/healing_config.json"):
        self.config = self._load_config(config_path)
        self.constraint_manager = ConstraintManager(self.config.get("constraints", {}))
        self.monitoring = MonitoringSystem()
        self.active_sessions: Dict[str, HealingSession] = {}
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Return default configuration."""
        return {
            "max_execution_time": 3600,  # 1 hour
            "max_retries_per_issue": 3,
            "max_concurrent_sessions": 5,
            "sandbox_timeout": 300,  # 5 minutes
            "constraints": {
                "max_loops_per_issue": 2,
                "cooldown_period": 1800,  # 30 minutes
                "blacklist_patterns": ["database_down", "network_outage"]
            },
            "datadog": {
                "api_key": os.getenv("DATADOG_API_KEY"),
                "app_key": os.getenv("DATADOG_APP_KEY")
            }
        }
    
    def start_healing_session(self, repo_url: str, trigger_source: str = "datadog") -> str:
        """
        Start a new healing session for a repository.
        
        Args:
            repo_url: GitHub repository URL
            trigger_source: Source that triggered the healing (datadog, manual, etc.)
            
        Returns:
            session_id: Unique identifier for this healing session
        """
        session_id = f"healing_{int(time.time())}_{hash(repo_url) % 10000}"
        
        # Check constraints before starting
        if not self.constraint_manager.can_start_session(repo_url):
            logger.warning(f"Session blocked by constraints for {repo_url}")
            return None
            
        # Check if we have too many active sessions
        if len(self.active_sessions) >= self.config["max_concurrent_sessions"]:
            logger.error("Maximum concurrent sessions reached")
            return None
        
        session = HealingSession(
            session_id=session_id,
            repo_url=repo_url,
            start_time=datetime.now(),
            status=PipelineStatus.IDENTIFYING,
            issues_identified=[],
            solutions_tested=[],
            fixes_applied=[],
            constraints_triggered=[]
        )
        
        self.active_sessions[session_id] = session
        logger.info(f"Started healing session {session_id} for {repo_url}")
        
        # Start the healing process asynchronously
        self._execute_healing_pipeline(session_id)
        
        return session_id
    
    def _execute_healing_pipeline(self, session_id: str):
        """
        Execute the complete healing pipeline for a session.
        """
        session = self.active_sessions.get(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return
        
        try:
            # Step 1: Identify Issues
            logger.info(f"Step 1: Identifying issues for {session.repo_url}")
            session.status = PipelineStatus.IDENTIFYING
            issues = identify_issues(session.repo_url)
            session.issues_identified = issues.get("issues", [])
            
            if not session.issues_identified:
                logger.info(f"No issues identified for {session.repo_url}")
                session.status = PipelineStatus.COMPLETED
                return
            
            # Step 2: Test Solutions in Sandbox
            logger.info(f"Step 2: Testing solutions in sandbox")
            session.status = PipelineStatus.TESTING
            executor = SandboxExecutor(self.config)
            tested_solutions = []
            
            for issue in session.issues_identified:
                if self.constraint_manager.is_issue_constrained(issue):
                    logger.warning(f"Issue {issue['id']} is constrained, skipping")
                    session.constraints_triggered.append(f"issue_{issue['id']}_constrained")
                    continue
                
                solution = executor.test_solution(issue, session.repo_url)
                if solution:
                    tested_solutions.append(solution)
                    session.solutions_tested.append(solution)
            
            if not tested_solutions:
                logger.warning("No valid solutions found after testing")
                session.status = PipelineStatus.FAILED
                return
            
            # Step 3: Apply Fixes to Production
            logger.info(f"Step 3: Applying fixes to production")
            session.status = PipelineStatus.RECTIFYING
            rectifier = ProductionRectifier(self.config)
            applied_fixes = []
            
            for solution in tested_solutions:
                if self.constraint_manager.can_apply_fix(solution):
                    fix_result = rectifier.apply_fix(solution, session.repo_url)
                    if fix_result["success"]:
                        applied_fixes.append(fix_result)
                        session.fixes_applied.append(fix_result)
                    else:
                        logger.error(f"Failed to apply fix: {fix_result['error']}")
                else:
                    logger.warning(f"Fix constrained: {solution['id']}")
                    session.constraints_triggered.append(f"fix_{solution['id']}_constrained")
            
            # Step 4: Complete Session
            session.status = PipelineStatus.COMPLETED
            session.execution_time = (datetime.now() - session.start_time).total_seconds()
            
            logger.info(f"Healing session {session_id} completed successfully")
            logger.info(f"Applied {len(applied_fixes)} fixes")
            
            # Update constraints and monitoring
            self.constraint_manager.update_session_history(session)
            self.monitoring.record_session_completion(session)
            
        except Exception as e:
            logger.error(f"Healing session {session_id} failed: {str(e)}")
            session.status = PipelineStatus.FAILED
            session.execution_time = (datetime.now() - session.start_time).total_seconds()
            
        finally:
            # Clean up session after a delay
            self._schedule_session_cleanup(session_id)
    
    def _schedule_session_cleanup(self, session_id: str):
        """Schedule cleanup of completed session."""
        # In a real implementation, you might use a background task queue
        # For now, we'll just log the completion
        logger.info(f"Session {session_id} cleanup scheduled")
    
    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """Get the current status of a healing session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session_id,
            "status": session.status.value,
            "execution_time": session.execution_time,
            "issues_identified": len(session.issues_identified),
            "solutions_tested": len(session.solutions_tested),
            "fixes_applied": len(session.fixes_applied),
            "constraints_triggered": len(session.constraints_triggered)
        }
    
    def get_all_sessions(self) -> List[Dict]:
        """Get status of all active sessions."""
        return [self.get_session_status(session_id) for session_id in self.active_sessions.keys()]
    
    def stop_session(self, session_id: str) -> bool:
        """Stop an active healing session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.status = PipelineStatus.FAILED
            logger.info(f"Session {session_id} stopped by user")
            return True
        return False

def main():
    """Main entry point for the self-healing orchestrator."""
    orchestrator = SelfHealingOrchestrator()
    
    # Example usage
    repo_url = "https://github.com/example/repo"
    session_id = orchestrator.start_healing_session(repo_url)
    
    if session_id:
        print(f"Started healing session: {session_id}")
        
        # Monitor the session
        while True:
            status = orchestrator.get_session_status(session_id)
            if status and status["status"] in ["completed", "failed"]:
                print(f"Session completed with status: {status['status']}")
                break
            time.sleep(5)

if __name__ == "__main__":
    main()
