from http import HTTPStatus

from canvas_sdk.effects import Effect
from canvas_sdk.effects.launch_modal import LaunchModalEffect
from canvas_sdk.effects.simple_api import HTMLResponse, Response
from canvas_sdk.handlers.application import Application
from canvas_sdk.handlers.simple_api import SimpleAPI, StaffSessionAuthMixin, api
from canvas_sdk.templates import render_to_string
from canvas_sdk.v1.data import Condition

ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">'
    '<circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" stroke-width="2"/>'
    "</svg>"
)


class ProblemsApp(Application):
    def on_open(self) -> Effect:
        patient_id = self.context["patient"]["id"]
        return LaunchModalEffect(
            url=f"/plugin-io/api/eval_case_013/problems?patient={patient_id}",
            target=LaunchModalEffect.TargetType.RIGHT_CHART_PANE,
        ).apply()


class ProblemsAPI(StaffSessionAuthMixin, SimpleAPI):
    @api.get("/problems")
    def problems(self) -> list[Response | Effect]:
        patient_id = self.request.query_params["patient"]
        conditions = Condition.objects.filter(patient__id=patient_id).order_by("-onset_date")

        context = {
            "icon": ICON_SVG,
            "conditions": [
                {"onset_date": condition.onset_date, "notes": condition.notes}
                for condition in conditions
            ],
        }
        return [
            HTMLResponse(
                render_to_string("templates/problems.html", context),
                status_code=HTTPStatus.OK,
            )
        ]
