"""Build a topic briefing with publisher links. Running this script consumes FlashData credits."""

from langchain_flashdata import FlashDataGoogleNews

tool = FlashDataGoogleNews()
arguments = {
    "query": "semiconductor manufacturing",
    "gl": "us",
    "hl": "en",
    "tbs": "qdr:d",
    "num": 5,
}
result = tool.invoke(arguments)
for item in result["results"][0].get("news", []):
    print(item.get("date"), item.get("source"), item.get("title"), item.get("link"))
