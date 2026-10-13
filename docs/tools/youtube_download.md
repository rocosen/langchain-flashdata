# YouTube Download for LangChain and LangGraph

Submit an asynchronous media-delivery job for a video you are authorized to process. Configure the cloud destination in the application, save the returned job ID, and later read delivery metadata without resubmitting the download.

**Task:** Deliver video or audio to customer storage. This tool calls only `youtube_download` through `FlashDataYouTubeDownload` in `langchain-flashdata` 0.2.0.

[YouTube Download API fields and limits](https://flashdata.dev/docs/sources/youtube_download?utm_source=langchain&utm_medium=integration&utm_campaign=intent_gtm_2026q4&utm_content=youtube_download-tool) · [API pricing](https://flashdata.dev/pricing) · [All task guides](https://github.com/flashdata-dev/langchain-flashdata/blob/main/docs/tools/README.md)

## Install and authenticate

```bash
pip install 'langchain-flashdata==0.2.0'
export FLASHDATA_API_KEY='YOUR_FLASHDATA_API_KEY'
```

Create an account at [FlashData](https://flashdata.dev/signup), create an API key in the console, enable this source and fund the account. **The MIT Python package is free; FlashData API calls are paid and consume credits.** Check the current source rate and your account limits before running this example. LangChain is an open-source framework; optional model, hosting and LangSmith services can have their own charges.

## Deliver video or audio to customer storage

```python
from langchain_flashdata import FlashDataYouTubeDownload

tool = FlashDataYouTubeDownload()
arguments = {
    "video_id": "dQw4w9WgXcQ",
    "download_type": "audio",
    "output_format": "mp3",
    "audio_quality": "128",
    "start_at": "00:00:00",
    "end_at": "00:00:10",
}
result = tool.invoke(arguments)
print("Save this job ID:", result["id"], "status:", result["status"])
```

[Runnable script](https://github.com/flashdata-dev/langchain-flashdata/blob/main/examples/tasks/youtube_download.py). All data tools support `await tool.ainvoke(arguments)` in an async function with the same inputs and response contract. Queries are trimmed and limited to 1–2,000 characters. Video tools accept an 11-character ID or a supported YouTube URL and send only the ID.

## Interpret the output

Submission returns `id`, `source` and `status`, not a media file. After completion, the result reader returns `output.results[0]` with `file_url`, `file_size`, `downloaded_bytes`, `md5`, `output_format` and available media attributes.

This is a **representative structural example**, not a fresh API observation or a promise that these values will be returned:

```json
{
  "id": "job_example-1",
  "source": "youtube_download",
  "status": "pending",
  "usage": {
    "credits": 0
  }
}
```

Download is asynchronous only. Language-level `ainvoke` still returns a submission receipt, not completion. Video formats are mp4/webm/mkv; audio formats m4a/mp3/opus. Clip times use H:MM:SS up to 12:00:00, with end later than start. FlashData charges delivered bytes; storage-provider charges are separate.

## Configure storage and read the job

Set `FLASHDATA_DOWNLOAD_STORAGE` to a JSON credential from your secret manager before constructing the tool. Alternatively pass `download_storage` as a JSON string to the constructor. Storage is excluded from model-facing arguments, repr and serialization. Never paste real credentials into a prompt or commit them.

```json
{"storage_type":"s3","storage_url":"YOUR_BUCKET","region":"us-east-1","access_key":"YOUR_ACCESS_KEY","secret_key":"YOUR_SECRET_KEY","object_prefix":"langchain-clips"}
```

The bucket/container must already exist. Other supported providers are S3-compatible, OSS, GCS, Azure, COS, BOS and TOS; use the [provider-specific storage fields](https://flashdata.dev/docs/sources/youtube_download). GCS uses a service account, Azure a write-enabled container SAS, and S3-compatible storage requires an endpoint. Keep the destination credential scoped to the intended bucket.

After saving the receipt, read the **same** ID in a later run:

```python
import os
from langchain_flashdata import FlashDataDownloadJob, FlashDataDownloadResult

job_id = os.environ["FLASHDATA_JOB_ID"]  # the id returned by the submission
status = FlashDataDownloadJob().invoke({"job_id": job_id})
print(status["job"]["status"])
if status["job"]["status"] == "completed":
    completed = FlashDataDownloadResult().invoke({"job_id": job_id})
    print(completed["output"]["results"])
```

The readers accept only `youtube_download` jobs. Pending/processing/failed jobs return their status; the result reader fetches JSON only after completion. It obtains the trusted result origin from FlashData, checks the signed result URL, and never forwards the API key to result storage. It does not download the delivered media into the agent process. Configure polling intervals in your application; do not replay a paid submit node when resuming a graph.


## Enable the download workflow in LangGraph

Install `langchain-flashdata[examples]` and set both FlashData environment variables.
Select only this source to expose the submit tool and its two readers:

```python
from langchain_flashdata import FlashDataToolkit
from langgraph.prebuilt import ToolNode

tools = FlashDataToolkit(sources=("youtube_download",)).get_tools()
node = ToolNode(tools, handle_tool_errors=False)
```

Pass the same `tools` to `create_agent` with a model of your choice if the agent
should choose media options. Have your application persist the returned job ID
before leaving the submit step. Later steps call `flashdata_download_job` or
`flashdata_download_result` with that ID. Use a tool-call budget; do not let
pending status trigger a second submission. Model-provider fees are separate.

## Handle failures and costs

Inputs are validated before submission. Realtime calls return the complete API envelope, including available usage fields. No paid request is retried automatically. If a timeout or broken response leaves the outcome unknown, check FlashData Jobs before submitting again. Do not add automatic retries or graph replay around paid tool calls. An unavailable optional field should remain unknown.

See [YouTube Download documentation](https://flashdata.dev/docs/sources/youtube_download?utm_source=langchain&utm_medium=integration&utm_campaign=intent_gtm_2026q4&utm_content=youtube_download-tool) for the current contract, [data handling](https://github.com/flashdata-dev/langchain-flashdata/blob/main/PRIVACY.md) for credential and result flow, or contact support@flashdata.dev.
