"""Request-boundary tests against the product catalog snapshot (2026-10-13)."""

import asyncio
import json
from pathlib import Path

import httpx
import pytest
from jsonschema import Draft7Validator
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import ValidationError

from langchain_flashdata import (
    FlashDataDownloadJob,
    FlashDataDownloadResult,
    FlashDataError,
    FlashDataToolkit,
    FlashDataYouTubeDownload,
)
from langchain_flashdata._client import ASYNC_URL, AUTH_URL, JOBS_URL, QUERY_URL
from langchain_flashdata.tools import SOURCE_TOOLS

CONTRACT = json.loads((Path(__file__).parents[1] / "fixtures/source-contract.json").read_text())
STORAGE = json.dumps(
    {
        "storage_type": "s3",
        "storage_url": "example-bucket",
        "region": "us-east-1",
        "access_key": "storage-access-secret",
        "secret_key": "storage-secret",
    }
)
INPUTS = {
    **{
        source: {"query": "climate research", "autocorrect": False}
        for source in CONTRACT
        if source.startswith("google_")
    },
    "youtube_search": {"query": "LangGraph", "filters": {"4k": True, "live": False}},
    "youtube_search_extended": {
        "query": "LangGraph",
        "max_results": 700,
        "filters": {"upload_date": "this_week", "subtitles": True},
    },
    "youtube_metadata": {"video_id": "https://youtu.be/dQw4w9WgXcQ"},
    "youtube_transcript": {"video_id": "dQw4w9WgXcQ"},
    "youtube_captions": {"video_id": "dQw4w9WgXcQ"},
    "youtube_trainability": {"video_id": "dQw4w9WgXcQ"},
    "youtube_channel": {"handle": " @jawed ", "video_limit": 100},
    "youtube_suggestions": {"query": "LangGraph", "language": "en", "region": "US"},
    "youtube_download": {
        "video_id": "dQw4w9WgXcQ",
        "download_type": "audio",
        "output_format": "mp3",
        "audio_quality": "128",
        "end_at": "00:00:10",
    },
}


@pytest.mark.parametrize("source", list(CONTRACT))
@pytest.mark.parametrize("async_mode", [False, True])
def test_every_source_real_http_serialization(mock_api, source, async_mode):
    seen = []
    expected = (
        {"id": "job_test-1", "source": source, "status": "pending"}
        if source == "youtube_download"
        else {"source": source, "status": "done", "results": []}
    )

    def handler(request):
        seen.append(request)
        payload = json.loads(request.content)
        assert payload["source"] == source
        params = payload["params"]
        if source == "youtube_download":
            assert str(request.url) == ASYNC_URL
            assert params.pop("storage") == json.loads(STORAGE)
        else:
            assert str(request.url) == QUERY_URL
        primary = {k: v for k, v in payload.items() if k in ("query", "video_id", "handle")}
        Draft7Validator(CONTRACT[source]).validate({**primary, **params})
        if source in ("youtube_transcript", "youtube_captions"):
            assert params["auto"] is (source == "youtube_transcript")
        if source == "youtube_channel":
            assert primary == {"handle": "@jawed"}
        if source == "youtube_search":
            assert params["filters"] == {"4k": True, "live": False}
        if source.startswith("google_") and source != "google_search":
            assert params == {"autocorrect": False}
        return httpx.Response(200, json=expected)

    sync_patch, async_patch = mock_api(handler)
    settings = {"api_key": "api-secret"}
    if source == "youtube_download":
        settings["download_storage"] = STORAGE
    tool = SOURCE_TOOLS[source](**settings)
    with sync_patch, async_patch:
        result = (
            asyncio.run(tool.ainvoke(INPUTS[source])) if async_mode else tool.invoke(INPUTS[source])
        )
    assert result == expected
    assert len(seen) == 1


@pytest.mark.parametrize("async_mode", [False, True])
def test_download_read_chain_never_forwards_key_to_storage(mock_api, async_mode):
    seen = []

    def handler(request):
        seen.append(str(request.url))
        assert request.method == "GET"
        if request.url.host == "results.example.test":
            assert "x-api-key" not in request.headers
            return httpx.Response(200, json={"results": [{"file_url": "s3://example/video.mp4"}]})
        assert request.headers["x-api-key"] == "api-secret"
        if str(request.url) == AUTH_URL:
            return httpx.Response(200, json={"result_origin": "https://results.example.test"})
        if str(request.url).endswith("/results"):
            return httpx.Response(
                302, headers={"Location": "https://results.example.test/file?sig=test"}
            )
        return httpx.Response(
            200, json={"job": {"source": "youtube_download", "status": "completed"}}
        )

    sync_patch, async_patch = mock_api(handler)
    tool = FlashDataDownloadResult(api_key="api-secret")
    with sync_patch, async_patch:
        args = {"job_id": "job_test-1"}
        result = asyncio.run(tool.ainvoke(args)) if async_mode else tool.invoke(args)
    assert result["output"]["results"][0]["file_url"] == "s3://example/video.mp4"
    assert len(seen) == 4


@pytest.mark.parametrize("tool_cls", [FlashDataDownloadJob, FlashDataDownloadResult])
@pytest.mark.parametrize("async_mode", [False, True])
def test_job_readers_reject_other_sources(mock_api, tool_cls, async_mode):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"job": {"source": "google_search", "status": "completed"}})

    sync_patch, async_patch = mock_api(handler)
    with sync_patch, async_patch, pytest.raises(FlashDataError, match="only accepts"):
        tool = tool_cls(api_key="api-secret")
        if async_mode:
            asyncio.run(tool.ainvoke({"job_id": "job_test-1"}))
        else:
            tool.invoke({"job_id": "job_test-1"})
    assert len(calls) == 1


@pytest.mark.parametrize(
    "target",
    [
        "http://results.example.test/f",
        "https://evil.test/f",
        "https://results.example.test:444/f",
        "https://user:pass@results.example.test/f",
    ],
)
def test_result_redirect_rejected_before_fetch(mock_api, target):
    calls = []

    def handler(request):
        calls.append(str(request.url))
        if str(request.url) == AUTH_URL:
            return httpx.Response(200, json={"result_origin": "https://results.example.test"})
        if str(request.url).endswith("/results"):
            return httpx.Response(302, headers={"Location": target})
        return httpx.Response(
            200, json={"job": {"source": "youtube_download", "status": "completed"}}
        )

    sync_patch, _ = mock_api(handler)
    with sync_patch, pytest.raises(FlashDataError, match="trusted result storage"):
        FlashDataDownloadResult(api_key="api-secret").invoke({"job_id": "job_test-1"})
    assert len(calls) == 3


def test_pending_download_only_reads_status(mock_api):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(
            200, json={"job": {"source": "youtube_download", "status": "processing"}}
        )

    sync_patch, _ = mock_api(handler)
    with sync_patch:
        result = FlashDataDownloadResult(api_key="api-secret").invoke({"job_id": "job_test-1"})
    assert result["job"]["status"] == "processing"
    assert str(calls[0].url) == f"{JOBS_URL}/job_test-1"
    assert len(calls) == 1


@pytest.mark.parametrize(
    "arguments",
    [
        {"video_id": "dQw4w9WgXcQ", "download_type": "audio", "video_quality": "<=720"},
        {"video_id": "dQw4w9WgXcQ", "download_type": "audio", "output_format": "mp4"},
        {"video_id": "dQw4w9WgXcQ", "start_at": "00:01:00", "end_at": "00:00:30"},
        {"video_id": "dQw4w9WgXcQ", "end_at": "13:00:00"},
        {"video_id": "dQw4w9WgXcQ", "storage": {"secret_key": "must-not-be-model-input"}},
    ],
)
def test_download_invalid_options_fail_before_network(arguments):
    with pytest.raises(ValidationError):
        FlashDataYouTubeDownload(api_key="api-secret", download_storage=STORAGE).invoke(arguments)


def test_all_selected_tools_hide_storage_and_key():
    toolkit = FlashDataToolkit(
        api_key="api-secret", sources=tuple(CONTRACT), download_storage=STORAGE
    )
    tools = toolkit.get_tools()
    assert len(tools) == 17
    assert len({tool.name for tool in tools}) == 17
    for obj in [toolkit, *tools]:
        serialized = repr(obj) + str(obj.model_dump())
        if obj is not toolkit:
            serialized += str(obj.to_json())
        for secret in ("api-secret", "storage-access-secret", "storage-secret"):
            assert secret not in serialized
    for tool in tools:
        schema = str(convert_to_openai_tool(tool))
        assert "api_key" not in schema
        assert "secret_key" not in schema
        assert "download_storage" not in schema


@pytest.mark.parametrize(
    "raw",
    [
        "not-json",
        "[]",
        '{"storage_type":"unknown"}',
        STORAGE.replace("example-bucket", "../secret-bucket"),
    ],
)
def test_storage_errors_do_not_echo_secrets(raw):
    with pytest.raises(FlashDataError) as error:
        FlashDataYouTubeDownload(api_key="api-secret", download_storage=raw)
    assert "storage-secret" not in str(error.value)


@pytest.mark.parametrize("bucket", ["1.2.3.4", "bucket.-name", "bucket-.name"])
def test_invalid_s3_bucket_is_rejected_locally(bucket):
    with pytest.raises(FlashDataError, match="S3 bucket"):
        FlashDataYouTubeDownload(
            api_key="api-secret", download_storage=STORAGE.replace("example-bucket", bucket)
        )


def test_gcs_does_not_forward_unrelated_service_account_fields():
    from langchain_flashdata._storage import storage_config

    account = {
        "project_id": "example",
        "client_email": "a@example.iam.gserviceaccount.com",
        "private_key": "-----BEGIN PRIVATE KEY-----\nfixture",
        "unrelated_secret": "do-not-forward",
    }
    normalized = storage_config(
        json.dumps(
            {"storage_type": "gcs", "storage_url": "example-bucket", "service_account": account}
        )
    )
    assert set(normalized["service_account"]) == {"project_id", "client_email", "private_key"}
    assert "do-not-forward" not in json.dumps(normalized)


@pytest.mark.parametrize("source", list(CONTRACT))
def test_every_task_runs_inside_langgraph_toolnode(mock_api, source):
    from langchain_core.messages import AIMessage, ToolMessage
    from langgraph.graph import END, START, MessagesState, StateGraph
    from langgraph.prebuilt import ToolNode

    expected = (
        {"id": "job_test-1", "source": source, "status": "pending"}
        if source == "youtube_download"
        else {"source": source, "status": "done", "results": []}
    )
    settings = {"api_key": "api-secret"}
    if source == "youtube_download":
        settings["download_storage"] = STORAGE
    tool = SOURCE_TOOLS[source](**settings)
    sync_patch, _ = mock_api(lambda request: httpx.Response(200, json=expected))
    builder = StateGraph(MessagesState)
    builder.add_node("tools", ToolNode([tool], handle_tool_errors=False))
    builder.add_edge(START, "tools")
    builder.add_edge("tools", END)
    with sync_patch:
        output = builder.compile().invoke(
            {
                "messages": [
                    AIMessage(
                        content="",
                        tool_calls=[{"name": tool.name, "args": INPUTS[source], "id": "task-1"}],
                    )
                ]
            }
        )
    assert isinstance(output["messages"][-1], ToolMessage)
    assert json.loads(output["messages"][-1].content) == expected
