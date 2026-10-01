class SecretRedactor:
    @staticmethod
    def redact(content: str) -> str:
        if not content:
            return ""
        if len(content) > 15:
            return content[:5] + "...[REDACTED]"
        return "[REDACTED]"
