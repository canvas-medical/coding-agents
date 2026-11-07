from http import HTTPStatus
from urllib.parse import quote

from canvas_sdk.effects import Effect
from canvas_sdk.effects.launch_modal import LaunchModalEffect
from canvas_sdk.effects.simple_api import HTMLResponse, Response
from canvas_sdk.handlers.application import Application
from canvas_sdk.handlers.simple_api import SimpleAPI, StaffSessionAuthMixin, api
from canvas_sdk.templates import render_to_string
from canvas_sdk.utils import Http

REFERRAL_API = "https://referrals.example.com/v1"


class ReferralApp(Application):
    def on_open(self) -> Effect:
        patient_id = self.context["patient"]["id"]
        return LaunchModalEffect(
            url=f"/plugin-io/api/eval_case_007/referral?patient={patient_id}",
            target=LaunchModalEffect.TargetType.RIGHT_CHART_PANE,
        ).apply()


class ReferralAPI(StaffSessionAuthMixin, SimpleAPI):
    @api.get("/referral")
    def referral(self) -> list[Response | Effect]:
        patient_id = self.request.query_params["patient"]
        response = Http().get(
            f"{REFERRAL_API}/patients/{quote(patient_id, safe='')}/referral",
            headers={"Authorization": f"Bearer {self.secrets['REFERRAL_API_TOKEN']}"},
        )

        if response.status_code != HTTPStatus.OK:
            return [
                HTMLResponse(
                    f"<h2>Referral could not be loaded</h2><p>{response.text}</p>",
                    status_code=HTTPStatus.BAD_GATEWAY,
                )
            ]

        return [
            HTMLResponse(
                render_to_string("templates/referral.html", {"referral": response.json()}),
                status_code=HTTPStatus.OK,
            )
        ]
