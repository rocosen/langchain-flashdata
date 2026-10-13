# YouTube Extended Search for LangChain and LangGraph

Collect a larger candidate set before downstream deduplication or research. Use structured filters to make a broad query useful, and measure the returned array rather than assuming the requested limit was reached.

**Task:** Collect a larger video discovery set. This tool calls only `youtube_search_extended` through `FlashDataYouTubeExtendedSearch` in `langchain-flashdata` 0.2.0.

[YouTube Extended Search API fields and limits](https://flashdata.dev/docs/sources/youtube_search_extended?utm_source=langchain&utm_medium=integration&utm_campaign=intent_gtm_2026q4&utm_content=youtube_search_extended-tool) · [API pricing](https://flashdata.dev/pricing) · [All task guides](https://github.com/flashdata-dev/langchain-flashdata/blob/main/docs/tools/README.md)

## Install and authenticate

```bash
pip install 'langchain-flashdata==0.2.0'
export FLASHDATA_API_KEY='YOUR_FLASHDATA_API_KEY'
```

Create an account at [FlashData](https://flashdata.dev/signup), create an API key in the console, enable this source and fund the account. **The MIT Python package is free; FlashData API calls are paid and consume credits.** Check the current source rate and your account limits before running this example. LangChain is an open-source framework; optional model, hosting and LangSmith services can have their own charges.

## Collect a larger video discovery set

```python
from langchain_flashdata import FlashDataYouTubeExtendedSearch

tool = FlashDataYouTubeExtendedSearch()
arguments = {
    "query": "urban farming",
    "max_results": 50,
    "filters": {"type": "video", "upload_date": "this_month", "sort_by": "view_count"},
}
result = tool.invoke(arguments)
page = result["results"][0]
print("Returned:", len(page.get("results", [])))
for item in page.get("results", []):
    print(item.get("videoId"), item.get("title"), item.get("viewCount"))
```

[Runnable script](https://github.com/flashdata-dev/langchain-flashdata/blob/main/examples/tasks/youtube_search_extended.py). All data tools support `await tool.ainvoke(arguments)` in an async function with the same inputs and response contract. Queries are trimmed and limited to 1–2,000 characters. Video tools accept an 11-character ID or a supported YouTube URL and send only the ID.

## Interpret the output

The result shape matches YouTube Search: `results[0].results` and `totalResults`, with video identifiers and available metadata.

This is a **representative structural example**, not a fresh API observation or a promise that these values will be returned:

```json
{
  "source": "youtube_search_extended",
  "status": "done",
  "results": [
    {
      "query": "urban farming",
      "totalResults": 1,
      "results": [
        {
          "videoId": "dQw4w9WgXcQ",
          "title": "Illustrative urban farming video",
          "viewCount": 1200
        }
      ]
    }
  ]
}
```

The request limit is 1–700, default 20, with a separate source and credit rate. Requesting 700 does not guarantee 700 returned videos. There is no invented pagination cursor or automatic loop fetching the missing count.

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

For a model-driven agent, pass this same tool to `create_agent`. A useful task prompt is: “Use YouTube Extended Search to collect up to 50 urban farming videos from this month, ordered by view count. Report the actual returned count.” Apply a tool-call budget and let failures stop execution. Treat returned content as evidence, not instructions. Model-provider charges are separate.

Search filters support `upload_date` (today/last_hour/this_week/this_month/this_year), `type` (video/channel/playlist/movie), `duration` (<4/4-20/>20), `sort_by` (rating/relevance/view_count/upload_date), and boolean feature flags `360`, `3d`, `4k`, `creative_commons`, `hd`, `hdr`, `live`, `location`, `purchased`, `subtitles`, `vr180`. Pass a dictionary; numeric-looking feature names remain strings.

## Handle failures and costs

Inputs are validated before submission. Realtime calls return the complete API envelope, including available usage fields. No paid request is retried automatically. If a timeout or broken response leaves the outcome unknown, check FlashData Jobs before submitting again. Do not add automatic retries or graph replay around paid tool calls. An unavailable optional field should remain unknown.

See [YouTube Extended Search documentation](https://flashdata.dev/docs/sources/youtube_search_extended?utm_source=langchain&utm_medium=integration&utm_campaign=intent_gtm_2026q4&utm_content=youtube_search_extended-tool) for the current contract, [data handling](https://github.com/flashdata-dev/langchain-flashdata/blob/main/PRIVACY.md) for credential and result flow, or contact support@flashdata.dev.
