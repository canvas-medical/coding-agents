import json
from http import HTTPStatus

from canvas_sdk.effects import Effect
from canvas_sdk.effects.launch_modal import LaunchModalEffect
from canvas_sdk.effects.simple_api import HTMLResponse, Response
from canvas_sdk.handlers.application import Application
from canvas_sdk.handlers.simple_api import SimpleAPI, StaffSessionAuthMixin, api
from canvas_sdk.templates import render_to_string
from canvas_sdk.v1.data import Condition


class TimelineApp(Application):
    def on_open(self) -> Effect:
        patient_id = self.context["patient"]["id"]
        return LaunchModalEffect(
            url=f"/plugin-io/api/eval_case_014/timeline?patient={patient_id}",
            target=LaunchModalEffect.TargetType.RIGHT_CHART_PANE,
        ).apply()


class TimelineAPI(StaffSessionAuthMixin, SimpleAPI):
    @api.get("/timeline")
    def timeline(self) -> list[Response | Effect]:
        patient_id = self.request.query_params["patient"]
        conditions = Condition.objects.filter(patient__id=patient_id).order_by("onset_date")

        config = {
            "patientId": patient_id,
            "events": [
                {
                    "onset": condition.onset_date.isoformat() if condition.onset_date else None,
                    "resolved": (
                        condition.resolution_date.isoformat() if condition.resolution_date else None
                    ),
                    "notes": condition.notes,
                }
                for condition in conditions
            ],
        }
        return [
            HTMLResponse(
                render_to_string("templates/timeline.html", {"TIMELINE_CONFIG": json.dumps(config)}),
                status_code=HTTPStatus.OK,
            )
        ]
