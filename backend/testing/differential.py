class DifferentialEngine:
    @staticmethod
    def compare(old_status: int, old_body: str, new_status: int, new_body: str) -> dict:
        diff = {
            "status_changed": old_status != new_status,
            "new_status": new_status,
            "old_status": old_status,
            "body_length_diff": len(new_body) - len(old_body),
            "meaningful_difference": False
        }
        if diff["status_changed"] or abs(diff["body_length_diff"]) > 50:
            diff["meaningful_difference"] = True
        return diff
