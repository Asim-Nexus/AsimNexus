# ASIMNEXUS API Documentation

## 🌐 External Integration API Reference

**Base URL:** `https://api.asim-nexus.ai/v1`
**Authentication:** Bearer Token (API Key)
**Content-Type:** `application/json`

---

## Authentication

### Get API Key
```http
POST /auth/token
Content-Type: application/json

{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "scope": "agents:read agents:write"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "agents:read agents:write"
}
```

### Use API Key
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

---

## Company Agents API

### CEO Agent

#### Make Decision
```http
POST /agents/ceo/decision
Authorization: Bearer {token}

{
  "type": "hire",
  "title": "Hire Senior Developer",
  "description": "Need experienced Python developer",
  "amount": 120000,
  "urgency": "high",
  "data": {
    "candidate_name": "John Doe",
    "role": "Senior Developer",
    "salary": 10000
  }
}
```

**Response:**
```json
{
  "decision_id": "DEC-20240115-143022",
  "type": "major",
  "status": "pending",
  "recommendation": 0,
  "options": [
    {
      "option": "approve",
      "title": "Approve Hire",
      "description": "Hire John Doe as Senior Developer",
      "pros": ["Skills match", "Cultural fit"],
      "cons": ["Salary at upper range"],
      "cost": 120000
    }
  ],
  "estimated_impact": {
    "financial": 120000,
    "time_months": 3,
    "risk": "medium"
  }
}
```

#### Get Decision Status
```http
GET /agents/ceo/decision/{decision_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "decision_id": "DEC-20240115-143022",
  "status": "human_approved",
  "decided_at": "2024-01-15T14:35:00Z",
  "decided_by": "human@example.com",
  "reasoning": "Approved based on technical interview performance"
}
```

---

### Architect Agent

#### Design System
```http
POST /agents/architect/design
Authorization: Bearer {token}

{
  "title": "E-commerce API",
  "description": "API for online store",
  "expected_users": 50000,
  "peak_tps": 500,
  "data_volume_gb": 200,
  "integrations": ["payment_gateway", "shipping_api"],
  "team_size": 8,
  "budget": "medium",
  "latency_requirements": "low",
  "compliance": ["PCI"]
}
```

**Response:**
```json
{
  "design_id": "ARCH-20240115-143022-a1b2c3",
  "title": "E-commerce API",
  "pattern": "microservices",
  "complexity": "high",
  "components": [
    {
      "name": "API Gateway",
      "component_type": "gateway",
      "responsibilities": ["Request routing", "Rate limiting"],
      "technologies": ["Kong", "NGINX"]
    }
  ],
  "apis": [
    {
      "path": "/api/v1/auth/login",
      "method": "POST",
      "description": "User authentication",
      "auth_required": true
    }
  ],
  "scalability_plan": {
    "expected_users": 50000,
    "peak_tps": 500,
    "strategies": ["horizontal_scaling", "auto_scaling", "caching"]
  }
}
```

#### Export Design Document
```http
GET /agents/architect/design/{design_id}/export
Authorization: Bearer {token}
```

**Response:** Markdown document

---

### DevOps Agent

#### Create Pipeline
```http
POST /agents/devops/pipeline
Authorization: Bearer {token}

{
  "name": "E-commerce API Pipeline",
  "repository_url": "https://github.com/company/ecommerce-api",
  "branch": "main",
  "template": "python_api",
  "custom_steps": [
    {
      "name": "security_scan",
      "action": "security_scan"
    }
  ]
}
```

**Response:**
```json
{
  "pipeline_id": "PIPE-20240115-143022-a1b2c3",
  "name": "E-commerce API Pipeline",
  "steps": [
    {"name": "checkout", "action": "git_checkout"},
    {"name": "install", "action": "pip_install"},
    {"name": "test", "action": "run_tests"},
    {"name": "build", "action": "build_docker"},
    {"name": "deploy", "action": "deploy_k8s"}
  ]
}
```

#### Deploy
```http
POST /agents/devops/deploy/{pipeline_id}
Authorization: Bearer {token}

{
  "app_name": "ecommerce-api",
  "version": "2.0.0",
  "environment": "production",
  "provider": "aws",
  "region": "us-east-1",
  "resources": {
    "cpu": "2 vCPU",
    "memory": "4 GB",
    "instances": 3
  }
}
```

**Response:**
```json
{
  "deployment_id": "DEP-20240115-143022-a1b2c3",
  "status": "completed",
  "app_name": "ecommerce-api",
  "version": "2.0.0",
  "environment": "production",
  "logs": [
    "[2024-01-15T14:30:22] checkout: completed",
    "[2024-01-15T14:30:45] install: completed",
    "[2024-01-15T14:31:10] test: completed",
    "[2024-01-15T14:32:00] build: completed",
    "[2024-01-15T14:33:15] deploy: completed"
  ]
}
```

#### Provision Infrastructure
```http
POST /agents/devops/infrastructure
Authorization: Bearer {token}

{
  "provider": "aws",
  "region": "us-east-1",
  "resources": [
    {
      "type": "vm",
      "count": 3,
      "specs": {"tier": "medium", "cpu": 2, "memory": 4}
    },
    {
      "type": "database",
      "engine": "postgres",
      "tier": "standard"
    }
  ]
}
```

**Response:**
```json
{
  "resources": [
    {
      "resource_id": "RES-a1b2c3d4",
      "name": "vm-RES-a1b2c3d4",
      "resource_type": "vm",
      "provider": "aws",
      "region": "us-east-1",
      "status": "running",
      "cost_per_hour": 0.10
    }
  ],
  "total_cost_per_hour": 0.35
}
```

---

### Marketing Agent

#### Create Content
```http
POST /agents/marketing/content
Authorization: Bearer {token}

{
  "content_type": "blog_post",
  "platform": "website",
  "topic": "AI in Healthcare",
  "target_audience": "healthcare professionals",
  "tone": "professional",
  "key_points": [
    "AI improves diagnostic accuracy",
    "Reduces administrative burden",
    "Enhances patient outcomes"
  ],
  "seo_keywords": ["AI healthcare", "medical AI", "diagnostic AI"]
}
```

**Response:**
```json
{
  "content_id": "CONTENT-20240115-143022-a1b2c3",
  "title": "AI in Healthcare",
  "content_type": "blog_post",
  "platform": "website",
  "content": "# AI in Healthcare\n\nArtificial Intelligence is transforming...",
  "hashtags": ["#ASIMNEXUS", "#AI", "#Healthcare"],
  "seo_keywords": ["AI healthcare", "medical AI"],
  "call_to_action": "Subscribe to our newsletter"
}
```

#### Create Campaign
```http
POST /agents/marketing/campaign
Authorization: Bearer {token}

{
  "name": "Q1 Product Launch",
  "description": "Launch campaign for new AI feature",
  "goal": "brand_awareness",
  "target_audience": {
    "demographics": ["tech_professionals", "developers"],
    "interests": ["AI", "automation"]
  },
  "budget": 5000,
  "channels": ["linkedin", "twitter", "email"],
  "content_requests": [
    {
      "content_type": "social_media",
      "platform": "linkedin",
      "topic": "Product Launch Announcement"
    }
  ]
}
```

**Response:**
```json
{
  "campaign_id": "CAMP-20240115-143022-a1b2c3",
  "name": "Q1 Product Launch",
  "channels": ["linkedin", "twitter", "email"],
  "content_pieces": ["CONTENT-xxx", "CONTENT-yyy"],
  "status": "draft",
  "kpis": {
    "reach": 10000,
    "engagement": 500,
    "conversions": 50
  }
}
```

---

### Software Agency

#### Create Project
```http
POST /agents/software/project
Authorization: Bearer {token}

{
  "name": "Customer Portal",
  "description": "Self-service customer portal",
  "requirements": {
    "functional": [
      "User authentication",
      "Profile management",
      "Order tracking"
    ],
    "non_functional": [
      "99.9% uptime",
      "< 2s response time"
    ]
  },
  "tech_preferences": {
    "language": "python",
    "framework": "fastapi",
    "database": "postgresql"
  },
  "budget_hours": 200,
  "deadline": "2024-03-15T00:00:00Z"
}
```

**Response:**
```json
{
  "project_id": "PROJ-a1b2c3d4",
  "name": "Customer Portal",
  "status": "active",
  "current_stage": "implementation",
  "tasks": ["TASK-xxx", "TASK-yyy", "TASK-zzz"],
  "components": [
    {
      "name": "Auth Service",
      "type": "service",
      "technologies": ["FastAPI", "JWT", "Redis"]
    }
  ],
  "start_date": "2024-01-15T14:30:00Z",
  "target_completion": "2024-03-15T00:00:00Z"
}
```

#### Get Project Status
```http
GET /agents/software/project/{project_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "project_id": "PROJ-a1b2c3d4",
  "name": "Customer Portal",
  "status": "active",
  "current_stage": "implementation",
  "progress": {
    "tasks_total": 12,
    "tasks_completed": 5,
    "tasks_pending": 4,
    "tasks_in_progress": 3,
    "percentage": 41.7
  },
  "code": {
    "modules": 8,
    "languages": ["python", "javascript"],
    "avg_test_coverage": "87.5%"
  }
}
```

#### Get Quality Report
```http
GET /agents/software/project/{project_id}/quality
Authorization: Bearer {token}
```

**Response:**
```json
{
  "project_id": "PROJ-a1b2c3d4",
  "modules_analyzed": 8,
  "metrics": [
    {
      "module": "Auth Service",
      "test_coverage": "92.0%",
      "complexity": 3.5,
      "lint_score": "98.0%",
      "security": "95.0%"
    }
  ],
  "overall_grade": "A"
}
```

---

## System API

### Knowledge System

#### Create Knowledge Node
```http
POST /knowledge/node
Authorization: Bearer {token}

{
  "title": "Machine Learning Basics",
  "node_type": "concept",
  "content": "# ML Basics\n\nMachine learning is...",
  "tags": ["ai", "ml", "basics"],
  "source_url": "https://example.com/article",
  "importance": 4,
  "confidence": 0.95
}
```

**Response:**
```json
{
  "node_id": "machine_learning_basics",
  "title": "Machine Learning Basics",
  "node_type": "concept",
  "summary": "Introduction to machine learning concepts",
  "created_at": "2024-01-15T14:30:00Z",
  "links": {}
}
```

#### Search Knowledge
```http
GET /knowledge/search?q=machine+learning
Authorization: Bearer {token}
```

**Response:**
```json
{
  "results": [
    {
      "node_id": "machine_learning_basics",
      "title": "Machine Learning Basics",
      "type": "concept",
      "summary": "Introduction to machine learning",
      "score": 15
    }
  ],
  "total": 5
}
```

#### Link Nodes
```http
POST /knowledge/link
Authorization: Bearer {token}

{
  "from_node": "machine_learning_basics",
  "to_node": "neural_networks",
  "link_type": "related"
}
```

**Response:**
```json
{
  "success": true,
  "from": "machine_learning_basics",
  "to": "neural_networks",
  "type": "related"
}
```

---

### Agent Communication

#### Send Message
```http
POST /communication/message
Authorization: Bearer {token}

{
  "sender_id": "ceo_agent",
  "recipient_id": "architect_agent",
  "message_type": "task_request",
  "payload": {
    "task": "Design system architecture",
    "priority": "high"
  },
  "priority": 4,
  "requires_response": true,
  "timeout_seconds": 60
}
```

**Response:**
```json
{
  "message_id": "MSG-a1b2c3d4",
  "status": "delivered",
  "response": {
    "message_id": "MSG-response",
    "content": {
      "accepted": true,
      "estimated_completion": "2 hours"
    }
  }
}
```

#### Create Collaboration Session
```http
POST /communication/session
Authorization: Bearer {token}

{
  "name": "Project Alpha",
  "description": "Build new feature",
  "mode": "hierarchical",
  "coordinator_id": "ceo_agent",
  "participant_ids": ["architect_agent", "devops_agent"]
}
```

**Response:**
```json
{
  "session_id": "SESSION-a1b2c3d4",
  "name": "Project Alpha",
  "mode": "hierarchical",
  "participants": [
    {"agent_id": "ceo_agent", "role": "coordinator"},
    {"agent_id": "architect_agent", "role": "executor"}
  ],
  "status": "active"
}
```

---

### Monitoring & Analytics

#### Get Agent Performance
```http
GET /monitoring/agent/{agent_id}/performance?hours=24
Authorization: Bearer {token}
```

**Response:**
```json
{
  "agent_id": "architect_agent",
  "period_hours": 24,
  "overall_score": 0.92,
  "metric_scores": {
    "task_completion": 0.95,
    "response_time": 0.88,
    "error_rate": 0.98
  },
  "active_alerts": 0,
  "metrics_summary": {
    "task_completion": {
      "count": 12,
      "latest": 0.95,
      "mean": 0.94
    }
  }
}
```

#### Get System Overview
```http
GET /monitoring/system/overview
Authorization: Bearer {token}
```

**Response:**
```json
{
  "total_agents": 5,
  "monitored_agents": 5,
  "system_health": 0.94,
  "health_status": "healthy",
  "active_alerts": 2,
  "critical_alerts": 0,
  "warning_alerts": 2,
  "alerts_by_severity": {
    "critical": 0,
    "warning": 2,
    "info": 0
  }
}
```

#### Get Recommendations
```http
GET /monitoring/agent/{agent_id}/recommendations
Authorization: Bearer {token}
```

**Response:**
```json
{
  "recommendations": [
    {
      "priority": "high",
      "area": "task_completion",
      "issue": "Low task completion rate",
      "recommendation": "Review task complexity",
      "actions": ["Break tasks into smaller pieces"]
    }
  ]
}
```

---

## WebSocket API

### Real-time Updates

Connect to WebSocket for real-time agent updates:

```javascript
const ws = new WebSocket('wss://api.asim-nexus.ai/v1/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['agent_activity', 'system_alerts']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

### Message Types

**Agent Activity:**
```json
{
  "type": "agent_activity",
  "timestamp": "2024-01-15T14:30:00Z",
  "agent_id": "devops_agent",
  "action": "deployment_complete",
  "details": {
    "deployment_id": "DEP-xxx",
    "status": "success"
  }
}
```

**System Alert:**
```json
{
  "type": "system_alert",
  "timestamp": "2024-01-15T14:30:00Z",
  "severity": "warning",
  "agent_id": "architect_agent",
  "metric": "response_time",
  "message": "Response time above threshold",
  "current_value": 5200,
  "threshold": 5000
}
```

---

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "AGENT_NOT_FOUND",
    "message": "Agent with ID 'unknown_agent' not found",
    "details": {
      "agent_id": "unknown_agent"
    },
    "timestamp": "2024-01-15T14:30:00Z"
  }
}
```

### Common Error Codes
- `UNAUTHORIZED` - Invalid or missing token
- `AGENT_NOT_FOUND` - Agent doesn't exist
- `TASK_NOT_FOUND` - Task doesn't exist
- `INVALID_REQUEST` - Malformed request
- `RATE_LIMITED` - Too many requests
- `AGENT_BUSY` - Agent unavailable
- `TIMEOUT` - Request timeout

---

## Rate Limits

- **Free tier:** 100 requests/minute
- **Pro tier:** 1000 requests/minute
- **Enterprise:** Custom limits

Rate limit headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705326600
```

---

## SDK Examples

### Python SDK
```python
from asim_nexus import ASIMClient

client = ASIMClient(api_key="your_api_key")

# Create project
project = client.software.create_project({
    "name": "Customer Portal",
    "description": "Self-service portal"
})

# Get decision from CEO
decision = client.ceo.make_decision({
    "type": "hire",
    "title": "Hire Developer",
    "amount": 100000
})
```

### JavaScript SDK
```javascript
import { ASIMClient } from '@asim-nexus/sdk';

const client = new ASIMClient({ apiKey: 'your_api_key' });

// Deploy application
const deployment = await client.devops.deploy({
  pipelineId: 'PIPE-xxx',
  config: {
    app_name: 'my-app',
    environment: 'production'
  }
});
```

---

## Support

- **API Status:** https://status.asim-nexus.ai
- **Documentation:** https://docs.asim-nexus.ai
- **Support Email:** api-support@asim-nexus.ai

---

**API Version:** 1.0.0
**Last Updated:** 2024-01-15
