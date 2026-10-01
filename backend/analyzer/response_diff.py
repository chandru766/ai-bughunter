import json

class BaselineEngine:
    @staticmethod
    def compare(baseline_status: int, baseline_headers: dict, baseline_body: str,
                test_status: int, test_headers: dict, test_body: str) -> dict:
        
        diff = {
            "status_changed": baseline_status != test_status,
            "headers_changed": baseline_headers != test_headers,
            "body_changed": baseline_body != test_body,
            "response_size_difference": len(test_body) - len(baseline_body),
            "fields_added": [],
            "fields_removed": [],
            "fields_modified": []
        }
        
        try:
            b_json = json.loads(baseline_body)
            t_json = json.loads(test_body)
            
            if isinstance(b_json, dict) and isinstance(t_json, dict):
                b_keys = set(b_json.keys())
                t_keys = set(t_json.keys())
                
                diff["fields_added"] = list(t_keys - b_keys)
                diff["fields_removed"] = list(b_keys - t_keys)
                
                common_keys = b_keys.intersection(t_keys)
                diff["fields_modified"] = [k for k in common_keys if b_json[k] != t_json[k]]
        except json.JSONDecodeError:
            pass 
            
        return diff
