"""Snapshot a channel and recent uploads. Running this script consumes FlashData credits."""

from langchain_flashdata import FlashDataYouTubeChannel

tool = FlashDataYouTubeChannel()
arguments = {"handle": "@jawed", "video_limit": 5}
result = tool.invoke(arguments)
item = result["results"][0]
print(item.get("name"), item.get("channelUrl"), item.get("subscriberCount"))
for video in item.get("videos", []):
    print(video.get("videoId"), video.get("title"), video.get("uploadDate"))
