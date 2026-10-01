import enum
import uuid
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bughunter.db")
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def generate_uuid(): return str(uuid.uuid4())

class FindingStatus(str, enum.Enum):
    NEW = "NEW"; ANALYZING = "ANALYZING"; NEEDS_VALIDATION = "NEEDS_VALIDATION"
    VALIDATED = "VALIDATED"; FALSE_POSITIVE = "FALSE_POSITIVE"; DUPLICATE = "DUPLICATE"
    REPORTED = "REPORTED"; CLOSED = "CLOSED"

class ValidationStatus(str, enum.Enum):
    UNVALIDATED = "UNVALIDATED"; RESEARCHER_CONFIRMED = "RESEARCHER_CONFIRMED"; RESEARCHER_REJECTED = "RESEARCHER_REJECTED"

class TestLevel(str, enum.Enum):
    PASSIVE = "PASSIVE"
    SAFE_ACTIVE = "SAFE_ACTIVE"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    BLOCKED = "BLOCKED"

class TestStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    BLOCKED = "BLOCKED"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    ANALYZED = "ANALYZED"

class ResearchSessionStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, default=generate_uuid, unique=True, index=True)
    name = Column(String, index=True)
    url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class ScopeRuleModel(Base):
    __tablename__ = "scope_rules"
    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"))
    pattern = Column(String)
    is_exclusion = Column(Boolean, default=False)
    
class Target(Base):
    __tablename__ = "targets"
    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"))
    url = Column(String)
    
class Endpoint(Base):
    __tablename__ = "endpoints"
    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"))
    path = Column(String)
    method = Column(String)
    
class HttpRequest(Base):
    __tablename__ = "http_requests"
    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id"))
    headers = Column(JSON)
    body = Column(Text)
    
class HttpResponse(Base):
    __tablename__ = "http_responses"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("http_requests.id"))
    status_code = Column(Integer)
    
class Finding(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, default=generate_uuid, unique=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"))
    title = Column(String)
    category = Column(String)
    severity = Column(String)
    status = Column(SQLEnum(FindingStatus), default=FindingStatus.NEW, index=True)
    validation_status = Column(SQLEnum(ValidationStatus), default=ValidationStatus.UNVALIDATED)
    
class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(Integer, primary_key=True, index=True)
    finding_id = Column(Integer, ForeignKey("findings.id"))
    
class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    finding_id = Column(Integer, ForeignKey("findings.id"))
    markdown_content = Column(Text, nullable=True)
    json_content = Column(JSON, nullable=True)
    report_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    action = Column(String)
    object = Column(String)
    result = Column(String)
    request_id = Column(String, index=True, nullable=True)
    severity = Column(String, default="INFO")

class BurpImport(Base):
    __tablename__ = "burp_imports"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    in_scope_records = Column(Integer, default=0)
    blocked_records = Column(Integer, default=0)
    duplicates = Column(Integer, default=0)

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True)
    title = Column(String)
    source_type = Column(String) 
    
class AiAnalysisLog(Base):
    __tablename__ = "ai_analysis_logs"
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String)
    status = Column(String)

# --- NEW PHASE 8 MODELS ---
class SystemConfig(Base):
    __tablename__ = "system_config"
    key = Column(String, primary_key=True)
    value = Column(String)

class TestPlan(Base):
    __tablename__ = "test_plans"
    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id"), nullable=True)
    recommendation_id = Column(Integer, nullable=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=True)
    test_category = Column(String)
    method = Column(String)
    url = Column(String)
    parameters = Column(JSON, nullable=True)
    safety_level = Column(SQLEnum(TestLevel), default=TestLevel.APPROVAL_REQUIRED)
    requires_human_approval = Column(Boolean, default=True)
    status = Column(SQLEnum(TestStatus), default=TestStatus.PLANNED, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class TestResult(Base):
    __tablename__ = "test_results"
    id = Column(Integer, primary_key=True, index=True)
    test_plan_id = Column(Integer, ForeignKey("test_plans.id"))
    status = Column(SQLEnum(TestStatus))
    request_raw = Column(Text)
    response_raw = Column(Text)
    observations = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class FindingChain(Base):
    __tablename__ = "finding_chains"
    id = Column(Integer, primary_key=True, index=True)
    findings = Column(JSON)
    relationships = Column(JSON, nullable=True)
    combined_impact = Column(Text)
    validation_status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuthType(str, enum.Enum):
    JWT = "JWT"
    COOKIE = "COOKIE"
    API_KEY = "API_KEY"
    CUSTOM_HEADER = "CUSTOM_HEADER"

class AuthenticationContext(Base):
    __tablename__ = "auth_contexts"
    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=True)
    name = Column(String)
    account_label = Column(String)
    auth_type = Column(SQLEnum(AuthType))
    encrypted_secret = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    enabled = Column(Boolean, default=True)

class AuthenticationMutation(Base):
    __tablename__ = "auth_mutations"
    id = Column(Integer, primary_key=True, index=True)
    test_plan_id = Column(Integer, ForeignKey("test_plans.id"))
    source_context_id = Column(Integer, ForeignKey("auth_contexts.id"))
    target_context_id = Column(Integer, ForeignKey("auth_contexts.id"))
    mutation_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# --- NEW PHASE 19 MODELS ---
class ResearchSession(Base):
    __tablename__ = "research_sessions"
    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"))
    name = Column(String)
    status = Column(SQLEnum(ResearchSessionStatus), default=ResearchSessionStatus.PLANNED)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ResearchRecommendation(Base):
    __tablename__ = "research_recommendations"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id"))
    endpoint = Column(String)
    possible_test_categories = Column(JSON)
    reasoning = Column(JSON)
    missing_evidence = Column(JSON)
    recommended_manual_validation = Column(JSON)
    confidence = Column(String)
    status = Column(String, default="PENDING") # PENDING, ACCEPTED, REJECTED
    created_at = Column(DateTime, default=datetime.utcnow)

class ResearchNote(Base):
    __tablename__ = "research_notes"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# --- NEW PHASE 20 MODELS ---

class AIAppStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class AIApplication(Base):
    __tablename__ = "ai_applications"
    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"))
    name = Column(String)
    base_url = Column(String)
    description = Column(Text)
    status = Column(SQLEnum(AIAppStatus), default=AIAppStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)

class AIEndpoint(Base):
    __tablename__ = "ai_endpoints"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("ai_applications.id"))
    method = Column(String)
    path = Column(String)
    content_type = Column(String, default="application/json")
    authentication_required = Column(Boolean, default=True)

class AITestCategory(str, enum.Enum):
    PROMPT_INJECTION = "PROMPT_INJECTION"
    INDIRECT_PROMPT_INJECTION = "INDIRECT_PROMPT_INJECTION"
    RAG_POISONING = "RAG_POISONING"
    SENSITIVE_INFORMATION_DISCLOSURE = "SENSITIVE_INFORMATION_DISCLOSURE"
    SYSTEM_PROMPT_LEAKAGE = "SYSTEM_PROMPT_LEAKAGE"
    INSECURE_OUTPUT_HANDLING = "INSECURE_OUTPUT_HANDLING"
    TOOL_ABUSE = "TOOL_ABUSE"
    EXCESSIVE_AGENCY = "EXCESSIVE_AGENCY"
    AUTHORIZATION = "AUTHORIZATION"
    MODEL_BEHAVIOR = "MODEL_BEHAVIOR"
    INPUT_VALIDATION = "INPUT_VALIDATION"

class AITestCase(Base):
    __tablename__ = "ai_test_cases"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("ai_applications.id"))
    endpoint_id = Column(Integer, ForeignKey("ai_endpoints.id"), nullable=True)
    category = Column(SQLEnum(AITestCategory))
    test_name = Column(String)
    description = Column(Text)
    safety_level = Column(SQLEnum(TestLevel), default=TestLevel.APPROVAL_REQUIRED)
    requires_human_approval = Column(Boolean, default=True)
    status = Column(SQLEnum(TestStatus), default=TestStatus.PLANNED)
    created_at = Column(DateTime, default=datetime.utcnow)

# --- NEW PHASE 21 MODELS ---

class AgentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"

class AgentType(str, enum.Enum):
    COORDINATOR = "COORDINATOR"
    RECONNAISSANCE = "RECONNAISSANCE"
    WEB_SECURITY = "WEB_SECURITY"
    API_SECURITY = "API_SECURITY"
    AUTHORIZATION = "AUTHORIZATION"
    AI_SECURITY = "AI_SECURITY"
    EVIDENCE = "EVIDENCE"
    REPORTING = "REPORTING"

class AIAgent(Base):
    __tablename__ = "ai_agents"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("ai_applications.id"))
    program_id = Column(Integer, ForeignKey("programs.id"))
    name = Column(String)
    description = Column(Text)
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.ACTIVE)
    agent_type = Column(SQLEnum(AgentType), default=AgentType.WEB_SECURITY)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ToolRiskLevel(str, enum.Enum):
    READ_ONLY = "READ_ONLY"
    LOW_IMPACT = "LOW_IMPACT"
    HIGH_IMPACT = "HIGH_IMPACT"
    BLOCKED = "BLOCKED"

class AgentTool(Base):
    __tablename__ = "agent_tools"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("ai_agents.id"))
    name = Column(String)
    description = Column(Text)
    risk_level = Column(SQLEnum(ToolRiskLevel), default=ToolRiskLevel.READ_ONLY)
    enabled = Column(Boolean, default=True)
    requires_approval = Column(Boolean, default=False)
    schema_def = Column(JSON, nullable=True) # JSON Schema for arguments

class PermissionState(str, enum.Enum):
    ALLOWED = "ALLOWED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    BLOCKED = "BLOCKED"

class ToolPermission(Base):
    __tablename__ = "tool_permissions"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("ai_agents.id"))
    tool_id = Column(Integer, ForeignKey("agent_tools.id"))
    user_identity = Column(String, nullable=True) # Bind to a specific synthetic user identity if needed
    state = Column(SQLEnum(PermissionState), default=PermissionState.BLOCKED)

# --- NEW PHASE 22 MODELS ---

class AgentCapability(Base):
    __tablename__ = "agent_capabilities"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("ai_agents.id"))
    capability_name = Column(String) # e.g. WEB_ANALYSIS, REPORT_GENERATION
    resource_type = Column(String) # e.g. ENDPOINT, FINDING
    allowed_actions = Column(String) # e.g. READ, ANALYZE, MODIFY

class MessageType(str, enum.Enum):
    TASK_REQUEST = "TASK_REQUEST"
    TASK_RESPONSE = "TASK_RESPONSE"
    EVIDENCE_REQUEST = "EVIDENCE_REQUEST"
    EVIDENCE_RESPONSE = "EVIDENCE_RESPONSE"
    ANALYSIS_REQUEST = "ANALYSIS_REQUEST"
    ANALYSIS_RESPONSE = "ANALYSIS_RESPONSE"
    APPROVAL_REQUEST = "APPROVAL_REQUEST"
    STATUS_UPDATE = "STATUS_UPDATE"

class MessageStatus(str, enum.Enum):
    DELIVERED = "DELIVERED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"

class AgentMessage(Base):
    __tablename__ = "agent_messages"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, index=True)
    sender_agent_id = Column(Integer, ForeignKey("ai_agents.id"))
    receiver_agent_id = Column(Integer, ForeignKey("ai_agents.id"))
    message_type = Column(SQLEnum(MessageType))
    resource_id = Column(String, nullable=True)
    payload = Column(JSON)
    payload_hash = Column(String)
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.DELIVERED)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AgentTaskStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"

class AgentTask(Base):
    __tablename__ = "agent_tasks"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String)
    assigned_agent_id = Column(Integer, ForeignKey("ai_agents.id"))
    task_type = Column(String)
    resource_id = Column(String, nullable=True)
    status = Column(SQLEnum(AgentTaskStatus), default=AgentTaskStatus.QUEUED)
    created_at = Column(DateTime, default=datetime.utcnow)
