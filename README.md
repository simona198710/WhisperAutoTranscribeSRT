Auto transcription system designed to automatically process audio files from videos, extract spoken content, and save it as text in the SRT subtitle format.<br>
The script is built with a focus on managing system resources and efficiency, regularly checking system temperatures to avoid cpu overheating.<br>
Usage: Edit root_dir in run.py, the script will crawl all subdirectories and transcribe all videofiles by first extracting its audio using ffmpeg.<br>
Currently it transcribes each file as both swedish and english.<br>
Each filepath transcribed will be saved to json, to avoid being transcribed more than once.
