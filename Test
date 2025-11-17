# TCS AutoAssist - Essential Implementation Guide

## 🎯 Project Overview

**TCS AutoAssist** is an intelligent chatbot system for DC Automation Support Team featuring:
- **Multi-tier AI**: OpenAI GPT-4 → Ollama Llama 3.2 → Rule-based fallbacks
- **Category-based Routing**: General, TCS Internal, Monitoring, Knowledge Base
- **Real-time Problem Resolution**: Server issues, API diagnostics, incident management
- **Enterprise Integration**: Splunk, Ansible, Confluence APIs

---

## 📊 Database Structure

### Database: `TCS_autoassist`

#### Core Tables Schema:

```sql
-- 👤 Users Table
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user',
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 💬 Chat Conversations Table
CREATE TABLE chat_conversations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(255) DEFAULT 'New Conversation',
    status ENUM('active', 'archived', 'deleted') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 📝 Chat Messages Table
CREATE TABLE chat_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT NOT NULL,
    sender_type ENUM('user', 'bot', 'system') NOT NULL,
    message_content TEXT NOT NULL,
    message_metadata JSON NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES chat_conversations(id) ON DELETE CASCADE
);

-- 🎫 Incident Management Table
CREATE TABLE query_resolutions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT NOT NULL,
    user_id INT NOT NULL,
    incident_id VARCHAR(50) UNIQUE,
    query_type VARCHAR(50),
    server_name VARCHAR(100),
    correlation_id VARCHAR(100),
    root_cause TEXT,
    resolution_steps TEXT,
    status ENUM('open', 'in_progress', 'resolved', 'closed') DEFAULT 'open',
    ai_service_used VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES chat_conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

## 🏗️ System Architecture Flow

```mermaid
graph TB
    A[👤 User Input] --> B[🎯 Category Selection]
    B --> C[📱 React Frontend<br/>Port 3000]
    C --> D[🌐 API Gateway<br/>FastAPI Port 8000]
    
    D --> E[🔐 JWT Authentication]
    E --> F[🧠 GPT Service<br/>Core Intelligence Engine]
    
    F --> G{📋 Category Router}
    G -->|General| H[🤖 OpenAI GPT-4]
    G -->|TCS Internal| I[📊 Knowledge Base Search]
    G -->|Monitoring| J[🔍 Splunk/Ansible APIs]
    G -->|Knowledge Base| K[📚 Confluence/Docs]
    
    H --> L[🦙 Ollama Fallback]
    L --> M[⚙️ Built-in Responses]
    
    I --> N[📈 CSV Server Issues DB]
    J --> O[📊 External Monitoring APIs]
    K --> P[📄 Text Documentation]
    
    N --> Q[🔧 Resolution Generator]
    O --> Q
    P --> Q
    M --> Q
    
    Q --> R[💾 Save to MySQL]
    R --> S[📱 Update UI Response]
    
    style F fill:#9c27b0,stroke:#6a1b9a,color:#fff
    style H fill:#4caf50,stroke:#2e7d32,color:#fff
    style L fill:#ff9800,stroke:#ef6c00,color:#fff
    style R fill:#f44336,stroke:#c62828,color:#fff
```

---

## 💻 Essential Files Structure

### Backend Core Files (FastAPI):

```
backend/
├── app/
│   ├── main.py                    # 🚀 Application Entry Point
│   ├── core/
│   │   ├── config.py             # ⚙️ Settings & Environment
│   │   ├── database.py           # 🗄️ MySQL Connection
│   │   └── security.py           # 🔒 JWT Authentication
│   ├── models/
│   │   ├── user.py               # 👤 User Data Models  
│   │   └── chat.py               # 💬 Chat Data Models
│   ├── api/
│   │   ├── auth.py               # 🔐 Login/Register APIs
│   │   ├── chat.py               # 💬 Chat Message APIs
│   │   └── admin.py              # 👨‍💼 Admin Management
│   ├── services/
│   │   ├── gpt_service.py        # 🧠 MAIN AI ENGINE
│   │   ├── csv_knowledge_service.py # 📊 Server Issues DB
│   │   └── enhanced_knowledge_service.py # 🔍 Multi-source Search
│   └── data/
│       └── knowledge_base.csv    # 🏦 TCS Server Issues Data
├── requirements.txt              # 📦 Python Dependencies
└── .env                         # 🔑 Configuration File
```

### Frontend Core Files (React TypeScript):

```
frontend/
├── src/
│   ├── App.tsx                   # 🏠 Main Application
│   ├── pages/
│   │   ├── LoginPage.tsx         # 🔑 Authentication
│   │   ├── ChatPage.tsx          # 💬 MAIN CHAT INTERFACE
│   │   └── IncidentsPage.tsx     # 🎫 Incident Management
│   ├── services/
│   │   └── api.ts                # 🔌 Backend Communication
│   └── components/
│       └── Layout.tsx            # 🏗️ App Layout
├── package.json                  # 📦 Dependencies
└── .env                         # 🌐 API Configuration
```

---

## 🧠 Core Intelligence Engine Logic

### GPTService - The Brain (`gpt_service.py`)

**Main Function**: `process_user_query()`

```python
async def process_user_query(self, message: str, category: str = None, 
                           server_name: str = None, correlation_id: str = None, 
                           user_context: Dict = None) -> Dict:
    """
    🎯 MAIN INTELLIGENCE ROUTING ENGINE
    
    Processing Flow:
    1. Category Detection → Route to appropriate handler
    2. Knowledge Search → Check databases & external sources  
    3. AI Processing → OpenAI → Ollama → Built-in fallback
    4. Response Generation → Format structured response
    """
    
    # 🎯 Priority 1: Category-based Routing
    if category:
        return await self._handle_category_based_query(
            message, category, server_name, correlation_id, user_context
        )
    
    # 🔍 Priority 2: Technical Issue Detection
    if self._has_technical_issue_context(message):
        return await self._search_enhanced_knowledge_base(
            message, server_name, user_context
        )
    
    # 📚 Priority 3: General Information
    return self._provide_guidance_response(user_context)
```

### Category Handlers:

#### 1. General Educational Queries:
```python
async def _handle_general_educational_query(self, message: str, user_context: Dict):
    """
    📚 EDUCATIONAL QUERY PROCESSING
    
    Tier 1: OpenAI GPT-4 (Primary AI)
    Tier 2: Ollama Llama 3.2 (Local Fallback)  
    Tier 3: Built-in Responses (Final Fallback)
    """
    
    # 🥇 Try OpenAI GPT-4 first
    try:
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "user", 
                "content": f"Provide comprehensive educational response: {message}"
            }],
            temperature=0.7,
            max_tokens=600
        )
        
        return {
            "message": f"📚 **Educational Response**\n\n{response.choices[0].message.content}",
            "ai_service_used": "openai_educational",
            "data_sources": ["OpenAI GPT-4", "Educational Knowledge"]
        }
    except Exception:
        # 🥈 Fallback to Ollama
        return await self._get_ollama_educational_response(message, user_context)
```

#### 2. TCS Internal Issues:
```python
async def _handle_TCS_internal_issue(self, message: str, server_name: str, 
                                     correlation_id: str, user_context: Dict):
    """
    🏦 TCS TECHNICAL ISSUE RESOLUTION
    
    Process:
    1. Extract server name (gb-, cn-, hk-, vn-, mx-, etc.)
    2. Classify issue type (auth, payload, performance, config)
    3. Search CSV knowledge base for matching solutions
    4. Query external APIs (Splunk, Ansible) for real-time data
    5. Generate structured resolution response
    """
    
    # 🔍 Server extraction & standardization
    if not server_name:
        server_name = self._extract_server_name(message)
    
    # 📊 Search knowledge base
    csv_results = self.csv_knowledge.search_issues(message, server_name)
    
    if csv_results:
        # ✅ Found existing solution
        return self._format_knowledge_base_response(csv_results[0])
    
    # 🔍 Query external APIs for real-time data
    api_data = await self._query_external_apis(message, server_name)
    
    # 🧠 AI analysis of the issue
    return await self._analyze_technical_issue(message, server_name, api_data)
```

#### 3. System Monitoring:
```python
async def _handle_monitoring_query(self, message: str, server_name: str, 
                                  correlation_id: str, user_context: Dict):
    """
    📊 SYSTEM MONITORING DATA ANALYSIS
    
    Sources:
    - Splunk API: Log analysis, error tracking
    - Ansible API: Automation status, deployment data
    - Performance metrics: CPU, memory, disk usage
    """
    
    monitoring_data = {}
    
    # 📋 Query Splunk for logs
    if correlation_id:
        monitoring_data['splunk_logs'] = await self._query_splunk_logs(correlation_id)
    
    # 🤖 Query Ansible for automation data
    if server_name:
        monitoring_data['ansible_data'] = await self._query_ansible_status(server_name)
    
    # 📊 Analyze monitoring data
    return self._analyze_monitoring_data(monitoring_data, message)
```

### Knowledge Base Structure:

#### CSV Server Issues Database (`knowledge_base.csv`):
```csv
issue_id,server_name,issue_type,error_code,description,root_cause,resolution_steps,priority
1,gb-api-01,auth_issue,401,"Authentication failed","JWT token expired","Check token expiration | Regenerate API token | Update headers | Retry request",medium
2,cn-db-server,performance_issue,500,"Database connection timeout","Connection pool exhausted","Monitor connection pool | Increase pool size | Restart service",high
3,hk-web-prod,payload_issue,400,"Invalid JSON format","Missing required fields","Validate JSON structure | Check required fields | Update request format",low
```

#### Server Naming Convention Recognition:
```python
def _extract_server_name(self, message: str) -> str:
    """
    🏦 TCS Server Naming Pattern Recognition
    
    Patterns:
    - gb-* : Great Britain/UK servers
    - cn-* : China servers  
    - hk-* : Hong Kong servers
    - vn-* : Vietnam servers
    - mx-* : Mexico servers
    - us-* : United States servers
    - ca-* : Canada servers
    - au-* : Australia servers
    - sg-* : Singapore servers
    - my-* : Malaysia servers
    - in-* : India servers
    - ae-* : UAE servers
    - fr-* : France servers
    - de-* : Germany servers
    """
    
    server_patterns = [
        r'\b(gb|cn|hk|vn|mx|us|ca|au|sg|my|in|ae|fr|de)-[a-zA-Z0-9-]+\b'
    ]
    
    for pattern in server_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(0).lower()
    
    return None
```

---

## 📱 Frontend Implementation

### Main Chat Interface (`ChatPage.tsx`)

**Core Features**:
1. **Category Selection Dialog**: 4 categories with descriptions
2. **Real-time Chat Interface**: Message bubbles, typing indicators
3. **Response Processing**: Markdown rendering, code highlighting
4. **Incident Management**: Create tickets, track resolutions

#### Category Selection Logic:
```typescript
const categoryOptions = [
    {
        id: 'general',
        title: 'General Question',
        description: 'Educational queries, tutorials, best practices',
        icon: '📚',
        color: '#2196F3'
    },
    {
        id: 'TCS_internal', 
        title: 'TCS Internal Issue',
        description: 'Server problems, API errors, technical issues',
        icon: '🏦', 
        color: '#DB0011'  // TCS Red
    },
    {
        id: 'monitoring',
        title: 'System Monitoring', 
        description: 'Splunk logs, Ansible data, performance metrics',
        icon: '📊',
        color: '#FF9800'
    },
    {
        id: 'knowledge_base',
        title: 'Internal Knowledge',
        description: 'Documentation, procedures, team knowledge', 
        icon: '📖',
        color: '#4CAF50'
    }
];
```

#### Message Sending Flow:
```typescript
const sendMessage = async () => {
    // 🎯 Ensure category is selected for new conversations
    if (!selectedCategory && !currentConversationId) {
        setShowCategorySelector(true);
        return;
    }
    
    // 📤 Send message with category context
    const messageData = {
        message: inputMessage,
        category: selectedCategory,
        conversation_id: currentConversationId || undefined,
        server_name: extractServerName(inputMessage),
        correlation_id: extractCorrelationId(inputMessage)
    };
    
    try {
        const response = await apiService.sendMessage(messageData);
        
        // 🎨 Display bot response with formatting
        displayBotResponse(response);
        
        // 💾 Save conversation state
        if (response.conversation_id) {
            setCurrentConversationId(response.conversation_id);
        }
    } catch (error) {
        console.error('Message send error:', error);
    }
};
```

### API Communication (`api.ts`):

```typescript
class ApiService {
    private api: AxiosInstance;
    
    constructor() {
        this.api = axios.create({
            baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
            timeout: 30000
        });
        
        // 🔒 JWT token interceptor
        this.api.interceptors.request.use((config) => {
            const token = localStorage.getItem('access_token');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        });
    }
    
    // 💬 Send chat message
    async sendMessage(messageData: MessageRequest): Promise<MessageResponse> {
        const response = await this.api.post('/api/chat/send-message', messageData);
        return response.data;
    }
    
    // 👤 User authentication
    async login(username: string, password: string): Promise<LoginResponse> {
        const response = await this.api.post('/api/auth/login', {
            username,
            password
        });
        return response.data;
    }
}
```

---

## 🔧 Configuration Files

### Backend Environment (`.env`):
```bash
# 🗄️ Database Configuration
DATABASE_URL=mysql+pymysql://TCS_user:secure_password@localhost:3306/TCS_autoassist

# 🔐 Security Settings  
SECRET_KEY=your-32-character-jwt-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 🧠 AI Services
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
OPENAI_MODEL=gpt-4

# 🦙 Ollama Fallback (Optional)
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
USE_OLLAMA_FALLBACK=true

# 🔌 External APIs
SPLUNK_API_URL=https://your-splunk-instance.com
SPLUNK_API_TOKEN=your-splunk-token
ANSIBLE_API_URL=https://your-ansible-tower.com  
ANSIBLE_API_TOKEN=your-ansible-token

# 🏢 Corporate Settings
COMPANY_NAME=TCS
DEPARTMENT=DC Automation Support Team
BOT_NAME=DC AutoAssist
```

### Frontend Environment (`.env`):
```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_COMPANY_NAME=TCS
REACT_APP_BOT_NAME=DC AutoAssist
```

### Python Dependencies (`requirements.txt`):
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pymysql==1.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
openai==1.3.7
requests==2.31.0
pandas==2.1.3
python-dotenv==1.0.0
mysql-connector-python==8.2.0
cryptography==41.0.7
```

### Node.js Dependencies (`package.json`):
```json
{
  "name": "TCS-autoassist-frontend",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0", 
    "typescript": "^4.9.5",
    "@mui/material": "^5.14.18",
    "@mui/icons-material": "^5.14.18",
    "@emotion/react": "^11.11.1",
    "@emotion/styled": "^11.11.0",
    "axios": "^1.6.2",
    "react-router-dom": "^6.18.0",
    "react-markdown": "^9.0.1"
  }
}
```

---

## 🚀 Quick Deployment Steps

### 1. Database Setup:
```sql
-- Create database and user
CREATE DATABASE TCS_autoassist;
CREATE USER 'TCS_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON TCS_autoassist.* TO 'TCS_user'@'localhost';

-- Run table creation scripts (from schema above)
-- Insert sample data for testing
```

### 2. Backend Deployment:
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run application
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Frontend Deployment:
```bash
# Install Node.js dependencies
npm install

# Configure API endpoint
echo "REACT_APP_API_URL=http://your-backend-server:8000" > .env

# Build and serve
npm run build
npx serve -s build -l 3000
```

---

## 📊 Sample API Requests & Responses

### 1. Educational Query:
**Request**:
```json
POST /api/chat/send-message
{
  "message": "What is REST API?",
  "category": "general"
}
```

**Response**:
```json
{
  "message": "📚 **Educational Response**\n\n# REST API Fundamentals\n\nREST (Representational State Transfer) is an architectural style for designing networked applications...",
  "conversation_id": 123,
  "ai_service_used": "openai_educational", 
  "data_sources": ["OpenAI GPT-4", "Educational Knowledge"],
  "suggestions": ["Learn about HTTP methods", "API authentication patterns"],
  "processing_time": "2.3s"
}
```

### 2. Technical Issue:
**Request**:
```json
POST /api/chat/send-message
{
  "message": "gb-api-01 showing 401 error",
  "category": "TCS_internal", 
  "server_name": "gb-api-01"
}
```

**Response**:
```json
{
  "message": "🔧 **Technical Issue Resolution**\n\n**Server**: gb-api-01 (UK Region)\n**Issue**: Authentication Error (401)\n\n**Resolution Steps**:\n1. Check JWT token expiration\n2. Regenerate API token\n3. Update request headers\n4. Retry request\n\n**Root Cause**: Token expired after 24 hours",
  "ai_service_used": "knowledge_base_match",
  "data_sources": ["CSV Knowledge Base", "Server Issues DB"],
  "incident_required": false,
  "knowledge_base_match": true,
  "server_region": "UK",
  "issue_priority": "medium"
}
```

---

## 💡 Key Implementation Points for Your Team

### 🎯 **Why Category-First Approach**:
1. **Intelligent Routing**: Different categories need different AI processing
2. **Resource Optimization**: Avoid expensive API calls for simple queries  
3. **Context Preservation**: Category provides essential context for AI
4. **User Experience**: Clear expectations for response type

### 🧠 **Multi-tier AI Strategy**:
1. **Primary**: OpenAI GPT-4 for comprehensive responses
2. **Fallback**: Ollama Llama 3.2 for when OpenAI unavailable
3. **Final**: Built-in responses for guaranteed availability
4. **Smart Routing**: Category determines which tier to use first

### 📊 **Knowledge Base Design**:
1. **CSV Format**: Easy to maintain, version control friendly
2. **Structured Data**: Consistent fields for reliable matching
3. **Server Patterns**: Recognizes TCS naming conventions
4. **Issue Classification**: Systematic categorization for quick resolution

### 🔒 **Security Considerations**:
1. **JWT Authentication**: Stateless, secure token-based auth
2. **Environment Variables**: Sensitive data not in code
3. **Input Validation**: Prevents injection attacks
4. **CORS Configuration**: Controlled cross-origin access

---

This guide provides your team with all essential implementation details while being concise enough for corporate environments with code access restrictions. The modular design allows for gradual implementation and customization based on your specific TCS requirements! 🎉
