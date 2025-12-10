"""Simple SendGrid email client using requests."""

from typing import NamedTuple

from requests import post as requests_post


class SendGridResponse(NamedTuple):
    """Response from SendGrid API."""

    success: bool
    message_id: str | None = None
    error_message: str | None = None
    error_code: int | None = None


class SendGridClient:
    """Simple SendGrid email client for Canvas plugin sandbox."""

    BASE_URL = "https://api.sendgrid.com/v3"

    def __init__(self, api_key: str, from_email: str) -> None:
        """Initialize SendGrid client.

        Args:
            api_key: SendGrid API key
            from_email: Email address to send from
        """
        self.api_key = api_key
        self.from_email = from_email

    def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        plain_text_body: str | None = None,
    ) -> SendGridResponse:
        """Send an email.

        Args:
            to: Recipient email address
            subject: Email subject line
            html_body: HTML content of the email
            plain_text_body: Optional plain text fallback content

        Returns:
            SendGridResponse with success status and message ID or error details
        """
        url = f"{self.BASE_URL}/mail/send"

        content = [{"type": "text/html", "value": html_body}]
        if plain_text_body:
            content.insert(0, {"type": "text/plain", "value": plain_text_body})

        payload = {
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": self.from_email},
            "subject": subject,
            "content": content,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests_post(
                url,
                json=payload,
                headers=headers,
                timeout=30,
            )

            if response.status_code >= 200 and response.status_code < 300:
                # SendGrid returns 202 Accepted with message ID in header
                message_id = response.headers.get("X-Message-Id")
                return SendGridResponse(success=True, message_id=message_id)
            else:
                try:
                    error_data = response.json()
                    errors = error_data.get("errors", [])
                    error_message = errors[0].get("message") if errors else response.text
                    return SendGridResponse(
                        success=False,
                        error_message=error_message,
                        error_code=response.status_code,
                    )
                except Exception:
                    return SendGridResponse(
                        success=False,
                        error_message=response.text,
                        error_code=response.status_code,
                    )
        except Exception as e:
            return SendGridResponse(success=False, error_message=str(e))
