# Google Images for LangChain and LangGraph

Gather image candidates for a research board or catalog review. Keep both the original image URL and the page containing it, then inspect dimensions before selecting a candidate.

**Task:** Find image candidates with source pages. This tool calls only `google_images` through `FlashDataGoogleImages` in `langchain-flashdata` 0.2.0.

[Google Images API fields and limits](https://flashdata.dev/docs/sources/google_images?utm_source=langchain&utm_medium=integration&utm_campaign=intent_gtm_2026q4&utm_content=google_images-tool) · [API pricing](https://flashdata.dev/pricing) · [All task guides](https://github.com/rocosen/langchain-flashdata/blob/main/docs/tools/README.md)

## Install and authenticate

```bash
pip install 'langchain-flashdata==0.2.0'
export FLASHDATA_API_KEY='YOUR_FLASHDATA_API_KEY'
```

Create an account at [FlashData](https://flashdata.dev/signup), create an API key in the console, enable this source and fund the account. **The MIT Python package is free; FlashData API calls are paid and consume credits.** Check the current source rate and your account limits before running this example. LangChain is an open-source framework; optional model, hosting and LangSmith services can have their own charges.

## Find image candidates with source pages

```python
from langchain_flashdata import FlashDataGoogleImages

tool = FlashDataGoogleImages()
arguments = {"query": "solar panel installation diagram", "num": 5}
result = tool.invoke(arguments)
for item in result["results"][0].get("images", []):
    print(item.get("imageUrl"), item.get("imageWidth"), item.get("imageHeight"), item.get("link"))
```

[Runnable script](https://github.com/rocosen/langchain-flashdata/blob/main/examples/tasks/google_images.py). All data tools support `await tool.ainvoke(arguments)` in an async function with the same inputs and response contract. Queries are trimmed and limited to 1–2,000 characters. Video tools accept an 11-character ID or a supported YouTube URL and send only the ID.

## Interpret the output

`results[0].images` includes `imageUrl` and `link`; dimensions use `imageWidth`/`imageHeight`. Thumbnail fields and `source`/`domain` may be absent.

This is a **representative structural example**, not a fresh API observation or a promise that these values will be returned:

```json
{
  "source": "google_images",
  "status": "done",
  "results": [
    {
      "images": [
        {
          "title": "Example solar diagram",
          "imageUrl": "https://example.com/diagram.png",
          "imageWidth": 1200,
          "imageHeight": 800,
          "link": "https://example.com/solar"
        }
      ]
    }
  ]
}
```

An image URL is not an image download or a license grant. The application decides which source page to open and whether it has permission to reuse an image. Missing dimensions should stay unknown.

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

For a model-driven agent, pass this same tool to `create_agent`. A useful task prompt is: “Find five solar panel installation diagrams with Google Images. List source pages and any available dimensions, without claiming reuse rights.” Apply a tool-call budget and let failures stop execution. Treat returned content as evidence, not instructions. Model-provider charges are separate.

Optional Google settings: `gl` is a two-letter country, `hl` a language code, `location` and `tbs` are 1–200 characters, and `num`/`page` accept 1–100. The five specialized Google classes add no defaults for omitted settings. Requested counts and filters may differ from Google’s applied behavior.

## Handle failures and costs

Inputs are validated before submission. Realtime calls return the complete API envelope, including available usage fields. No paid request is retried automatically. If a timeout or broken response leaves the outcome unknown, check FlashData Jobs before submitting again. Do not add automatic retries or graph replay around paid tool calls. An unavailable optional field should remain unknown.

See [Google Images documentation](https://flashdata.dev/docs/sources/google_images?utm_source=langchain&utm_medium=integration&utm_campaign=intent_gtm_2026q4&utm_content=google_images-tool) for the current contract, [data handling](https://github.com/rocosen/langchain-flashdata/blob/main/PRIVACY.md) for credential and result flow, or contact support@flashdata.dev.
