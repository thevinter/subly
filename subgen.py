import ffmpeg
import json
import datetime
import re
import sys
import os
import argparse
from openai import OpenAI
client = OpenAI()

def extract_audio(video_path, audio_path):
    try:
        (
            ffmpeg
            .input(video_path)
            .output(
                audio_path,
                acodec='libmp3lame',
                ac=1,
                ar='16k',
                audio_bitrate='64k'
            )
            .overwrite_output()
            .run(quiet=True)
        )
        print(f"[INFO] Audio extracted to {audio_path}")
    except ffmpeg.Error as e:
        print(f"[ERROR] Failed to extract audio from {video_path}: {e}")
        sys.exit(1)

def transcribe_audio(audio_path):
    try:
        with open(audio_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model='whisper-1',
                file=audio_file,
                response_format="verbose_json"
            )
        print("[INFO] Audio transcription completed.")
        return transcript
    except Exception as e:
        print(f"[ERROR] Failed to transcribe audio: {e}")
        sys.exit(1)

def format_timestamp(seconds):
    milliseconds = int(round(seconds * 1000))
    hours = milliseconds // (3600 * 1000)
    milliseconds = milliseconds % (3600 * 1000)
    minutes = milliseconds // (60 * 1000)
    milliseconds = milliseconds % (60 * 1000)
    seconds = milliseconds // 1000
    milliseconds = milliseconds % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def transcription_to_srt(transcription, srt_path):
    segments = transcription.segments  # Updated access
    try:
        with open(srt_path, 'w', encoding='utf-8') as srt_file:
            for idx, segment in enumerate(segments, start=1):
                start_time = format_timestamp(segment.start)
                end_time = format_timestamp(segment.end)
                text = segment.text.strip()
                srt_file.write(f"{idx}\n{start_time} --> {end_time}\n{text}\n\n")
        print(f"[INFO] SRT file saved to {srt_path}")
    except Exception as e:
        print(f"[ERROR] Failed to write SRT file: {e}")
        sys.exit(1)

def parse_srt(srt_path):
    try:
        with open(srt_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        print(f"[ERROR] Failed to read SRT file: {e}")
        sys.exit(1)

    pattern = re.compile(
        r'(\d+)\n'             # Subtitle index
        r'(\d{2}:\d{2}:\d{2},\d{3})\s-->\s'  # Start time
        r'(\d{2}:\d{2}:\d{2},\d{3})\n'       # End time
        r'(.*?)\n\n',          # Subtitle text
        re.DOTALL
    )

    subtitles = []
    for match in pattern.finditer(content):
        index = int(match.group(1))
        start_time = match.group(2)
        end_time = match.group(3)
        text = match.group(4).strip()
        subtitles.append({
            'index': index,
            'start_time': start_time,
            'end_time': end_time,
            'text': text
        })

    return subtitles

def divide_into_blocks(subtitles, block_size):
    return [subtitles[i:i + block_size] for i in range(0, len(subtitles), block_size)]

def translate_block(block, target_language):
    # Prepare the text with markers
    text_to_translate = ''
    for subtitle in block:
        text_to_translate += f"### Subtitle {subtitle['index']}\n{subtitle['text']}\n"

    # Custom prompt
    prompt = (
        f"Please translate the following text to {target_language}. "
        "Keep the markers (### Subtitle N) in place. Do not change anything else.\n\n"
        f"{text_to_translate}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are an assistant that translates subtitles into {target_language}. "
                        "Just translate the provided text. Try to keep the same length for each of the phrases."
                    )
                },
                {"role": "user", "content": prompt}
            ],
        )
        print("[INFO] Translation API call completed.")
    except Exception as e:
        print(f"[ERROR] Failed to translate subtitles: {e}")
        sys.exit(1)

    # Extract the translated text
    translated_text = response.choices[0].message.content

    # Split the translated text back into subtitles
    translated_subtitles = {}
    pattern = re.compile(r'### Subtitle (\d+)\n(.*?)(?=\n### Subtitle \d+|\Z)', re.DOTALL)
    for match in pattern.finditer(translated_text):
        index = int(match.group(1))
        text = match.group(2).strip()
        translated_subtitles[index] = text

    return translated_subtitles

def write_translated_srt(subtitles, translated_subtitles, output_srt_path):
    try:
        with open(output_srt_path, 'w', encoding='utf-8') as srt_file:
            for subtitle in subtitles:
                index = subtitle['index']
                start_time = subtitle['start_time']
                end_time = subtitle['end_time']
                text = translated_subtitles.get(index, subtitle['text'])  # Use original text if translation is missing
                srt_file.write(f"{index}\n{start_time} --> {end_time}\n{text}\n\n")
        print(f"[INFO] Translated SRT file saved to {output_srt_path}")
    except Exception as e:
        print(f"[ERROR] Failed to write translated SRT file: {e}")
        sys.exit(1)

def generate_video_with_subtitles(video_path, srt_path, output_video_path, subtitle_type):

    import subprocess

    try:
        if subtitle_type == 'soft':
            command = [
                'ffmpeg',
                '-i', video_path,
                '-i', srt_path,
                '-c:v', 'copy',
                '-c:a', 'copy',
                '-c:s', 'mov_text',
                '-map', '0',
                '-map', '1',
                '-y',
                output_video_path
            ]
            print(f"[DEBUG] Running command: {' '.join(command)}")
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                print(f"[ERROR] FFmpeg failed with error:\n{result.stderr}")
                sys.exit(1)
        elif subtitle_type == 'hard':
            (
                ffmpeg
                .input(video_path)
                .output(
                    output_video_path,
                    vf=f"subtitles='{srt_path}'"
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        print(f"[INFO] Video with {subtitle_type} subtitles saved to {output_video_path}")
    except Exception as e:
        print(f"[ERROR] Failed to generate video with subtitles: {e}")
        sys.exit(1)


def process_video(video_file, args):
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    output_dir = os.path.join('out', base_name)
    os.makedirs(output_dir, exist_ok=True)

    # Update the audio file extension to .mp3
    audio_file = os.path.join(output_dir, 'output_audio.mp3')
    srt_file = os.path.join(output_dir, 'output_subtitles.srt')
    translated_srt_file = os.path.join(output_dir, 'translated_subtitles.srt')

    print(f"\nProcessing video: {video_file}")
    print("Extracting audio...")
    extract_audio(video_file, audio_file)

    print("Transcribing audio...")
    transcription_result = transcribe_audio(audio_file)

    print("Generating SRT file...")
    transcription_to_srt(transcription_result, srt_file)

    print("Parsing SRT file...")
    subtitles = parse_srt(srt_file)

    print("Dividing subtitles into blocks...")
    block_size = 50
    blocks = divide_into_blocks(subtitles, block_size)

    print(f"Translating subtitles to {args.language}...")
    translated_subtitles = {}
    for block in blocks:
        block_translations = translate_block(block, args.language)
        translated_subtitles.update(block_translations)

    print("Writing translated SRT file...")
    write_translated_srt(subtitles, translated_subtitles, translated_srt_file)

    if args.generate_video:
        if args.subtitle_type in ['soft', 'both']:
            output_video_soft = os.path.join(output_dir, f"{base_name}_softsubs.mp4")
            print("Generating video with soft subtitles...")
            generate_video_with_subtitles(video_file, translated_srt_file, output_video_soft, 'soft')
        if args.subtitle_type in ['hard', 'both']:
            output_video_hard = os.path.join(output_dir, f"{base_name}_hardsubs.mp4")
            print("Generating video with hard subtitles...")
            generate_video_with_subtitles(video_file, translated_srt_file, output_video_hard, 'hard')

    print(f"[SUCCESS] Processing of '{video_file}' completed.")

def main():
    parser = argparse.ArgumentParser(description='Subtitle Generator')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('filename', nargs='?', help='Path to the video file')
    group.add_argument('-f', '--folder', help='Path to the folder containing video files')
    args = parser.parse_args()

    # Interactive CLI
 
    args.language = input("Enter the desired language for translation (default: English): ").strip() or 'English'

    generate_video = input("Do you want to generate an output video with the subtitles? (yes/[no]): ").strip().lower() or 'no'
    if generate_video in ['yes', 'y']:
        args.generate_video = True
        print("\nSubtitles can be added in two ways:")
        print("1. Soft Subtitles: Subtitles can be turned on/off.")
        print("2. Hard Subtitles: Subtitles are permanently embedded into the video.")
        print("3. Both: Generate both versions.")
        subtitle_type = input("Do you want soft, hard subtitles, or both? (soft/hard/both) or (1/2/3): ").strip().lower()
        
        if subtitle_type in ['soft', '1']:
            args.subtitle_type = 'soft'
        elif subtitle_type in ['hard', '2']:
            args.subtitle_type = 'hard'
        elif subtitle_type in ['both', '3']:
            args.subtitle_type = 'both'
        else:
            print("Invalid option for subtitles. Defaulting to 'soft'.")
            args.subtitle_type = 'soft'
    else:
        args.generate_video = False

    # Process single file or all files in a folder
    if args.folder:
        if not os.path.isdir(args.folder):
            print(f"[ERROR] Folder '{args.folder}' does not exist.")
            sys.exit(1)
        video_files = [os.path.join(args.folder, f) for f in os.listdir(args.folder) if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]
        if not video_files:
            print(f"[ERROR] No video files found in folder '{args.folder}'.")
            sys.exit(1)
        for video_file in video_files:
            process_video(video_file, args)
    elif args.filename:
        if not os.path.isfile(args.filename):
            print(f"[ERROR] File '{args.filename}' does not exist.")
            sys.exit(1)
        process_video(args.filename, args)
    else:
        print("[ERROR] No input file or folder specified.")
        sys.exit(1)

if __name__ == '__main__':
    main()
