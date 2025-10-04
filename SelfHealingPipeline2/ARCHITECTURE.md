# 🔄 Self-Healing Agent System Architecture

## Visual Pipeline Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Repo   │    │    Datadog      │    │   External      │
│   (Public)      │    │   Monitoring    │    │   Triggers      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │ Webhooks             │ Alerts               │ Events
          │ (issues, PRs,        │ (CPU, errors,        │ (manual,
          │  workflows, push)    │  latency)            │  scheduled)
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼──────────────┐
                    │                            │
                    │     MONITOR AGENT          │
                    │                            │
                    │ • Register webhooks        │
                    │ • Setup Datadog monitors   │
                    │ • Normalize payloads       │
                    │ • Event correlation        │
                    │                            │
                    └─────────────┬──────────────┘
                                  │
                                  │ Structured Problem JSON
                                  │
                    ┌─────────────▼──────────────┐
                    │                            │
                    │     REASONER AGENT         │
                    │                            │
                    │ • OpenAI/PhenomL API       │
                    │ • Analyze issue context    │
                    │ • Generate fix proposals   │
                    │ • Plan remediation steps   │
                    │                            │
                    └─────────────┬──────────────┘
                                  │
                                  │ Fix Proposal JSON
                                  │
                    ┌─────────────▼──────────────┐
                    │                            │
                    │     EXECUTOR AGENT         │
                    │                            │
                    │ • Create TrueFoundry Job   │
                    │ • Sandbox execution        │
                    │ • Validation & testing     │
                    │ • Production deployment    │
                    │                            │
                    └─────────────┬──────────────┘
                                  │
                                  │ Deployment Result
                                  │
                    ┌─────────────▼──────────────┐
                    │                            │
                    │     PRODUCTION             │
                    │                            │
                    │ • GitHub PR creation       │
                    │ • CI/CD pipeline trigger   │
                    │ • Automated merge/deploy   │
                    │ • Monitoring verification  │
                    │                            │
                    └────────────────────────────┘
```

## Data Flow Sequence

```
1. TRIGGER
   ┌─────────────┐
   │ GitHub PR   │ ──webhook──┐
   │ fails CI    │            │
   └─────────────┘            │
                              │
   ┌─────────────┐            │
   │ Datadog     │ ──alert────┼──┐
   │ API errors  │            │  │
   └─────────────┘            │  │
                              │  │
                              │  │
                              ▼  ▼
2. MONITOR AGENT
   ┌─────────────────────────────────────┐
   │ Normalized Event:                   │
   │ {                                   │
   │   "repo": "github.com/org/repo",    │
   │   "event": "PR failed",             │
   │   "commit": "sha123",               │
   │   "error": "test_login failed",     │
   │   "timestamp": "2025-01-04T14:22Z"  │
   │ }                                   │
   └─────────────────────────────────────┘
                              │
                              ▼
3. REASONER AGENT
   ┌─────────────────────────────────────┐
   │ Fix Proposal:                       │
   │ {                                   │
   │   "repo": "github.com/org/repo",    │
   │   "commit": "sha123",               │
   │   "proposed_fix": [                 │
   │     "Rollback config.yaml",         │
   │     "Restart auth-service"          │
   │   ],                                │
   │   "tests": [                        │
   │     "pytest tests/test_auth.py",    │
   │     "npm run lint"                  │
   │   ]                                 │
   │ }                                   │
   └─────────────────────────────────────┘
                              │
                              ▼
4. EXECUTOR AGENT
   ┌─────────────────────────────────────┐
   │ TrueFoundry Sandbox Job:            │
   │                                     │
   │ 1. Clone repo                       │
   │ 2. Checkout commit                  │
   │ 3. Apply fix                        │
   │ 4. Run tests                        │
   │ 5. Validate results                 │
   └─────────────────────────────────────┘
                              │
                              ▼
5. PRODUCTION DEPLOYMENT
   ┌─────────────────────────────────────┐
   │ 1. Create GitHub PR                 │
   │ 2. Trigger CI/CD pipeline           │
   │ 3. Merge if CI passes               │
   │ 4. Deploy to production             │
   │ 5. Monitor for success              │
   └─────────────────────────────────────┘
```

## Agent Responsibilities

### 🎯 Monitor Agent
- **Input**: GitHub webhooks, Datadog alerts, external triggers
- **Processing**: Event normalization, correlation, deduplication
- **Output**: Structured problem JSON
- **APIs Used**: GitHub API, Datadog API

### 🧠 Reasoner Agent  
- **Input**: Structured problem JSON
- **Processing**: Issue analysis, fix generation, remediation planning
- **Output**: Fix proposal with tests
- **APIs Used**: OpenAI API, PhenomL API

### ⚡ Executor Agent
- **Input**: Fix proposal JSON
- **Processing**: Sandbox testing, validation, production deployment
- **Output**: Deployment result and monitoring
- **APIs Used**: TrueFoundry API, GitHub API

## Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    TECHNOLOGY STACK                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🎯 MONITORING & TRIGGERS                                   │
│  ├─ GitHub API (webhooks, issues, PRs, workflows)          │
│  ├─ Datadog API (alerts, metrics, monitoring)              │
│  └─ External triggers (manual, scheduled, etc.)            │
│                                                             │
│  🧠 REASONING & AI                                          │
│  ├─ OpenAI API (GPT-4.1 for reasoning)                     │
│  ├─ PhenomL API (code-specific fixes)                      │
│  └─ Custom prompt engineering                              │
│                                                             │
│  ⚡ EXECUTION & DEPLOYMENT                                  │
│  ├─ TrueFoundry API (sandbox jobs, ephemeral containers)   │
│  ├─ GitHub API (PR creation, CI/CD triggers)               │
│  └─ Kubernetes/Docker (container orchestration)            │
│                                                             │
│  🔧 INFRASTRUCTURE                                          │
│  ├─ MCP (Model Context Protocol) for agent communication   │
│  ├─ JSON for data exchange                                  │
│  ├─ YAML for job specifications                            │
│  └─ Python for agent implementation                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Constraint & Safety Mechanisms

```
┌─────────────────────────────────────────────────────────────┐
│                    SAFETY CONSTRAINTS                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔄 LOOP PREVENTION                                         │
│  ├─ Max retries per issue (3 attempts)                     │
│  ├─ Time budget limits (10 min per sandbox job)            │
│  ├─ Deduplication (tag issues to prevent re-triggering)    │
│  └─ Cooldown periods between healing attempts              │
│                                                             │
│  🛡️ SANDBOX ISOLATION                                       │
│  ├─ TrueFoundry ephemeral containers                       │
│  ├─ No access to production secrets                        │
│  ├─ Limited network access (test endpoints only)           │
│  └─ Automatic cleanup after job completion                 │
│                                                             │
│  🚨 ESCALATION & MONITORING                                 │
│  ├─ Human notification on failure                          │
│  ├─ Slack/email alerts for critical issues                 │
│  ├─ Real-time monitoring via Datadog                       │
│  └─ Audit trail for all healing actions                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Example End-to-End Flow

### Scenario: Failed PR with Authentication Issues

```
1. 🚨 TRIGGER
   GitHub PR #123 fails CI with error: "test_login failed"
   Datadog shows spike in authentication errors

2. 📊 MONITOR AGENT
   Correlates GitHub webhook + Datadog alert
   Creates normalized event:
   {
     "repo": "github.com/company/auth-service",
     "event": "PR_CI_FAILED", 
     "commit": "abc123",
     "error": "test_login failed",
     "context": {
       "failed_tests": ["test_login", "test_token_validation"],
       "error_rate": 15.2,
       "affected_endpoints": ["/api/auth/login"]
     }
   }

3. 🧠 REASONER AGENT
   Analyzes context using OpenAI
   Generates fix proposal:
   {
     "proposed_fix": [
       "Rollback config.yaml to previous working version",
       "Restart auth-service container",
       "Update JWT secret configuration"
     ],
     "tests": [
       "pytest tests/test_auth.py::test_login",
       "pytest tests/test_auth.py::test_token_validation",
       "npm run lint"
     ]
   }

4. ⚡ EXECUTOR AGENT
   Creates TrueFoundry sandbox job:
   - Clone repo, checkout commit abc123
   - Apply proposed fixes
   - Run specified tests
   - All tests pass ✅

5. 🚀 PRODUCTION DEPLOYMENT
   - Create GitHub PR with fixes
   - Trigger CI/CD pipeline
   - CI passes → merge PR
   - Deploy to production
   - Monitor shows errors resolved ✅

6. ✅ VERIFICATION
   Monitor Agent confirms:
   - Authentication errors dropped to 0%
   - All health checks passing
   - Healing session completed successfully
```

## Benefits

- **🔄 Autonomous**: Fully automated healing without human intervention
- **🛡️ Safe**: Sandbox testing prevents production issues
- **⚡ Fast**: Minutes instead of hours for issue resolution
- **📊 Comprehensive**: Monitors both code and infrastructure
- **🔗 Integrated**: Works with existing GitHub and Datadog workflows
- **💰 Cost-effective**: Only uses resources when issues occur

## Scalability Considerations

- **Multi-repo support**: Single system can monitor multiple repositories
- **Concurrent healing**: Multiple healing sessions can run simultaneously
- **Resource optimization**: TrueFoundry jobs scale based on demand
- **API rate limiting**: Intelligent queuing and retry mechanisms
