import re
from urllib.parse import urlparse
from enum import Enum

class ScopeDecision(Enum):
    IN_SCOPE = "IN_SCOPE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    UNKNOWN = "UNKNOWN"

class ScopeRule:
    def __init__(self, pattern: str, is_exclusion: bool = False):
        self.pattern = pattern
        self.is_exclusion = is_exclusion
        
        # Determine if pattern includes scheme/path or just hostname
        if "://" in pattern or "/" in pattern:
            self.match_type = "url"
            regex_str = re.escape(pattern).replace(r'\*', '.*')
        else:
            self.match_type = "hostname"
            regex_str = re.escape(pattern).replace(r'\*', '.*')
            
        self.regex = re.compile(f"^{regex_str}$", re.IGNORECASE)

    def matches(self, url: str) -> bool:
        if self.match_type == "url":
            return bool(self.regex.match(url))
        else:
            parsed = urlparse(url)
            # Fallback if urlparse treats a scheme-less domain as a path
            hostname = parsed.hostname or url.split('/')[0]
            # Strip scheme if it was parsed
            if "://" in url and parsed.hostname:
                hostname = parsed.hostname
            return bool(self.regex.match(hostname))

class ScopeValidator:
    def __init__(self):
        self.rules = []

    def add_rule(self, pattern: str, is_exclusion: bool = False):
        self.rules.append(ScopeRule(pattern, is_exclusion))

    def evaluate(self, url: str) -> ScopeDecision:
        try:
            parsed = urlparse(url)
            if parsed.scheme and parsed.scheme.lower() not in ["http", "https"]:
                return ScopeDecision.OUT_OF_SCOPE
            # Normalize to prevent basic bypasses
            url = url.strip()
        except Exception:
            return ScopeDecision.OUT_OF_SCOPE

        # Check exclusions first, they are a hard boundary
        for rule in self.rules:
            if rule.is_exclusion and rule.matches(url):
                return ScopeDecision.OUT_OF_SCOPE
                
        # Check inclusions
        for rule in self.rules:
            if not rule.is_exclusion and rule.matches(url):
                return ScopeDecision.IN_SCOPE
                
        # If not explicitly included, it is unknown/blocked
        return ScopeDecision.UNKNOWN
