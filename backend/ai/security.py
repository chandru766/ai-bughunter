from observability.logger import log_event

class PromptInjectionDefense:
    @staticmethod
    def sanitize_context(retrieved_docs: list) -> str:
        """
        Architectural defense: 
        Explicitly mark retrieved context as untrusted boundaries.
        """
        sanitized = ""
        for doc in retrieved_docs:
            content = doc.get('content', '')
            if "ignore all previous instructions" in content.lower():
                log_event("PROMPT_INJECTION_BLOCKED", level=30, source="RAG_CONTEXT")
            sanitized += f"\n[UNTRUSTED RAG CONTEXT ID: {doc.get('id', 'N/A')}]\n{content}\n[END UNTRUSTED]"
        return sanitized

    @staticmethod
    def sanitize_http(http_content: str) -> str:
        """
        Explicitly demarcate Target Data.
        """
        if "ignore all previous instructions" in http_content.lower() or "you are now" in http_content.lower():
            log_event("PROMPT_INJECTION_BLOCKED", level=30, source="HTTP_RESPONSE")
        return f"\n[UNTRUSTED HTTP CONTENT]\n{http_content}\n[END UNTRUSTED]"
