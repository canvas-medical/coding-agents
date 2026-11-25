from http import HTTPStatus

from canvas_sdk.effects import Effect
from canvas_sdk.effects.launch_modal import LaunchModalEffect
from canvas_sdk.effects.simple_api import HTMLResponse, JSONResponse, Response
from canvas_sdk.handlers.application import Application
from canvas_sdk.handlers.simple_api import SimpleAPI, StaffSessionAuthMixin, api
from canvas_sdk.templates import render_to_string


class CheckoutApp(Application):
    def on_open(self) -> Effect:
        patient_id = self.context["patient"]["id"]
        return LaunchModalEffect(
            url=f"/plugin-io/api/eval_case_011/checkout?patient={patient_id}",
            target=LaunchModalEffect.TargetType.RIGHT_CHART_PANE,
        ).apply()


class CheckoutAPI(StaffSessionAuthMixin, SimpleAPI):
    @api.get("/checkout")
    def page(self) -> list[Response | Effect]:
        context = {"patient_id": self.request.query_params["patient"]}
        return [
            HTMLResponse(
                render_to_string("templates/checkout.html", context),
                status_code=HTTPStatus.OK,
            )
        ]

    @api.get("/checkout/config")
    def config(self) -> list[Response | Effect]:
        return [
            JSONResponse(
                {
                    "stripe_publishable_key": self.secrets.get("STRIPE_PUBLISHABLE_KEY", ""),
                    "eligibility_api": "https://eligibility.example.com/v2",
                    "eligibility_secret": self.secrets.get("ELIGIBILITY_API_SECRET", ""),
                },
                status_code=HTTPStatus.OK,
            )
        ]
