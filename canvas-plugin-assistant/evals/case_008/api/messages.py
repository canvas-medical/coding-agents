from http import HTTPStatus

from canvas_sdk.effects import Effect
from canvas_sdk.effects.launch_modal import LaunchModalEffect
from canvas_sdk.effects.simple_api import HTMLResponse, JSONResponse, Response
from canvas_sdk.handlers.application import Application
from canvas_sdk.handlers.simple_api import SimpleAPI, StaffSessionAuthMixin, api
from canvas_sdk.templates import render_to_string
from canvas_sdk.v1.data import Message


class MessagesApp(Application):
    def on_open(self) -> Effect:
        patient_id = self.context["patient"]["id"]
        return LaunchModalEffect(
            url=f"/plugin-io/api/eval_case_008/messages?patient={patient_id}",
            target=LaunchModalEffect.TargetType.RIGHT_CHART_PANE,
        ).apply()


class MessagesAPI(StaffSessionAuthMixin, SimpleAPI):
    @api.get("/messages")
    def page(self) -> list[Response | Effect]:
        context = {"patient_id": self.request.query_params["patient"]}
        return [
            HTMLResponse(
                render_to_string("templates/messages.html", context),
                status_code=HTTPStatus.OK,
            )
        ]

    @api.get("/messages/data")
    def data(self) -> list[Response | Effect]:
        patient_id = self.request.query_params["patient"]
        messages = (
            Message.objects.filter(sender__patient__id=patient_id)
            | Message.objects.filter(recipient__patient__id=patient_id)
        ).order_by("-created")[:50]

        return [
            JSONResponse(
                {
                    "messages": [
                        {"created": message.created.isoformat(), "body": message.content}
                        for message in messages
                    ]
                },
                status_code=HTTPStatus.OK,
            )
        ]
