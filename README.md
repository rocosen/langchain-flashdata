# langchain-flashdata

Google Search, News, Images, Shopping, Videos and Places; YouTube search,
metadata, transcripts, captions, license labels, channel data, autocomplete and
media delivery for LangChain and LangGraph. Each task has a source-specific
Python tool and a [runnable guide](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/README.md).

This package is maintained by FlashData. It implements LangChain's `BaseTool` and
`BaseToolkit` interfaces with synchronous and native asynchronous HTTP calls.

## Installation

Requires Python 3.10 or newer (below Python 4). Install from
[PyPI](https://pypi.org/project/langchain-flashdata/):

```bash
pip install -U langchain-flashdata
```

Create an API key in the [FlashData console](https://flashdata.dev), enable the
sources you need, and provide it through your environment:

```bash
export FLASHDATA_API_KEY='YOUR_FLASHDATA_API_KEY'
```

**The MIT package is free to install. FlashData API queries are paid and consume credits.** Check [current pricing](https://flashdata.dev/pricing)
and your account's available credits before running examples. Model provider
charges are separate.

## Quick start

```python
from langchain_flashdata import FlashDataGoogleSearch

search = FlashDataGoogleSearch()
result = search.invoke({"query": "LangGraph durable execution", "num": 3})
for item in result["results"][0].get("organic", []):
    print(item.get("title"), item.get("link"))
```

All tools also accept `api_key="..."` at construction time. Do not put real keys
in source files. Credentials are excluded from model-facing argument schemas
and tool serialization.

## Choose a task

Version 0.2.0 supports all 15 FlashData sources. Each class sends only its named
source; importing a single class does not give an agent the other query tools.

| Capability | Class | Inputs and result guide |
| --- | --- | --- |
| Google Search | `FlashDataGoogleSearch` | [Find citable web results for an agent](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/google_search.md) |
| Google News | `FlashDataGoogleNews` | [Build a topic briefing with publisher links](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/google_news.md) |
| Google Images | `FlashDataGoogleImages` | [Find image candidates with source pages](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/google_images.md) |
| Google Shopping | `FlashDataGoogleShopping` | [Compare merchant result snapshots](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/google_shopping.md) |
| Google Video Search | `FlashDataGoogleVideos` | [Discover video pages across websites](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/google_videos.md) |
| Google Places | `FlashDataGooglePlaces` | [Find local business candidates](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/google_places.md) |
| YouTube Search | `FlashDataYouTubeSearch` | [Shortlist videos by topic](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/youtube_search.md) |
| YouTube Extended Search | `FlashDataYouTubeExtendedSearch` | [Collect a larger video discovery set](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/youtube_search_extended.md) |
| YouTube Video Metadata | `FlashDataYouTubeMetadata` | [Inspect a video before deeper processing](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/youtube_metadata.md) |
| YouTube Transcript | `FlashDataYouTubeTranscript` | [Build timestamped transcript evidence](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/youtube_transcript.md) |
| YouTube Captions | `FlashDataYouTubeCaptions` | [Read the uploader-provided caption track](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/youtube_captions.md) |
| YouTube License Metadata | `FlashDataYouTubeTrainability` | [Inspect the Creative Commons label](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/youtube_trainability.md) |
| YouTube Channel Data | `FlashDataYouTubeChannel` | [Snapshot a channel and recent uploads](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/youtube_channel.md) |
| YouTube Autocomplete | `FlashDataYouTubeSuggestions` | [Explore phrasing before video search](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/youtube_suggestions.md) |
| YouTube Download | `FlashDataYouTubeDownload` | [Deliver video or audio to customer storage](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/youtube_download.md) |

Two additional tools, `FlashDataDownloadJob` and `FlashDataDownloadResult`, read
existing download jobs. Download submission is asynchronous and requires
`FLASHDATA_DOWNLOAD_STORAGE` JSON in the application environment. Storage credentials
are excluded from model-facing schemas. See the download guide before enabling it.

The original four classes and `FlashDataToolkit()` behavior remain compatible.
The default toolkit still returns Google Search, YouTube Search, Metadata and
Transcript. Select the needed sources explicitly for other workflows:

```python
from langchain_flashdata import FlashDataToolkit

tools = FlashDataToolkit(sources=("google_news", "youtube_captions")).get_tools()
```

Selecting `youtube_download` adds its two readers and requires storage configuration.
Google Search retains `num=10`, `page=1`, `autocorrect=True`; the five other Google
tools omit unset options so the provider chooses its behavior. YouTube Search
retains a default of 10 (maximum 20); Extended Search defaults to 20 (maximum 700)
and uses a separate source/rate. Requested counts are not guaranteed.

Transcript defaults to automatic captions; Captions defaults to uploader captions.
Both select English by default, read existing tracks, and never generate, translate
or fall back. License Metadata inspects Creative Commons labels and does not grant
training permission. See each guide for input constraints and exact output fields.

## Use with a LangChain / LangGraph agent

The [research example](https://github.com/rocosen/langchain-flashdata/blob/main/examples/research_agent.py) uses `create_agent`, which runs
on LangGraph. The model chooses tools and arguments from the question. A tool call
limit bounds the number of queries; it does not set a credit or dollar limit.

```bash
git clone https://github.com/rocosen/langchain-flashdata.git
cd langchain-flashdata
pip install '.[examples]'
export OPENAI_API_KEY='YOUR_MODEL_PROVIDER_KEY'
export OPENAI_MODEL='YOUR_TOOL_CALLING_MODEL'
# Optional for a Chat Completions compatible provider:
# export OPENAI_BASE_URL='https://YOUR_PROVIDER/v1'

python examples/research_agent.py \
  'Find recent LangGraph tutorials using Google Search. Request 3 results and cite their URLs.' \
  --max-tool-calls 1
```

This example uses `ChatOpenAI` with the Chat Completions API. Use a model that
supports tool calling. You can replace that model adapter with another LangChain
chat model. The FlashData tools do not depend on a particular model provider.

For a custom graph, pass the tools from `FlashDataToolkit().get_tools()` to
LangGraph's `ToolNode`. Use `handle_tool_errors=False` to propagate query failures
and stop execution before a model can resubmit an unknown-outcome query. Avoid
automatic graph retries or replay of paid tool nodes.

```python
from langchain_flashdata import FlashDataToolkit
from langgraph.prebuilt import ToolNode

tools = FlashDataToolkit().get_tools()
tool_node = ToolNode(tools, handle_tool_errors=False)
```

See [the examples guide](https://github.com/rocosen/langchain-flashdata/blob/main/examples/README.md) for direct tool calls, transcript
research, and the hosted MCP alternative.

## Output and errors

`invoke` and `ainvoke` return the complete API response dictionary. The envelope
contains `source`, `results`, and available usage/timestamp fields; some successful
responses omit `status`. Tool-call invocations produce a LangChain `ToolMessage`
containing the JSON response.

| Operation | Data location |
| --- | --- |
| Google Search | `results[0].organic` |
| YouTube search | `results[0].results` |
| Video metadata | `results[0]` |
| Transcript | `results[0].segments`, with available `fullText`, `languageCode`, and `isAutoGenerated` |

Invalid arguments fail locally before sending a request. API failures raise
`FlashDataError`, a LangChain `ToolException`. HTTP 401 indicates an invalid key,
402 insufficient credits, 403 a source/access restriction, and 429 a rate/quota
limit. Upstream error bodies and credentials are not included in exception messages.

Paid POST requests are not automatically retried or redirected. A timeout,
connection failure, unreadable result, or unexpected response may occur after a
query was submitted and charged: check Jobs in the FlashData console before
submitting again. The client connects directly to FlashData over HTTPS, with a
15-second connect timeout and a 120-second I/O timeout. Environment proxy settings
are not used.

## Existing MCP users

You can also connect LangChain to the existing hosted MCP endpoint at
`https://data.flashdata.dev/mcp` using the `X-API-Key` header. The native Python
tools above cover all 15 sources; the MCP catalog also contains account operations
and varies with key scopes. See [hosted_mcp.py](https://github.com/rocosen/langchain-flashdata/blob/main/examples/hosted_mcp.py).
The example uses the current `langchain[mcp]` API, which LangChain labels beta.

## Development

```bash
uv sync --extra examples
uv run --extra examples pytest --disable-socket --allow-unix-socket
uv run ruff check .
uv run ruff format --check .
uv build
uv run twine check dist/*
```

Tests include LangChain's standard tool suite, request contracts, validation,
sync/async calls, `ToolMessage` delivery, Agent error propagation, and tool budgets.
Unit tests do not call external services. Run the four paid API integration tests
explicitly with `FLASHDATA_API_KEY` configured:

```bash
FLASHDATA_RUN_LIVE=1 uv run --extra examples pytest tests/integration_tests -q
```

Release instructions: [RELEASING.md](https://github.com/rocosen/langchain-flashdata/blob/main/RELEASING.md).
Data handling: [PRIVACY.md](https://github.com/rocosen/langchain-flashdata/blob/main/PRIVACY.md).
License: [MIT](https://github.com/rocosen/langchain-flashdata/blob/main/LICENSE).
Support: [support@flashdata.dev](mailto:support@flashdata.dev).
