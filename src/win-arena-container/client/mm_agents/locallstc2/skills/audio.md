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
- Both APIs return only the plain transcript text, without timestamps or metadata. Use that returned text as task evidence before taking the next action.
- When copying transcript details into another app, preserve exact names, codes, prices, quantities, and deadlines. Use conventional readable formatting for spoken times (for example `8:00 AM`, not `8am`) and verify the completed text before terminating.
- This tool does not enable, disable, or verify Live Caption.
- If the task instruction explicitly says to use Chrome Live Caption, transcribe with this API first, then enable Chrome Live Caption through Chrome, verify from the resulting UI that the toggle is on or captions are visible during playback, and leave it enabled. The API supplies reliable speech content but does not satisfy the separate Live Caption method requirement.
- Do not terminate a task that explicitly requires Chrome Live Caption unless the execution history contains positive evidence that Live Caption was enabled or visibly active. A successful transcript from this API is not such evidence.
