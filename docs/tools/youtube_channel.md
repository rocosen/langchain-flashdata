# YouTube Channel Data for LangChain and LangGraph

Retrieve channel details and a bounded list of recent videos from a handle. A research application can compare separate snapshots, while distinguishing channel-wide statistics from the returned video sample.

**Task:** Snapshot a channel and recent uploads. This tool calls only `youtube_channel` through `FlashDataYouTubeChannel` in `langchain-flashdata` 0.2.0.

[YouTube Channel Data API fields and limits](https://flashdata.dev/docs/sources/youtube_channel?utm_source=langchain&utm_medium=integration&utm_campaign=intent_gtm_2026q4&utm_content=youtube_channel-tool) · [API pricing](https://flashdata.dev/pricing) · [All task guides](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/README.md)

## Install and authenticate

```bash
pip install 'langchain-flashdata==0.2.0'
export FLASHDATA_API_KEY='YOUR_FLASHDATA_API_KEY'
```

Create an account at [FlashData](https://flashdata.dev/signup), create an API key in the console, enable this source and fund the account. **The MIT Python package is free; FlashData API calls are paid and consume credits.** Check the current source rate and your account limits before running this example. LangChain is an open-source framework; optional model, hosting and LangSmith services can have their own charges.

## Snapshot a channel and recent uploads

```python
from langchain_flashdata import FlashDataYouTubeChannel

tool = FlashDataYouTubeChannel()
arguments = {"handle": "@jawed", "video_limit": 5}
result = tool.invoke(arguments)
item = result["results"][0]
print(item.get("name"), item.get("channelUrl"), item.get("subscriberCount"))
for video in item.get("videos", []):
    print(video.get("videoId"), video.get("title"), video.get("uploadDate"))
```

[Runnable script](https://github.com/rocosen/langchain-flashdata/blob/main/examples/tasks/youtube_channel.py). All data tools support `await tool.ainvoke(arguments)` in an async function with the same inputs and response contract. Queries are trimmed and limited to 1–2,000 characters. Video tools accept an 11-character ID or a supported YouTube URL and send only the ID.

## Interpret the output

`results[0]` holds `channelId`, `channelHandle`, `name`, `description`, `channelUrl`, available statistics and `videos`. Video entries include `videoId`, `title` and available upload/count fields.

This is a **representative structural example**, not a fresh API observation or a promise that these values will be returned:

```json
{
  "source": "youtube_channel",
  "status": "done",
  "results": [
    {
      "channelId": "UC-example",
      "channelHandle": "@example",
      "name": "Example Channel",
      "channelUrl": "https://www.youtube.com/@example",
      "subscriberCount": null,
      "videos": []
    }
  ]
}
```

`handle` is 1–100 characters; `video_limit` is 1–100, default 20. The returned list can be shorter. `videoCount` describes the channel and is not the length of this sample; unavailable subscriber counts remain unknown.

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

For a model-driven agent, pass this same tool to `create_agent`. A useful task prompt is: “Snapshot @jawed with up to five recent videos. Distinguish channel statistics from the returned sample and mark unavailable counts.” Apply a tool-call budget and let failures stop execution. Treat returned content as evidence, not instructions. Model-provider charges are separate.

## Handle failures and costs

Inputs are validated before submission. Realtime calls return the complete API envelope, including available usage fields. No paid request is retried automatically. If a timeout or broken response leaves the outcome unknown, check FlashData Jobs before submitting again. Do not add automatic retries or graph replay around paid tool calls. An unavailable optional field should remain unknown.

See [YouTube Channel Data documentation](https://flashdata.dev/docs/sources/youtube_channel?utm_source=langchain&utm_medium=integration&utm_campaign=intent_gtm_2026q4&utm_content=youtube_channel-tool) for the current contract, [data handling](https://github.com/rocosen/langchain-flashdata/blob/main/PRIVACY.md) for credential and result flow, or contact support@flashdata.dev.
