import json
import logging
import uuid
import contextvars
from datetime import datetime

# Context variable for the current request ID
request_id_ctx = contextvars.ContextVar('request_id', default=None)

class StructuredJSONLogger(logging.Handler):
    def __init__(self, filename=None):
        super().__init__()
        self.filename = filename

    def emit(self, record):
        try:
            req_id = request_id_ctx.get()
            log_record = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "event": getattr(record, 'event', 'APPLICATION_LOG'),
                "message": record.getMessage(),
                "request_id": req_id
            }

            # Add any extra fields passed in the `extra` dict
            for key, value in record.__dict__.items():
                if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
                               'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
                               'msecs', 'message', 'msg', 'name', 'pathname', 'process',
                               'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName', 'event', 'request_id']:
                    log_record[key] = value

            log_entry = json.dumps(log_record)
            print(log_entry)
            
            if self.filename:
                with open(self.filename, 'a') as f:
                    f.write(log_entry + '\n')
                    
        except Exception as e:
            print(f"FAILED TO LOG: {str(e)}")

# Set up the logger
logger = logging.getLogger("ai_bughunter")
logger.setLevel(logging.INFO)
logger.handlers = []

# Optional: Add file handler if needed, currently writing to stdout
json_handler = StructuredJSONLogger()
logger.addHandler(json_handler)

def get_request_id():
    req_id = request_id_ctx.get()
    if not req_id:
        req_id = str(uuid.uuid4())
        request_id_ctx.set(req_id)
    return req_id

def set_request_id(req_id: str):
    request_id_ctx.set(req_id)

def log_event(event: str, level: int = logging.INFO, **kwargs):
    logger.log(level, "", extra={"event": event, **kwargs})
