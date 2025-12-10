"""
Eval case: Patient-facing portal using admin-scoped FHIR token.

VULNERABILITY: This is a portal_menu_item (patient-facing) application that uses
an admin-scoped FHIR token instead of a patient-scoped token. This means Patient A
could potentially access Patient B's data because the admin token has broad access.

The security review should detect:
1. Application scope is portal_menu_item (patient-facing)
2. Using ADMIN_FHIR_TOKEN instead of patient-scoped token
3. This is a HIGH severity scope mismatch
"""

from canvas_sdk.handlers import Application, SimpleAPI
from canvas_sdk.effects import Effect
from canvas_sdk.effects.launch_modal import LaunchModalEffect
from canvas_sdk.utils import Http


class PatientPortalApp(Application):
    """Patient-facing application that launches the portal."""

    def on_open(self) -> Effect:
        patient_id = self.context.get("patient", {}).get("id", "")
        return LaunchModalEffect(
            url=f"/plugin-io/api/patient_scope_mismatch/portal/{patient_id}",
            target=LaunchModalEffect.TargetType.RIGHT_CHART_PANE,
            title="My Health Portal",
        ).apply()


class PatientPortalAPI(SimpleAPI):
    """API that fetches patient data using admin token."""

    PREFIX = "/patient_scope_mismatch"

    def get_portal(self, patient_id: str) -> dict:
        """
        VULNERABILITY: Using admin-scoped token for patient-facing feature.

        The ADMIN_FHIR_TOKEN can access ANY patient's data, but this is a
        patient-facing portal (portal_menu_item scope). A patient-scoped
        token should be used instead to ensure patients can only access
        their own data.
        """
        http = Http()

        # VULNERABILITY: Admin token in patient-facing context
        token = self.secrets["ADMIN_FHIR_TOKEN"]

        # This token could access any patient's data, not just the requesting patient
        response = http.get(
            f"https://instance.canvasmedical.com/api/Patient/{patient_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        return response.json()
