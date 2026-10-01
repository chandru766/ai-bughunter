import jwt

class JWTAnalyzer:
    @staticmethod
    def analyze(token: str):
        try:
            header = jwt.get_unverified_header(token)
            payload = jwt.decode(token, options={"verify_signature": False})
            return {
                "header": header,
                "payload": payload,
                "claims": list(payload.keys())
            }
        except Exception as e:
            return {"error": str(e)}
