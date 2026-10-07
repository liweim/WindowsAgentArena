---
name: audio
domain: audio
priority: high
when_to_use: Load when a task provides an audio file inside the VM
---

# Skill: Audio transcription

- Use `AudioTools.transcribe(vm_path=...)` to read speech from an MP3, WAV, FLAC, or OGG file stored in the VM.
- Pass the absolute VM path, not a `file://` URL. In API calls, write Windows paths with forward slashes, for example `C:/Users/Docker/Desktop/Message.mp3`. Do not put a path such as `C:\Users\...` in a normal Python string because sequences such as `\U` can make the call fail to parse.
- If the exact filename is not stated, inspect the browser's local-file URL or use a read-only file listing to find the audio file before calling the API; do not guess the filename.
- The API result contains the transcript text. Use that returned text as task evidence before taking the next action.
- When copying transcript details into another app, preserve exact names, codes, prices, quantities, and deadlines. Use conventional readable formatting for spoken times (for example `8:00 AM`, not `8am`) and verify the completed text before terminating.
- Set `timestamps=True` only when word timing is needed; ordinary content extraction should omit it.
- This tool does not enable, disable, or verify Live Caption.
- If the task instruction explicitly says to use Chrome Live Caption, using this API is only an accuracy aid and never satisfies that method requirement. First enable Chrome Live Caption through Chrome, verify from the resulting UI that the toggle is on or captions are visible during playback, and leave it enabled. Only then use this API if the visible captions are incomplete or need confirmation.
- Do not terminate a task that explicitly requires Chrome Live Caption unless the execution history contains positive evidence that Live Caption was enabled or visibly active. A successful transcript from this API is not such evidence.
