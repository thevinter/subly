# Subtly

This program automates the process of generating subtitles for video files. It:

- Extracts audio from videos.
- Transcribes the audio using OpenAI's Whisper API.
- Translates the transcriptions into a desired language using OpenAI's GPT-4 model.
- Generates SRT subtitle files.
- Optionally creates videos with soft or hard subtitles.
- Supports batch processing of multiple videos in a folder.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Command-Line Arguments](#command-line-arguments)
  - [Interactive CLI Prompts](#interactive-cli-prompts)
  - [Examples](#examples)
- [Output Structure](#output-structure)
- [Important Notes](#important-notes)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Contributing](#contributing)
- [Contact](#contact)

## Features

- **Audio Extraction**: Extracts audio from video files and converts it to MP3 format to reduce file size.
- **Transcription**: Uses OpenAI's Whisper API to transcribe audio into text.
- **Translation**: Translates transcriptions into the desired language using OpenAI's GPT-4 model.
- **Subtitle Generation**: Creates SRT files for both the original and translated subtitles.
- **Video Generation**: Optionally generates videos with soft (can be toggled on/off) or hard (permanently embedded) subtitles.
- **Batch Processing**: Processes a single video file or all video files in a specified folder.

## Requirements

- **Python 3.6 or higher**
- **FFmpeg**: Must be installed and accessible from the command line.
- **OpenAI API Key**: You need an API key from OpenAI with access to the Whisper and GPT-4 models.
- **Python Libraries**:
  - `ffmpeg-python`
  - `openai`
  - `argparse`
  - `python-dotenv` (optional, for loading environment variables)

## Installation

1. **Clone or Download the Repository**:

   ```bash
   git clone https://github.com/thevinter/subtly
   cd subtly
   ```

2. **Set Up a Virtual Environment** (optional but recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use 'venv\Scripts\activate'
   ```

3. **Install Required Python Packages**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Install FFmpeg**:

   - **Linux**: Install via your package manager (e.g., `sudo apt-get install ffmpeg`).
   - **macOS**: Install via Homebrew (`brew install ffmpeg`).
   - **Windows**: Download from the [FFmpeg website](https://ffmpeg.org/download.html) and add it to your system PATH.

5. **Set Up OpenAI API Key**:

   - Sign up for an account at [OpenAI](https://openai.com/).
   - Obtain your API key from the OpenAI dashboard.
   - Set the API key as an environment variable:

## Usage

### Command-Line Arguments

The script can process a single video file or all video files in a folder.

- **Process a Single Video File**:

  ```bash
  python subgen.py <filename>
  ```

- **Process All Videos in a Folder**:

  ```bash
  python subgen.py -f <folder>
  ```

### Interactive CLI Prompts

When you run the script, it will prompt you for:

1. **Desired Language for Translation**:

   - Enter the language you want the subtitles translated into (e.g., `Italian`, `Spanish`, `French`).

2. **Generate Output Video with Subtitles**:

   - Decide whether to generate an output video with the subtitles (`yes` or `no`).

3. **Subtitle Type**:

   - If you choose to generate a video, select the subtitle type:
     - **Soft Subtitles** (`soft`): Subtitles can be turned on/off by the viewer.
     - **Hard Subtitles** (`hard`): Subtitles are permanently embedded into the video.
     - **Both** (`both`): Generates both versions.

## Output Structure

The script saves the results in an `out/` directory with the following structure:

```
out/
└── <videoname>/
    ├── output_audio.mp3
    ├── output_subtitles.srt
    ├── translated_subtitles.srt
    ├── <videoname>_softsubs.mp4  # If soft subtitles were generated
    └── <videoname>_hardsubs.mp4  # If hard subtitles were generated
```

## Important Notes

- **Subtitle Accuracy**: The accuracy of transcriptions and translations depends on the quality of the audio and the capabilities of the OpenAI models.

- **Supported Languages**: Afrikaans, Arabic, Armenian, Azerbaijani, Belarusian, Bosnian, Bulgarian, Catalan, Chinese, Croatian, Czech, Danish, Dutch, English, Estonian, Finnish, French, Galician, German, Greek, Hebrew, Hindi, Hungarian, Icelandic, Indonesian, Italian, Japanese, Kannada, Kazakh, Korean, Latvian, Lithuanian, Macedonian, Malay, Marathi, Maori, Nepali, Norwegian, Persian, Polish, Portuguese, Romanian, Russian, Serbian, Slovak, Slovenian, Spanish, Swahili, Swedish, Tagalog, Tamil, Thai, Turkish, Ukrainian, Urdu, Vietnamese, and Welsh.

- **FFmpeg Compatibility**: Ensure that your FFmpeg installation supports the required codecs and formats. The script uses `mov_text` for soft subtitles in MP4 containers.

- **Supported Video Formats**: The script processes video files with the following extensions: `.mp4`, `.mov`, `.avi`, `.mkv`.

## Troubleshooting

- **Audio File Size Limit**:

  - The OpenAI Whisper API has a maximum audio file size limit of 25 MB.
  - Subtly converts audio to MP3 format with reduced bitrate to keep the file size within limits.
  - For longer videos, consider splitting the audio or increasing compression.

- **FFmpeg Errors**:

  - **Codec Not Supported**: Ensure that FFmpeg supports the `mov_text` codec for MP4 soft subtitles.
  - **Invalid Subtitle Format**: Check that the SRT files are correctly formatted.
  - **Permission Issues**: Ensure the script has read/write permissions for the input and output directories.

- **OpenAI API Errors**:

  - **Authentication**: Ensure your API key is correctly set and has the necessary permissions.
  - **Rate Limits**: Check if you have exceeded your API rate limits or usage quota.
  - **Model Access**: Verify that your OpenAI account has access to the Whisper and GPT-4 models.

- **Script Hangs or Freezes**:

  - This may occur due to network issues or large input sizes.
  - Reduce the `block_size` in the script to process smaller chunks at a time.
