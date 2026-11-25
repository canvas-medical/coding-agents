from http import HTTPStatus

from canvas_sdk.effects import Effect
from canvas_sdk.effects.launch_modal import LaunchModalEffect
from canvas_sdk.effects.simple_api import HTMLResponse, Response
from canvas_sdk.handlers.application import Application
from canvas_sdk.handlers.simple_api import SimpleAPI, StaffSessionAuthMixin, api
from canvas_sdk.templates import render_to_string
from canvas_sdk.v1.data import Patient


class TeamApp(Application):
    def on_open(self) -> Effect:
        return LaunchModalEffect(
            url="/plugin-io/api/eval_case_009/team",
            target=LaunchModalEffect.TargetType.PAGE,
        ).apply()


class TeamAPI(StaffSessionAuthMixin, SimpleAPI):
    @api.get("/team")
    def page(self) -> list[Response | Effect]:
        return [
            HTMLResponse(
                render_to_string("templates/team.html", {}),
                status_code=HTTPStatus.OK,
            )
        ]

    @api.get("/team/patients")
    def search(self) -> list[Response | Effect]:
        query = self.request.query_params.get("q", "")
        patients = Patient.objects.filter(last_name__istartswith=query).order_by(
            "last_name", "first_name"
        )[:20]

        results = [
            {
                "id": patient.id,
                "name": f"{patient.first_name} {patient.last_name}",
                "dob": patient.birth_date,
            }
            for patient in patients
        ]
        return [
            HTMLResponse(
                render_to_string("templates/patient_search.html", {"results": results}),
                status_code=HTTPStatus.OK,
            )
        ]
