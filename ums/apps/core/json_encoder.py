# your_app_name/json_encoders.py
import json
from datetime import date, datetime

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat() # Converts date/datetime to ISO 8601 string (e.g., "2025-06-28")
        # Let the base class default method raise the TypeError for other types
        return super().default(obj)