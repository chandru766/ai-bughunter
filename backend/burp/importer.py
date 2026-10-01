import base64
import hashlib
from defusedxml import ElementTree

class BurpXMLImporter:
    @staticmethod
    def calculate_hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()
        
    @staticmethod
    def parse(xml_content: bytes, validator) -> dict:
        try:
            # DefusedXML prevents XXE and entity expansion attacks natively
            root = ElementTree.fromstring(xml_content)
        except Exception as e:
            raise ValueError("Malformed or dangerous XML structure detected. Parsing aborted.")

        results = {
            "total": 0, 
            "imported": 0, 
            "in_scope": 0, 
            "blocked": 0, 
            "duplicates": 0, 
            "items": []
        }
        
        seen_hashes = set()
        
        for item in root.findall('item'):
            results["total"] += 1
            url = item.findtext('url', '')
            if not url:
                continue
            
            # Scope Enforcement (HARD SECURITY BOUNDARY)
            decision = validator.evaluate(url)
            if decision.value != "IN_SCOPE":
                results["blocked"] += 1
                continue
                
            results["in_scope"] += 1
            
            req_elem = item.find('request')
            req_b64 = req_elem.text if req_elem is not None else ""
            try:
                req_raw = base64.b64decode(req_b64).decode('utf-8', errors='ignore')
            except:
                req_raw = ""
            
            resp_elem = item.find('response')
            resp_b64 = resp_elem.text if resp_elem is not None else ""
            try:
                resp_raw = base64.b64decode(resp_b64).decode('utf-8', errors='ignore')
            except:
                resp_raw = ""
                
            status_code = item.findtext('status', '0')
            method = item.findtext('method', 'GET')
            
            # Fingerprinting for duplicates (Method + URL + Body Content)
            fp = hashlib.sha256(f"{method}|{url}|{req_raw}".encode()).hexdigest()
            if fp in seen_hashes:
                results["duplicates"] += 1
                continue
                
            seen_hashes.add(fp)
            
            results["items"].append({
                "url": url,
                "method": method,
                "request_raw": req_raw,
                "response_raw": resp_raw,
                "status_code": int(status_code)
            })
            results["imported"] += 1
            
        return results
