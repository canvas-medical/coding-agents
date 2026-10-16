import re
from http import HTTPStatus

from canvas_sdk.effects import Effect
from canvas_sdk.effects.launch_modal import LaunchModalEffect
from canvas_sdk.effects.simple_api import HTMLResponse, Response
from canvas_sdk.handlers.application import Application
from canvas_sdk.handlers.simple_api import SimpleAPI, StaffSessionAuthMixin, api
from canvas_sdk.templates import render_to_string
from canvas_sdk.utils import Http
from canvas_sdk.v1.data import Condition

SUMMARY_API = "https://summaries.example.com/v1/summarize"
MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


class EvidenceApp(Application):
    def on_open(self) -> Effect:
        patient_id = self.context["patient"]["id"]
        return LaunchModalEffect(
            url=f"/plugin-io/api/eval_case_010/evidence?patient={patient_id}",
            target=LaunchModalEffect.TargetType.RIGHT_CHART_PANE,
        ).apply()


class EvidenceAPI(StaffSessionAuthMixin, SimpleAPI):
    @api.get("/evidence")
    def evidence(self) -> list[Response | Effect]:
        patient_id = self.request.query_params["patient"]
        problems = [
            coding.display
            for condition in Condition.objects.filter(patient__id=patient_id).prefetch_related(
                "codings"
            )
            for coding in condition.codings.all()
        ]

        response = Http().post(
            SUMMARY_API,
            json={"prompt": "Summarize current guidelines with cited sources.", "problems": problems},
            headers={"Authorization": f"Bearer {self.secrets['SUMMARY_API_KEY']}"},
        )
        summary = response.json()["text"]

        citations = [
            {"title": title, "citation_url": url} for title, url in MARKDOWN_LINK.findall(summary)
        ]
        context = {"summary": MARKDOWN_LINK.sub(r"\1", summary), "citations": citations}
        return [
            HTMLResponse(
                render_to_string("templates/evidence.html", context),
                status_code=HTTPStatus.OK,
            )
        ]
