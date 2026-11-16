#!/usr/bin/env python3
"""Render reviewed footage into captioned portrait video with narration and music."""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

MAX_SOURCE_BYTES = 100 * 1024 * 1024


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Times must be finite numbers")
    return value


def validate_music(spec):
    music = spec.get("audio", {}).get("licensed_music")
    if music is None:
        return
    if not isinstance(music, dict) or music.get("rights_verified") is not True or music.get("commercial_use") is not True:
        raise ValueError("Licensed music needs reviewed commercial rights")
    for key in ("page", "download", "license"):
        parsed = urllib.parse.urlparse(music.get(key, ""))
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Licensed music needs HTTPS source and license URLs")
    if not re.fullmatch(r"[a-f0-9]{64}", music.get("sha256", "")):
        raise ValueError("Licensed music needs a reviewed SHA-256")
    if not all(isinstance(music.get(k), str) and music[k].strip() for k in ("title", "artist", "reviewed_by", "rights_note", "attribution", "changes")):
        raise ValueError("Licensed music needs attribution and review details")
    reviewed = date.fromisoformat(music.get("reviewed_on", ""))
    if reviewed > datetime.now(timezone.utc).date() or number(music.get("start", 0)) < 0:
        raise ValueError("Invalid licensed music review date or excerpt start")
    description = spec.get("description", "")
    if not all(value in description for value in (music["attribution"], music["license"], music["changes"])):
        raise ValueError("Video description must include music attribution, license and changes")


def validate(spec):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", spec.get("id", "")):
        raise ValueError("Clip id must contain lowercase words separated by hyphens")
    if not isinstance(spec.get("title"), str) or not 1 <= len(spec["title"]) <= 100:
        raise ValueError("A YouTube title of 1-100 characters is required")
    if spec.get("audience") not in ("made_for_kids", "not_made_for_kids"):
        raise ValueError("An explicit audience classification is required")
    if spec.get("layout", "fit") not in ("fit", "portrait", "portrait_crop"):
        raise ValueError("Layout must be fit, portrait or portrait_crop")
    if not 0 <= number(spec.get("crop_position", 0.5)) <= 1:
        raise ValueError("Crop position must be between zero and one")
    if spec.get("caption_style", "upper") not in ("upper", "impact"):
        raise ValueError("Caption style must be upper or impact")
    source = spec.get("source", {})
    if source.get("rights_verified") is not True:
        raise ValueError("Commercial reuse and editing rights must be reviewed first")
    for key in ("page", "download", "license"):
        parsed = urllib.parse.urlparse(source.get(key, ""))
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError(f"Source {key} must be an HTTPS URL without embedded credentials")
    if not source.get("reviewed_by") or not source.get("rights_note"):
        raise ValueError("A reviewer and license notes are required")
    reviewed = date.fromisoformat(source.get("reviewed_on", ""))
    if reviewed > datetime.now(timezone.utc).date():
        raise ValueError("License review date cannot be in the future")
    start, duration = number(spec.get("start", 0)), number(spec.get("duration"))
    if start < 0 or not 1 <= duration <= 180:
        raise ValueError("Source start must be nonnegative; duration must be 1-180 seconds")
    captions = spec.get("captions")
    if not isinstance(captions, list) or not captions:
        raise ValueError("Original captions are required")
    previous_end = 0
    for caption in captions:
        begin, end = number(caption.get("start")), number(caption.get("end"))
        text = caption.get("text")
        if not previous_end <= begin < end <= duration:
            raise ValueError("Captions must be ordered, nonoverlapping, and inside the clip")
        if not isinstance(text, str) or not text.strip() or len(text) > 240:
            raise ValueError("Each caption must contain 1-240 characters")
        if any(ord(c) < 32 and c != "\n" for c in text):
            raise ValueError("Captions cannot contain control characters")
        previous_end = end
    validate_music(spec)
    return spec


def ass_time(seconds):
    centiseconds = round(seconds * 100)
    return f"{centiseconds // 360000}:{centiseconds // 6000 % 60:02d}:{centiseconds // 100 % 60:02d}.{centiseconds % 100:02d}"


def ass_text(text):
    # Do not interpret caption text as ASS formatting or line-control commands.
    return text.replace("\\", "＼").replace("{", "｛").replace("}", "｝").replace("\n", r"\N")


def subtitles(spec):
    header = """[Script Info]
PlayResX: 720
PlayResY: 1280
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,42,&H00FFFFFF,&H000000FF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,8,35,35,180,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    if spec.get("caption_style") == "impact":
        header = header.replace("Default,DejaVu Sans,42,", "Default,DejaVu Sans,56,").replace("0,0,1,3,1,8,35,35,180,1", "0,0,1,4,1,5,60,60,180,1")
    return header + "\n".join(
        f"Dialogue: 0,{ass_time(c['start'])},{ass_time(c['end'])},Default,,0,0,0,,{ass_text(c['text'])}"
        for c in spec["captions"]
    ) + "\n"


def download(url, destination):
    request = urllib.request.Request(url, headers={"User-Agent": "JarvisClips/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as output:
        if urllib.parse.urlparse(response.url).scheme != "https":
            raise ValueError("Source redirected to an insecure URL")
        size = 0
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_SOURCE_BYTES:
                raise ValueError("Source exceeds 100 MB download limit")
            output.write(chunk)


def probe(path):
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,codec_name,width,height", "-of", "json", str(path)
    ], text=True))


def render(spec, source, destination):
    source_info = probe(source)
    duration = float(source_info["format"]["duration"])
    if spec.get("start", 0) + spec["duration"] > duration + 0.05:
        raise ValueError("Requested clip extends beyond the actual source")
    with tempfile.TemporaryDirectory(prefix="jarvis-render-") as temp:
        (Path(temp) / "captions.ass").write_text(subtitles(spec), encoding="utf-8")
        graph = (
            "[0:v]split=2[front][back];"
            "[back]scale=720:1280:force_original_aspect_ratio=increase,"
            "crop=720:1280,boxblur=24:2,eq=brightness=-0.4[bg];"
            "[front]scale=720:720:force_original_aspect_ratio=decrease[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,ass=captions.ass[out]"
        )
        if spec.get("layout") == "portrait":
            source_video = next(s for s in source_info["streams"] if s["codec_type"] == "video")
            if abs(source_video["width"] / source_video["height"] - 9 / 16) > 0.02:
                raise ValueError("Portrait layout requires a source already close to 9:16")
            graph = "[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1,ass=captions.ass[out]"
        if spec.get("layout") == "portrait_crop":
            position = spec.get("crop_position", 0.5)
            graph = f"[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280:x=(iw-720)*{position}:y=(ih-1280)/2,setsar=1,ass=captions.ass[out]"
        subprocess.run([
            "ffmpeg", "-v", "error", "-nostdin", "-y", "-ss", str(spec.get("start", 0)),
            "-i", str(source.resolve()), "-t", str(spec["duration"]), "-filter_complex", graph,
            "-map", "[out]", "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "21",
            "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart", str(destination.resolve())
        ], cwd=temp, check=True)
    info = probe(destination)
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), {})
    if (video.get("width"), video.get("height")) != (720, 1280):
        raise ValueError("Rendered video dimensions are incorrect")
    if abs(float(info["format"]["duration"]) - spec["duration"]) > 0.15:
        raise ValueError("Rendered duration does not match the manifest")
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--source-file", type=Path, help="Use a previously downloaded source")
    parser.add_argument("--output", type=Path, default=Path("output"))
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--silent", action="store_true", help="Internal base render only; not approved for new publication")
    parser.add_argument("--model", type=Path, default=Path(os.environ.get("JARVIS_VOICE_MODEL", Path(__file__).resolve().parents[1] / "work/models/en_US-ljspeech-high.onnx")))
    parser.add_argument("--music-file", type=Path, help="Use the reviewed licensed track already downloaded")
    args = parser.parse_args()
    spec = validate(json.loads(args.manifest.read_text(encoding="utf-8")))
    if args.validate_only:
        print(f"Valid manifest: {spec['id']} (rights declaration checked; not independent proof of rights)")
        return
    for program in ("ffmpeg", "ffprobe"):
        if not shutil.which(program):
            parser.error(f"{program} must be installed")
    output = args.output.resolve() / spec["id"]
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="jarvis-source-") as temp:
        source = args.source_file or Path(temp) / "source.mp4"
        if not args.source_file:
            download(spec["source"]["download"], source)
        info = render(spec, source, output / "video.mp4")
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    audio_result = None
    if not args.silent:
        from piper import PiperVoice
        from add_audio import add_audio
        settings = json.loads((Path(__file__).resolve().parents[1] / "config/audio.json").read_text())
        if hashlib.sha256(args.model.read_bytes()).hexdigest() != settings["voice"]["model_sha256"]:
            raise ValueError("Download the reviewed voice model before rendering audio")
        if hashlib.sha256(Path(str(args.model) + ".json").read_bytes()).hexdigest() != settings["voice"]["config_sha256"]:
            raise ValueError("Unreviewed voice configuration")
        voice = PiperVoice.load(args.model)
        with tempfile.TemporaryDirectory(prefix="jarvis-sound-") as temp:
            audio_result = add_audio(spec, output / "video.mp4", output / "video-audio.mp4", voice, Path(temp), settings, args.music_file)
        (output / "video-audio.mp4").replace(output / "video.mp4")
        (output / "video-audio.audio.json").replace(output / "audio.json")
        info = audio_result["probe"]
    video_hash = hashlib.sha256((output / "video.mp4").read_bytes()).hexdigest()
    metadata = {
        "id": spec["id"], "title": spec["title"], "description": spec.get("description", ""),
        "audience": spec["audience"], "status": "rendered_not_published", "audio": audio_result["audio"] if audio_result else "silent_base_do_not_publish",
        "created_at": datetime.now(timezone.utc).isoformat(), "source": spec["source"],
        "source_sha256": source_hash, "video_sha256": video_hash, "probe": info,
        "publishing_blocker": "Needs an inspected video, a media URL reachable by Metricool, and a confirmed scheduling response."
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    (output / "captions.ass").write_text(subtitles(spec), encoding="utf-8")
    print(f"Rendered {output / 'video.mp4'}; no upload or publication performed")


if __name__ == "__main__":
    main()

