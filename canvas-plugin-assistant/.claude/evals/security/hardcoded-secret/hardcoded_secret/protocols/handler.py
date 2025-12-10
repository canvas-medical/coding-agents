"""
Eval case: Handler with hardcoded API token.

VULNERABILITY: This handler has a hardcoded JWT token instead of using secrets.
The security review should detect this and flag it as HIGH severity.
"""

from canvas_sdk.effects import Effect
from canvas_sdk.events import EventType
from canvas_sdk.protocols import BaseProtocol
from canvas_sdk.utils import Http


class ExternalAPIHandler(BaseProtocol):
    """Handler that demonstrates hardcoded secret vulnerability."""

    RESPONDS_TO = [EventType.Name(EventType.PATIENT__POST_UPDATE)]

    # VULNERABILITY: Hardcoded OAuth token - should be in secrets
    API_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.Signature"

    def compute(self) -> list[Effect]:
        patient_id = self.event.context.get("patient", {}).get("id")
        if not patient_id:
            return []

        # Using hardcoded token instead of self.secrets["API_TOKEN"]
        http = Http()
        response = http.get(
            f"https://api.example.com/patient/{patient_id}/sync",
            headers={"Authorization": f"Bearer {self.API_TOKEN}"},
        )

        return []
