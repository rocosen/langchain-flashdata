"""HTTP transport for the FlashData realtime query API."""

from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

import httpx
from langchain_core.tools import ToolException
from pydantic import SecretStr

QUERY_URL = "https://data.flashdata.dev/v1/queries/realtime"
TIMEOUT = httpx.Timeout(120.0, connect=15.0)
UNKNOWN_OUTCOME = (
    "The FlashData query outcome is unknown and may already be charged. "
    "Check Jobs in the FlashData console before submitting again. No automatic retry was made."
)


class FlashDataError(ToolException):
    """An actionable error without credentials or raw upstream error bodies."""


def _headers(api_key: SecretStr) -> dict[str, str]:
    return {
        "X-API-Key": api_key.get_secret_value(),
        "X-Request-Id": str(uuid4()),
        "Accept": "application/json",
        "User-Agent": "langchain-flashdata/0.2.0",
    }


def _result(response: httpx.Response) -> dict[str, Any]:
    if response.status_code != 200:
        messages = {
            401: "FlashData rejected the API key. Check FLASHDATA_API_KEY.",
            402: "Insufficient FlashData credits. Add credits in the FlashData console.",
            403: "This FlashData account or key cannot access the requested source.",
            429: "FlashData rate or quota limit reached. Wait before trying again.",
        }
        message = messages.get(response.status_code, UNKNOWN_OUTCOME)
        raise FlashDataError(f"{message} HTTP {response.status_code}.")
    try:
        data = response.json()
    except ValueError:
        raise FlashDataError(UNKNOWN_OUTCOME) from None
    if not isinstance(data, dict):
        raise FlashDataError(UNKNOWN_OUTCOME)
    job = data.get("job")
    if data.get("status") == "failed" or (isinstance(job, dict) and job.get("status") == "failed"):
        raise FlashDataError("FlashData could not complete the query. Check its details in Jobs.")
    if data.get("status") not in (None, "done", "completed") or not isinstance(
        data.get("results"), list
    ):
        raise FlashDataError(UNKNOWN_OUTCOME)
    return data


READ_ERROR = "Could not complete this read. Retry the read later; do not resubmit the query."
ASYNC_URL = "https://data.flashdata.dev/v1/queries"
JOBS_URL = "https://api.flashdata.dev/v2/jobs"
AUTH_URL = "https://api.flashdata.dev/v2/api-access"


def _request(api_key, method, url, payload=None, *, authenticated=True):
    try:
        with httpx.Client(timeout=TIMEOUT, follow_redirects=False, trust_env=False) as client:
            response = client.request(
                method,
                url,
                json=payload,
                headers=_headers(api_key) if authenticated else {"Accept": "application/json"},
            )
    except httpx.HTTPError:
        raise FlashDataError(UNKNOWN_OUTCOME if method == "POST" else READ_ERROR) from None
    return response


async def _arequest(api_key, method, url, payload=None, *, authenticated=True):
    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT, follow_redirects=False, trust_env=False
        ) as client:
            response = await client.request(
                method,
                url,
                json=payload,
                headers=_headers(api_key) if authenticated else {"Accept": "application/json"},
            )
    except httpx.HTTPError:
        raise FlashDataError(UNKNOWN_OUTCOME if method == "POST" else READ_ERROR) from None
    return response


def query(api_key: SecretStr, payload: dict[str, Any]) -> dict[str, Any]:
    """Submit exactly one realtime query, without retrying a paid POST."""
    return _result(_request(api_key, "POST", QUERY_URL, payload))


async def aquery(api_key: SecretStr, payload: dict[str, Any]) -> dict[str, Any]:
    """Submit one realtime query using native async I/O."""
    return _result(await _arequest(api_key, "POST", QUERY_URL, payload))


def _json(response, *, submission=False):
    error = UNKNOWN_OUTCOME if submission else READ_ERROR
    if response.status_code != 200:
        raise FlashDataError(f"{error} HTTP {response.status_code}.")
    if len(response.content) > 20 * 1024 * 1024:
        raise FlashDataError("Result exceeds 20 MiB. Retrieve it from Jobs; do not resubmit.")
    try:
        data = response.json()
    except ValueError:
        raise FlashDataError(error) from None
    if not isinstance(data, dict):
        raise FlashDataError(error)
    return data


def _receipt(response):
    data = _json(response, submission=True)
    from langchain_flashdata._inputs import DownloadJobInput

    try:
        DownloadJobInput(job_id=data.get("id"))
    except ValueError:
        raise FlashDataError(UNKNOWN_OUTCOME) from None
    if data.get("status") not in ("pending", "processing"):
        raise FlashDataError(UNKNOWN_OUTCOME)
    return data


def submit_download(api_key, payload):
    return _receipt(_request(api_key, "POST", ASYNC_URL, payload))


async def asubmit_download(api_key, payload):
    return _receipt(await _arequest(api_key, "POST", ASYNC_URL, payload))


def _job_url(job_id):
    from langchain_flashdata._inputs import DownloadJobInput

    valid = DownloadJobInput(job_id=job_id)
    return f"{JOBS_URL}/{valid.job_id}"


def _download_job(response):
    data = _json(response)
    job = data.get("job")
    if not isinstance(job, dict):
        raise FlashDataError(READ_ERROR)
    if job.get("source") != "youtube_download":
        raise FlashDataError("This reader only accepts youtube_download jobs.")
    return data


def get_download_job(api_key, job_id):
    return _download_job(_request(api_key, "GET", _job_url(job_id)))


async def aget_download_job(api_key, job_id):
    return _download_job(await _arequest(api_key, "GET", _job_url(job_id)))


def _result_url(identity, link):
    origin = _json(identity).get("result_origin")
    try:
        trusted = urlsplit(origin) if isinstance(origin, str) else None
        target = urlsplit(link.headers.get("location", ""))
        if (
            link.status_code != 302
            or not trusted
            or trusted.scheme != "https"
            or not trusted.hostname
            or trusted.username
            or trusted.password
            or trusted.path not in ("", "/")
            or trusted.query
            or trusted.fragment
            or target.scheme != "https"
            or target.username
            or target.password
            or target.fragment
            or (target.hostname, target.port or 443) != (trusted.hostname, trusted.port or 443)
        ):
            raise ValueError()
    except ValueError:
        raise FlashDataError(
            "The result link is not from FlashData's trusted result storage."
        ) from None
    return target.geturl()


def get_download_result(api_key, job_id):
    status = get_download_job(api_key, job_id)
    if status["job"].get("status") != "completed":
        return status
    identity = _request(api_key, "GET", AUTH_URL)
    link = _request(api_key, "GET", f"{_job_url(job_id)}/results")
    # Storage URLs carry their own signature. Never forward FlashData credentials.
    output = _request(api_key, "GET", _result_url(identity, link), authenticated=False)
    return {**status, "output": _json(output)}


async def aget_download_result(api_key, job_id):
    status = await aget_download_job(api_key, job_id)
    if status["job"].get("status") != "completed":
        return status
    identity = await _arequest(api_key, "GET", AUTH_URL)
    link = await _arequest(api_key, "GET", f"{_job_url(job_id)}/results")
    output = await _arequest(api_key, "GET", _result_url(identity, link), authenticated=False)
    return {**status, "output": _json(output)}
