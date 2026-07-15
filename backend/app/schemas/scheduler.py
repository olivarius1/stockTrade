from pydantic import BaseModel

class SchedulerConfig(BaseModel):
    schedule_type: str
    cron_expression: str
    enabled: bool = True
    include_ai: bool = False
    financial_update_frequency: int = 7
