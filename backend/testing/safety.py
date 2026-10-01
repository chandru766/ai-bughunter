from models.database import SystemConfig

class SafetyPolicy:
    MAX_REQUESTS_PER_TARGET = 10
    MAX_REQUESTS_PER_MINUTE = 5
    
    @staticmethod
    def is_kill_switch_active(db) -> bool:
        config = db.query(SystemConfig).filter(SystemConfig.key == "KILL_SWITCH").first()
        return config and config.value == "ACTIVE"
        
    @staticmethod
    def rate_limit_check(db, target_id: int) -> bool:
        # MVP Mock limit check
        return True
