"""Deliver video or audio to customer storage. Running this script consumes FlashData credits."""

from langchain_flashdata import FlashDataYouTubeDownload

tool = FlashDataYouTubeDownload()
arguments = {
    "video_id": "dQw4w9WgXcQ",
    "download_type": "audio",
    "output_format": "mp3",
    "audio_quality": "128",
    "start_at": "00:00:00",
    "end_at": "00:00:10",
}
result = tool.invoke(arguments)
print("Save this job ID:", result["id"], "status:", result["status"])
