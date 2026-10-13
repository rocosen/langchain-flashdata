"""Inspect the Creative Commons label. Running this script consumes FlashData credits."""

from langchain_flashdata import FlashDataYouTubeTrainability

tool = FlashDataYouTubeTrainability()
arguments = {"video_id": "dQw4w9WgXcQ"}
result = tool.invoke(arguments)
item = result["results"][0]
print(item.get("videoId"), item.get("kind"), item.get("permitted"))
