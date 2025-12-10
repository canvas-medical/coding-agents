"""Simple Twilio SMS client using requests."""

from typing import NamedTuple

from requests import post as requests_post


class TwilioResponse(NamedTuple):
    """Response from Twilio API."""

    success: bool
    message_sid: str | None = None
    error_message: str | None = None
    error_code: int | None = None


class TwilioClient:
    """Simple Twilio SMS client for Canvas plugin sandbox."""

    BASE_URL = "https://api.twilio.com/2010-04-01"

    def __init__(self, account_sid: str, auth_token: str, from_number: str) -> None:
        """Initialize Twilio client.

        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_number: Phone number to send SMS from (E.164 format)
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    def send_sms(self, to: str, body: str) -> TwilioResponse:
        """Send an SMS message.

        Args:
            to: Recipient phone number (E.164 format, e.g., +15551234567)
            body: Message text

        Returns:
            TwilioResponse with success status and message SID or error details
        """
        url = f"{self.BASE_URL}/Accounts/{self.account_sid}/Messages.json"

        data = {"To": to, "From": self.from_number, "Body": body}

        try:
            response = requests_post(
                url,
                data=data,
                auth=(self.account_sid, self.auth_token),
                timeout=30,
            )

            if response.status_code >= 200 and response.status_code < 300:
                response_data = response.json()
                return TwilioResponse(
                    success=True, message_sid=response_data.get("sid")
                )
            else:
                try:
                    error_data = response.json()
                    return TwilioResponse(
                        success=False,
                        error_message=error_data.get("message", response.text),
                        error_code=error_data.get("code", response.status_code),
                    )
                except Exception:
                    return TwilioResponse(
                        success=False,
                        error_message=response.text,
                        error_code=response.status_code,
                    )
        except Exception as e:
            return TwilioResponse(success=False, error_message=str(e))
