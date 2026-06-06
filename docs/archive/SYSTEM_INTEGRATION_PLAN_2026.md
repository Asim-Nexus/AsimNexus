# ASIMNEXUS System Integration Plan 2026 (नेपाली/English)

## परिचय (Introduction)

यो दस्तावेजले ASIMNEXUS का सबै प्रणालीहरूलाई कसरी जोड्ने भनेर विस्तृत योजना प्रदान गर्छ।

This document provides a detailed plan for integrating all ASIMNEXUS systems.

---

## CURRENT INTEGRATION STATUS (वर्तमान एकीकरण स्थिति)

### Working Integrations (काम गर्ने एकीकरण):

1. **Infinite Brain ↔ Personal Clone** ✅
   - Personal Clone uses Infinite Brain for memory storage
   - Personality profiles stored in graph
   - Knowledge profiles stored in graph

2. **Infinite Brain ↔ Chat Integration** ✅
   - Chat uses ScopedRetriever for context
   - Chat creates notes from conversations
   - Chat builds graph context for queries

3. **Personal Clone ↔ Chat Integration** ✅
   - Chat uses Personal Clone for personalization
   - Chat adapts responses based on personality
   - Chat records interactions in Personal Clone

### Missing Integrations (हराइरहेको एकीकरण):

1. **Frontend ↔ Backend** ❌
2. **Backend ↔ Database** ❌
3. **World Systems ↔ Infinite Brain** ❌
4. **API Gateway ↔ Core Systems** ❌
5. **Authentication ↔ All Systems** ❌

---

## INTEGRATION ARCHITECTURE (एकीकरण वास्तुकला)

### Target Architecture:

```
┌─────────────────────────────────────────────────┐
│           User Interface Layer                  │
│  (React / Web / Mobile / Desktop / AR/VR)       │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│           API Gateway Layer                     │
│  (Authentication / Rate Limiting / Routing)     │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│           Service Layer                          │
│  (Chat Service / Personal Clone Service /        │
│   World Systems Service / Security Service)      │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│           Core Layer                             │
│  (Infinite Brain / Personal Clone /             │
│   World Systems / Security Audit)               │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│           Data Layer                            │
│  (PostgreSQL / Redis / Vector DB / Neo4j)       │
└─────────────────────────────────────────────────┘
```

---

## INTEGRATION STEPS (एकीकरण चरणहरू)

### Phase 1: Database Integration (डाटाबेस एकीकरण)

**Step 1.1: Setup PostgreSQL**
```python
# File: core/database/postgresql.py
import asyncpg
from typing import Optional

class PostgreSQLConnection:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None
    
    async def connect(self):
        self.pool = await asyncpg.create_pool(self.connection_string)
    
    async def execute(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
```

**Step 1.2: Setup Redis**
```python
# File: core/database/redis.py
import redis.asyncio as redis
from typing import Optional

class RedisConnection:
    def __init__(self, host: str = "localhost", port: int = 6379):
        self.host = host
        self.port = port
        self.client = None
    
    async def connect(self):
        self.client = await redis.Redis(host=self.host, port=self.port)
    
    async def set(self, key: str, value: str, expire: Optional[int] = None):
        await self.client.set(key, value, ex=expire)
    
    async def get(self, key: str):
        return await self.client.get(key)
```

**Step 1.3: Setup Vector DB (ChromaDB)**
```python
# File: core/database/vector_db.py
import chromadb
from chromadb.config import Settings

class VectorDBConnection:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.client = None
    
    def connect(self):
        self.client = chromadb.PersistentClient(path=self.persist_directory)
    
    def get_or_create_collection(self, name: str):
        return self.client.get_or_create_collection(name)
```

**Step 1.4: Setup Neo4j (Optional for Graph)**
```python
# File: core/database/neo4j.py
from neo4j import AsyncGraphDatabase

class Neo4jConnection:
    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
    
    async def connect(self):
        self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    async def execute_query(self, query: str, parameters: dict = None):
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            return await result.data()
```

---

### Phase 2: Authentication System (प्रमाणीकरण प्रणाली)

**Step 2.1: Create JWT Authentication**
```python
# File: core/auth/jwt_auth.py
import jwt
from datetime import datetime, timedelta
from typing import Optional

class JWTAuth:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def create_token(self, user_id: str, expires_in: int = 3600) -> str:
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['user_id']
        except:
            return None
```

**Step 2.2: Create User Management**
```python
# File: core/auth/user_manager.py
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class User:
    user_id: str
    username: str
    email: str
    password_hash: str
    created_at: datetime
    roles: List[str]

class UserManager:
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def create_user(self, username: str, email: str, password: str) -> User:
        # Hash password and create user
        pass
    
    async def get_user(self, user_id: str) -> Optional[User]:
        # Get user from database
        pass
    
    async def verify_credentials(self, username: str, password: str) -> Optional[User]:
        # Verify credentials
        pass
```

---

### Phase 3: API Gateway Implementation (API गेटवे कार्यान्वयन)

**Step 3.1: Create API Gateway**
```python
# File: core/api_gateway/gateway.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from core.auth.jwt_auth import JWTAuth

class APIGateway:
    def __init__(self):
        self.app = FastAPI()
        self.jwt_auth = JWTAuth(secret_key="your-secret-key")
        self._setup_middleware()
        self._setup_routes()
    
    def _setup_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
    
    def _setup_routes(self):
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy"}
        
        @self.app.post("/auth/login")
        async def login(request: Request):
            # Login logic
            pass
        
        @self.app.get("/api/chat")
        async def chat_endpoint(request: Request):
            # Chat endpoint
            pass

def get_api_gateway():
    return APIGateway()
```

---

### Phase 4: Service Layer Implementation (सेवा तह कार्यान्वयन)

**Step 4.1: Create Chat Service**
```python
# File: services/chat_service.py
from core.infinite_brain.chat_integration import get_chat_integration
from core.infinite_brain.personal_clone import get_personal_clone

class ChatService:
    def __init__(self):
        self.chat_integration = get_chat_integration()
        self.personal_clone = get_personal_clone("default")
    
    async def process_message(self, user_id: str, message: str) -> dict:
        # Process message with chat integration
        result = self.chat_integration.process_query(message, user_id)
        
        # Record interaction
        self.personal_clone.record_interaction(
            query=message,
            response=result['response'],
            context={},
            satisfaction_score=None
        )
        
        return result

def get_chat_service():
    return ChatService()
```

**Step 4.2: Create Personal Clone Service**
```python
# File: services/personal_clone_service.py
from core.infinite_brain.personal_clone import get_personal_clone

class PersonalCloneService:
    def __init__(self):
        self.clones = {}
    
    def get_clone(self, user_id: str):
        if user_id not in self.clones:
            self.clones[user_id] = get_personal_clone(user_id)
        return self.clones[user_id]
    
    async def create_profile(self, user_id: str, profile_data: dict):
        clone = self.get_clone(user_id)
        return clone.create_personality_profile(**profile_data)
    
    async def get_summary(self, user_id: str):
        clone = self.get_clone(user_id)
        return clone.get_interaction_summary()

def get_personal_clone_service():
    return PersonalCloneService()
```

**Step 4.3: Create World Systems Service**
```python
# File: services/world_systems_service.py
from core.world.global_financial_systems import GlobalFinancialSystemsIntegration

class WorldSystemsService:
    def __init__(self):
        self.financial_systems = GlobalFinancialSystemsIntegration()
    
    async def get_financial_data(self) -> dict:
        return {
            "institutions": len(self.financial_systems.institutions),
            "transactions": len(self.financial_systems.transactions)
        }
    
    async def create_transaction(self, transaction_data: dict):
        # Create transaction logic
        pass

def get_world_systems_service():
    return WorldSystemsService()
```

---

### Phase 5: Frontend-Backend Connection (Frontend-Backend कनेक्सन)

**Step 5.1: Create API Client in Frontend**
```javascript
// File: frontend/react/src/services/apiClient.js
class APIClient {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('token');
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  setToken(token) {
    this.token = token;
    localStorage.setItem('token', token);
  }
}

export const apiClient = new APIClient();
```

**Step 5.2: Create Chat Component**
```javascript
// File: frontend/react/src/components/ChatInterface.jsx
import React, { useState } from 'react';
import { apiClient } from '../services/apiClient';

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages([...messages, userMessage]);

    try {
      const response = await apiClient.post('/api/chat', {
        message: input,
      });

      const assistantMessage = { role: 'assistant', content: response.response };
      setMessages([...messages, userMessage, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
    }

    setInput('');
  };

  return (
    <div className="chat-interface">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>
      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}

export default ChatInterface;
```

---

### Phase 6: World Systems Integration (विश्व प्रणाली एकीकरण)

**Step 6.1: Connect World Systems to Infinite Brain**
```python
# File: core/integrations/world_brain_integration.py
from core.infinite_brain.node_classifier import get_node_classifier
from core.infinite_brain.graph_maintainer import get_graph_maintainer
from core.world.global_financial_systems import GlobalFinancialSystemsIntegration

class WorldBrainIntegration:
    def __init__(self):
        self.classifier = get_node_classifier()
        self.maintainer = get_graph_maintainer()
        self.financial_systems = GlobalFinancialSystemsIntegration()
    
    async def sync_financial_data(self):
        """Sync financial data to Infinite Brain"""
        for institution in self.financial_systems.institutions.values():
            # Create atomic note for each institution
            note_content = f"Financial institution: {institution.name}, Type: {institution.type}, Country: {institution.country}"
            
            atomic_notes = self.classifier.create_atomic_notes(note_content)
            for note in atomic_notes:
                self.maintainer.add_note(note)
        
        return {"synced": len(self.financial_systems.institutions)}
    
    async def sync_education_data(self):
        """Sync education data to Infinite Brain"""
        # Similar implementation for education
        pass
    
    async def sync_environment_data(self):
        """Sync environment data to Infinite Brain"""
        # Similar implementation for environment
        pass

def get_world_brain_integration():
    return WorldBrainIntegration()
```

---

### Phase 7: Configuration Management (कन्फिगरेसन व्यवस्थापन)

**Step 7.1: Create config.json**
```json
{
  "database": {
    "postgresql": {
      "host": "localhost",
      "port": 5432,
      "database": "asimnexus",
      "user": "asimnexus",
      "password": "your-password"
    },
    "redis": {
      "host": "localhost",
      "port": 6379
    },
    "neo4j": {
      "uri": "bolt://localhost:7687",
      "user": "neo4j",
      "password": "your-password"
    }
  },
  "api": {
    "host": "localhost",
    "port": 8000,
    "secret_key": "your-secret-key"
  },
  "integrations": {
    "openai": {
      "api_key": "your-openai-key"
    },
    "anthropic": {
      "api_key": "your-anthropic-key"
    }
  }
}
```

**Step 7.2: Create .env file**
```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=asimnexus
POSTGRES_USER=asimnexus
POSTGRES_PASSWORD=your-password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# API
API_HOST=localhost
API_PORT=8000
API_SECRET_KEY=your-secret-key

# LLM
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

---

## INTEGRATION TESTING (एकीकरण परीक्षण)

### Test 1: Database Connection
```python
# File: tests/test_database_integration.py
async def test_postgresql_connection():
    from core.database.postgresql import PostgreSQLConnection
    db = PostgreSQLConnection("postgresql://user:pass@localhost/db")
    await db.connect()
    result = await db.execute("SELECT 1")
    assert result is not None
```

### Test 2: Authentication Flow
```python
# File: tests/test_auth_flow.py
async def test_login_flow():
    from core.auth.user_manager import UserManager
    from core.auth.jwt_auth import JWTAuth
    
    user_manager = UserManager(db_connection)
    user = await user_manager.create_user("testuser", "test@example.com", "password")
    
    jwt_auth = JWTAuth("secret")
    token = jwt_auth.create_token(user.user_id)
    
    verified_user_id = jwt_auth.verify_token(token)
    assert verified_user_id == user.user_id
```

### Test 3: API Gateway
```python
# File: tests/test_api_gateway.py
async def test_api_gateway():
    from core.api_gateway.gateway import get_api_gateway
    from fastapi.testclient import TestClient
    
    gateway = get_api_gateway()
    client = TestClient(gateway.app)
    
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### Test 4: End-to-End Integration
```python
# File: tests/test_e2e_integration.py
async def test_e2e_chat_flow():
    # 1. User logs in
    # 2. User sends chat message
    # 3. Message processed through chat service
    # 4. Response generated
    # 5. Interaction recorded in personal clone
    # 6. Note created in infinite brain
    pass
```

---

## DEPLOYMENT PLAN (प्रसारण योजना)

### Step 1: Docker Setup
```dockerfile
# File: Dockerfile
FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Docker Compose
```yaml
# File: docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: asimnexus
      POSTGRES_USER: asimnexus
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  neo4j:
    image: neo4j:5
    environment:
      NEO4J_AUTH: neo4j/password
    ports:
      - "7474:7474"
      - "7687:7687"

  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - neo4j
```

### Step 3: Kubernetes Deployment
```yaml
# File: k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: asimnexus-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: asimnexus-api
  template:
    metadata:
      labels:
        app: asimnexus-api
    spec:
      containers:
      - name: api
        image: asimnexus/api:latest
        ports:
        - containerPort: 8000
```

---

## SUMMARY (सारांश)

### Integration Priority:

**Phase 1 (Critical - Week 1):**
1. Database setup (PostgreSQL, Redis, Vector DB)
2. Authentication system (JWT, User Management)
3. Configuration files (config.json, .env)

**Phase 2 (High - Week 2):**
1. API Gateway implementation
2. Service layer (Chat, Personal Clone, World Systems)
3. Frontend API client

**Phase 3 (Medium - Week 3):**
1. World Systems to Infinite Brain integration
2. Frontend-Backend connection
3. Integration testing

**Phase 4 (Low - Week 4):**
1. Docker setup
2. Kubernetes deployment
3. Monitoring and logging

### Expected Outcome:

After completing all phases, ASIMNEXUS will have:
- ✅ Fully integrated database layer
- ✅ Working authentication system
- ✅ Running API gateway
- ✅ Connected frontend and backend
- ✅ World systems integrated with Infinite Brain
- ✅ Deployable with Docker/Kubernetes
- ✅ Production-ready architecture

यो एकीकरण योजना पूरा भएपछि, ASIMNEXUS एक पूर्ण रूपमा एकीकृत, उत्पादन-तयार प्रणाली हुनेछ।
