from http import HTTPStatus

from canvas_sdk.effects import Effect
from canvas_sdk.effects.launch_modal import LaunchModalEffect
from canvas_sdk.effects.simple_api import HTMLResponse, Response
from canvas_sdk.handlers.application import Application
from canvas_sdk.handlers.simple_api import SimpleAPI, StaffSessionAuthMixin, api
from canvas_sdk.templates import render_to_string


class LookupApp(Application):
    def on_open(self) -> Effect:
        patient_id = self.context["patient"]["id"]
        return LaunchModalEffect(
            url=f"/plugin-io/api/eval_case_006/lookup?patient={patient_id}",
            target=LaunchModalEffect.TargetType.RIGHT_CHART_PANE,
        ).apply()


class LookupAPI(StaffSessionAuthMixin, SimpleAPI):
    @api.get("/lookup")
    def lookup(self) -> list[Response | Effect]:
        context = {
            "patient_id": self.request.query_params["patient"],
            "api_base": "https://formulary.example.com/v2",
            "api_key": self.secrets["FORMULARY_API_KEY"],
        }
        return [
            HTMLResponse(
                render_to_string("templates/lookup.html", context),
                status_code=HTTPStatus.OK,
            )
        ]
