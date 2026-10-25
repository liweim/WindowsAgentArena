---
name: audio
domain: audio
priority: high
when_to_use: Load when speech in a VM audio/video file or an embedded web video must be understood
---

# Skill: Audio and video transcription

- You must use `AudioTools.transcribe(vm_path=...)` before ordinary task actions whenever the task provides an MP3, WAV, FLAC, or OGG audio file, or an MP4, MOV, or MKV video file stored in the VM. Do not skip the API in favor of listening, visual inference, player controls, or Live Caption.
- You must use `AudioTools.transcribe_web_video()` before ordinary task actions whenever the task asks you to understand speech in a video embedded in the opened webpage. Omit `page_url` to use the currently opened Chrome page; pass `page_url='https://...'` only when the exact webpage or direct media URL is already known. Do not manually download the web video first.
- For video input, the API automatically uses FFmpeg to extract a 16 kHz mono WAV before sending it to Parakeet TDT. Do not manually extract the audio first.
- Pass the absolute VM path, not a `file://` URL. In API calls, write Windows paths with forward slashes, for example `C:/Users/Docker/Desktop/Message.mp3`. Do not put a path such as `C:\Users\...` in a normal Python string because sequences such as `\U` can make the call fail to parse.
- If the exact filename is not stated, inspect the browser's local-file URL or use a read-only file listing to find the audio file before calling the API; do not guess the filename.
- Both APIs produce plain transcript text without timestamps. Results up to 1000 characters are returned directly.
- Longer results overwrite one fixed local text file: `C:/Users/Docker/Desktop/audio.txt` on Windows, `/home/user/audio.txt` on Linux, or `/sdcard/Download/audio.txt` on Android. Use `bash_execution` to search that exact path for targeted keywords or patterns and limit the output; never print the whole file into context.
- When copying transcript details into another app, preserve exact names, codes, prices, quantities, and deadlines. Use conventional readable formatting for spoken times (for example `8:00 AM`, not `8am`) and verify the completed text before terminating.
- Whenever either `AudioTools` transcription API is used, Chrome Live Caption must also be enabled and left enabled. Transcription does not replace this requirement.
