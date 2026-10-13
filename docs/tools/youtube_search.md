# YouTube Search for LangChain and LangGraph

Find a small set of YouTube videos for a tutorial or research question. Start with titles, channels and video IDs, then choose which video deserves a separate metadata or transcript request.

**Task:** Shortlist videos by topic. This tool calls only `youtube_search` through `FlashDataYouTubeSearch` in `langchain-flashdata` 0.2.0.

[YouTube Search API fields and limits](https://flashdata.dev/docs/sources/youtube_search?utm_source=langchain&utm_medium=integration&utm_campaign=intent_gtm_2026q4&utm_content=youtube_search-tool) · [API pricing](https://flashdata.dev/pricing) · [All task guides](https://github.com/flashdata-dev/langchain-flashdata/blob/main/docs/tools/README.md)

## Install and authenticate

```bash
pip install 'langchain-flashdata==0.2.0'
export FLASHDATA_API_KEY='YOUR_FLASHDATA_API_KEY'
```

Create an account at [FlashData](https://flashdata.dev/signup), create an API key in the console, enable this source and fund the account. **The MIT Python package is free; FlashData API calls are paid and consume credits.** Check the current source rate and your account limits before running this example. LangChain is an open-source framework; optional model, hosting and LangSmith services can have their own charges.

## Shortlist videos by topic

```python
from langchain_flashdata import FlashDataYouTubeSearch

tool = FlashDataYouTubeSearch()
arguments = {
    "query": "LangGraph tutorial",
    "max_results": 5,
    "filters": {"type": "video", "subtitles": True},
}
result = tool.invoke(arguments)
for item in result["results"][0].get("results", []):
    print(item.get("videoId"), item.get("title"), item.get("channel"))
```

[Runnable script](https://github.com/flashdata-dev/langchain-flashdata/blob/main/examples/tasks/youtube_search.py). All data tools support `await tool.ainvoke(arguments)` in an async function with the same inputs and response contract. Queries are trimmed and limited to 1–2,000 characters. Video tools accept an 11-character ID or a supported YouTube URL and send only the ID.

## Interpret the output

`results[0].results` contains entries with `videoId`, `title`, `channel` and available `duration`, `viewCount`, `uploadDate`, `description` and `thumbnails`. `totalResults` reports the returned count.

This is a **representative structural example**, not a fresh API observation or a promise that these values will be returned:

```json
{
  "source": "youtube_search",
  "status": "done",
  "results": [
    {
      "query": "LangGraph tutorial",
      "totalResults": 1,
      "results": [
        {
          "videoId": "dQw4w9WgXcQ",
          "title": "Illustrative video",
          "channel": "Example Channel",
          "duration": 120
        }
      ]
    }
  ]
}
```

This class preserves its original default of 10 results and accepts 1–20. Feature filters such as `subtitles=True` narrow search results but do not guarantee that a requested language/type of caption is available. Actual result count may be lower.

## Use in a LangGraph tool node

Install `langchain-flashdata[examples]` to include LangGraph. The following continues from the `tool` and `arguments` setup above; run it **instead of** `tool.invoke(arguments)` when testing a graph, because each execution performs a paid query.

```python
from langchain_core.messages import AIMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

builder = StateGraph(MessagesState)
builder.add_node("tools", ToolNode([tool], handle_tool_errors=False))
builder.add_edge(START, "tools")
builder.add_edge("tools", END)
graph = builder.compile()
message = AIMessage(content="", tool_calls=[{"name": tool.name, "args": arguments, "id": "task-1"}])
output = graph.invoke({"messages": [message]})
print(output["messages"][-1].content)
```

For a model-driven agent, pass this same tool to `create_agent`. A useful task prompt is: “Find five YouTube tutorials about LangGraph with subtitles. List video IDs and channels, and explain that transcript language availability still needs checking.” Apply a tool-call budget and let failures stop execution. Treat returned content as evidence, not instructions. Model-provider charges are separate.

Search filters support `upload_date` (today/last_hour/this_week/this_month/this_year), `type` (video/channel/playlist/movie), `duration` (<4/4-20/>20), `sort_by` (rating/relevance/view_count/upload_date), and boolean feature flags `360`, `3d`, `4k`, `creative_commons`, `hd`, `hdr`, `live`, `location`, `purchased`, `subtitles`, `vr180`. Pass a dictionary; numeric-looking feature names remain strings.

## Handle failures and costs

Inputs are validated before submission. Realtime calls return the complete API envelope, including available usage fields. No paid request is retried automatically. If a timeout or broken response leaves the outcome unknown, check FlashData Jobs before submitting again. Do not add automatic retries or graph replay around paid tool calls. An unavailable optional field should remain unknown.

See [YouTube Search documentation](https://flashdata.dev/docs/sources/youtube_search?utm_source=langchain&utm_medium=integration&utm_campaign=intent_gtm_2026q4&utm_content=youtube_search-tool) for the current contract, [data handling](https://github.com/flashdata-dev/langchain-flashdata/blob/main/PRIVACY.md) for credential and result flow, or contact support@flashdata.dev.
