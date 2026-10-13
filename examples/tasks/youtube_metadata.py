"""Inspect a video before deeper processing. Running this script consumes FlashData credits."""

from langchain_flashdata import FlashDataYouTubeMetadata

tool = FlashDataYouTubeMetadata()
arguments = {"video_id": "dQw4w9WgXcQ", "include_chapters": True, "include_formats": False}
result = tool.invoke(arguments)
item = result["results"][0]
print(item.get("title"), item.get("channel"), item.get("transcriptLanguages"))
for chapter in item.get("chapters", []):
    print(chapter.get("start_time"), chapter.get("end_time"), chapter.get("title"))
