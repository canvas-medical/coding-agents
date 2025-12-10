"""AWS S3 client for storing and retrieving pharmacy mapping data."""

from datetime import UTC, datetime
from hashlib import sha256
from hmac import new as hmac_new
from http import HTTPStatus
from urllib.parse import quote

import requests


class AwsS3Credentials:
    """AWS S3 credentials configuration."""

    def __init__(self, aws_key: str, aws_secret: str, instance: str) -> None:
        self.aws_key = aws_key
        self.aws_secret = aws_secret
        self.instance = instance


class AwsS3:
    """AWS S3 client using AWS Signature Version 4 authentication.

    All object keys are automatically prefixed with '{instance}-plugins/'
    to ensure proper isolation between Canvas instances.
    """

    ALGORITHM = "AWS4-HMAC-SHA256"
    SAFE_CHARACTERS = "-._~"

    def __init__(self, credentials: AwsS3Credentials) -> None:
        self.aws_key = credentials.aws_key
        self.aws_secret = credentials.aws_secret
        self.instance = credentials.instance
        self.region = "us-west-2"
        self.bucket = "canvas-plugin-data"

    def is_ready(self) -> bool:
        """Check if all required credentials are configured."""
        return bool(self.aws_key and self.aws_secret and self.instance)

    def _prefixed_key(self, object_key: str) -> str:
        """Add instance prefix to object key."""
        return f"{self.instance}-plugins/{object_key}"

    def get_host(self) -> str:
        """Get the S3 bucket endpoint hostname."""
        return f"{self.bucket}.s3.{self.region}.amazonaws.com"

    def _get_signature_key(self, amz_date: str, canonical_request: str) -> tuple[str, str]:
        """Generate AWS Signature Version 4 signing key and signature."""
        date_stamp = amz_date[:8]
        credential_scope = f"{date_stamp}/{self.region}/s3/aws4_request"

        k_date = hmac_new(
            ("AWS4" + self.aws_secret).encode("utf-8"),
            date_stamp.encode("utf-8"),
            sha256,
        ).digest()
        k_region = hmac_new(k_date, self.region.encode("utf-8"), sha256).digest()
        k_service = hmac_new(k_region, b"s3", sha256).digest()
        k_signing = hmac_new(k_service, b"aws4_request", sha256).digest()

        string_to_sign = (
            f"{self.ALGORITHM}\n{amz_date}\n{credential_scope}\n"
            f"{sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )
        signature = hmac_new(k_signing, string_to_sign.encode("utf-8"), sha256).hexdigest()

        return credential_scope, signature

    def _build_headers(
        self, object_key: str, data: tuple[bytes, str] | None = None
    ) -> dict[str, str]:
        """Build authenticated headers for S3 requests."""
        method = "PUT" if data else "GET"
        binary_data, content_type = data if data else (b"", "")

        host = self.get_host()
        amz_date = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        payload_hash = sha256(binary_data).hexdigest()
        canonical_uri = f"/{quote(object_key)}"

        canonical_headers = f"host:{host}\nx-amz-content-sha256:{payload_hash}\nx-amz-date:{amz_date}\n"
        signed_headers = "host;x-amz-content-sha256;x-amz-date"

        if content_type:
            canonical_headers = f"content-type:{content_type}\n{canonical_headers}"
            signed_headers = f"content-type;{signed_headers}"

        canonical_request = (
            f"{method}\n{canonical_uri}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
        )

        credential_scope, signature = self._get_signature_key(amz_date, canonical_request)
        authorization_header = (
            f"{self.ALGORITHM} Credential={self.aws_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        return {
            "Host": host,
            "x-amz-date": amz_date,
            "x-amz-content-sha256": payload_hash,
            "Authorization": authorization_header,
        }

    def get_object(self, object_key: str) -> requests.Response:
        """Retrieve an object from S3.

        The object_key is automatically prefixed with '{instance}-plugins/'.
        """
        if not self.is_ready():
            response = requests.Response()
            response.status_code = HTTPStatus.SERVICE_UNAVAILABLE
            return response

        prefixed_key = self._prefixed_key(object_key)
        headers = self._build_headers(prefixed_key)
        endpoint = f"https://{headers['Host']}/{prefixed_key}"
        return requests.get(endpoint, headers=headers, timeout=30)

    def put_object(self, object_key: str, data: str, content_type: str = "application/json") -> requests.Response:
        """Upload an object to S3.

        The object_key is automatically prefixed with '{instance}-plugins/'.
        """
        if not self.is_ready():
            response = requests.Response()
            response.status_code = HTTPStatus.SERVICE_UNAVAILABLE
            return response

        prefixed_key = self._prefixed_key(object_key)
        binary_data = data.encode("utf-8")
        headers = self._build_headers(prefixed_key, (binary_data, content_type))
        headers["Content-Type"] = content_type
        headers["Content-Length"] = str(len(binary_data))

        endpoint = f"https://{headers['Host']}/{prefixed_key}"
        return requests.put(endpoint, headers=headers, data=binary_data, timeout=30)
