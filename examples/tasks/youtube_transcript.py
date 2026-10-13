"""Build timestamped transcript evidence. Running this script consumes FlashData credits."""

from langchain_flashdata import FlashDataYouTubeTranscript

tool = FlashDataYouTubeTranscript()
arguments = {"video_id": "dQw4w9WgXcQ", "language": "en", "auto": True}
result = tool.invoke(arguments)
item = result["results"][0]
for segment in item.get("segments", []):
    print(segment["start"], segment["end"], segment["text"])
