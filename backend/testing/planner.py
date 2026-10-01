from models.database import TestPlan, TestLevel, TestStatus

class TestPlanner:
    @staticmethod
    def create_plan(program_id: int, target_id: int, url: str, method: str, test_category: str, parameters: dict = None) -> TestPlan:
        # Architectural Policy: Safe categories only
        safe_categories = ["Response comparison", "Information exposure analysis", "Security-header analysis"]
        approval_categories = ["Authorization comparison", "Authentication-state comparison"]
        
        if test_category in approval_categories:
            level = TestLevel.APPROVAL_REQUIRED
            requires_approval = True
        elif test_category in safe_categories:
            level = TestLevel.SAFE_ACTIVE
            requires_approval = False
        else:
            level = TestLevel.PASSIVE
            requires_approval = False
            
        return TestPlan(
            program_id=program_id,
            target_id=target_id,
            url=url,
            method=method,
            test_category=test_category,
            parameters=parameters or {},
            safety_level=level,
            requires_human_approval=requires_approval,
            status=TestStatus.PLANNED
        )
