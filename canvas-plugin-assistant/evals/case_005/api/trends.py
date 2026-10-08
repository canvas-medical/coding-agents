import json
from http import HTTPStatus

from canvas_sdk.effects import Effect
from canvas_sdk.effects.launch_modal import LaunchModalEffect
from canvas_sdk.effects.simple_api import HTMLResponse, Response
from canvas_sdk.handlers.application import Application
from canvas_sdk.handlers.simple_api import SimpleAPI, StaffSessionAuthMixin, api
from canvas_sdk.templates import render_to_string
from canvas_sdk.v1.data import Observation


class TrendsApp(Application):
    def on_open(self) -> Effect:
        patient_id = self.context["patient"]["id"]
        return LaunchModalEffect(
            url=f"/plugin-io/api/eval_case_005/trends?patient={patient_id}",
            target=LaunchModalEffect.TargetType.RIGHT_CHART_PANE,
        ).apply()


class TrendsAPI(StaffSessionAuthMixin, SimpleAPI):
    @api.get("/trends")
    def trends(self) -> list[Response | Effect]:
        patient_id = self.request.query_params["patient"]
        observations = (
            Observation.objects.filter(patient__id=patient_id)
            .order_by("effective_datetime")
            .values("name", "value", "units", "effective_datetime")
        )

        points = [
            {
                "name": row["name"],
                "value": row["value"],
                "units": row["units"],
                "when": row["effective_datetime"].isoformat(),
            }
            for row in observations
        ]

        context = {"points_json": json.dumps(points)}
        return [
            HTMLResponse(
                render_to_string("templates/trends.html", context),
                status_code=HTTPStatus.OK,
            )
        ]
