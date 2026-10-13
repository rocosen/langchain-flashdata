"""Discover video pages across websites. Running this script consumes FlashData credits."""

from langchain_flashdata import FlashDataGoogleVideos

tool = FlashDataGoogleVideos()
arguments = {"query": "battery recycling process demonstration", "num": 5}
result = tool.invoke(arguments)
for item in result["results"][0].get("videos", []):
    print(item.get("title"), item.get("source"), item.get("duration"), item.get("link"))
