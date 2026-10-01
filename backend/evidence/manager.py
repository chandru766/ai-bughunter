import hashlib
import re

class EvidenceManager:
    @staticmethod
    def calculate_hash(content: str) -> str:
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @staticmethod
    def verify_integrity(content: str, original_hash: str) -> bool:
        current_hash = EvidenceManager.calculate_hash(content)
        return current_hash == original_hash

    @staticmethod
    def redact_sensitive_data(content: str) -> str:
        # Deterministic redaction pipeline
        patterns = {
            r'(?i)(Authorization:\s*Bearer\s+)[^\r\n]+': r'\1[REDACTED]',
            r'(?i)(Cookie:\s*.*?(?:session|sid|token)=)[^;\r\n]+': r'\1[REDACTED]',
            r'(?i)("?(?:api_key|apikey|password|secret|access_token)"?\s*[:=]\s*"?)[\w\-]+("?)': r'\1[REDACTED]\2',
            r'(ey[a-zA-Z0-9_-]{10,}\.ey[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,})': r'[REDACTED_JWT]'
        }
        
        redacted_content = content
        for pattern, replacement in patterns.items():
            redacted_content = re.sub(pattern, replacement, redacted_content)
            
        return redacted_content

    @classmethod
    def process_evidence(cls, content: str, evidence_type: str, description: str):
        redacted_content = cls.redact_sensitive_data(content)
        is_redacted = redacted_content != content
        
        content_hash = cls.calculate_hash(redacted_content)
        
        return {
            "content": redacted_content,
            "content_hash": content_hash,
            "original_hash": content_hash, # For safety, we only ever store and hash the redacted version
            "redaction_status": is_redacted
        }
