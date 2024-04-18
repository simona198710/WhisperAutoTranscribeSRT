import time
import util
from faster_whisper import WhisperModel
import subprocess
import os
import datetime
import gc
import multiprocessing

import psutil
import time

root_dir = '/media/simon/stream'  # Specify the root directory
#root_dir = '/media/simon/from_e'
#root_dir = 'test'  # Specify the root directory

model = None

seenFiles = {}
seenFiles=util.load_data("seenFiles")
if not "files" in seenFiles:
	seenFiles["files"] = []

doneFiles = {}
doneFiles=util.load_data("doneFiles")
if not "files" in doneFiles:
	doneFiles["files"] = []

def check_cpu_temps():
		temps = psutil.sensors_temperatures()['coretemp']
		cpu_temps = [temp.current for temp in temps]
		print("Temps: "+str(cpu_temps))
		while True:
			# Get CPU temperature
			temps = psutil.sensors_temperatures()['coretemp']
			cpu_temps = [temp.current for temp in temps]
			#print("Temps: "+str(cpu_temps))
			
			# Check if any core temperature is above 75 degrees Celsius
			if any(temp > 75 for temp in cpu_temps):
				#print("Waiting for CPU temperatures to cool down...")
				time.sleep(3)  # Wait for 3 second
				temps = psutil.sensors_temperatures()['coretemp']
				cpu_temps = [temp.current for temp in temps]
				if any(temp > 73 for temp in cpu_temps):
					time.sleep(6)  # Wait for 6 second
			else:
				break


def transcribe(file,filename,folder,lang='auto'):
	global model
	
	start_time = time.time()
	check_cpu_temps()
	
	input_file = file
	output_file = 'out.wav'
	try:
		os.remove('out.wav')
	except:
		pass
	cmd = ['ffmpeg', '-i', input_file, '-hide_banner', '-loglevel', 'error', '-y', '-acodec', 'pcm_s16le', '-af', 'aresample=async=1', '-ac', '1', '-ar', '16000', output_file]

	subprocess.run(cmd, check=True)
	print("Audio extraction took %s seconds" % (time.time() - start_time))
	gc.collect()
	time.sleep(10)
	check_cpu_temps()
	
	if model is None:
		model_time = time.time()
		#model_size = "models/whisper-medium-int8"
		model_size = "models/whisper-large-int8"
		model = WhisperModel(model_size, device="cuda", compute_type="int8",local_files_only=True)
		print("Model init took %s seconds" % (time.time() - model_time))
		gc.collect()
	if not os.path.exists(output_file):  
		return
	audio_start_time = time.time()
	langs=["sv","en"]
	for lang in langs:
		segments, info = model.transcribe("out.wav",task="transcribe",beam_size=5, vad_filter=True, vad_parameters=dict(min_silence_duration_ms=3000),condition_on_previous_text=False, language=lang,best_of=3)
		print("Audio init took %s seconds" % (time.time() - audio_start_time))
		
		print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
		gc.collect()
		if not info.language in langs:
			print("Skipped wrong lang")
			return False

		segments_start_time = time.time()
		segment_time=time.time()
		subtitle_segments=[]
		i=0
		base_name, extension = os.path.splitext(filename)
		srt_file = folder+"/"+ base_name +"_"+lang+'.srt'
		with open(srt_file, 'w') as f:
			 f.write('\n')
		for segment in segments:
			segment_text = segment.text.replace('\n', ' ')
			start_time_seg = datetime.timedelta(seconds=segment.start)
			end_time = datetime.timedelta(seconds=segment.end)
			#subtitle_segments.append((start_time_seg, end_time, segment_text))
			base_name, extension = os.path.splitext(filename)
			srt_file = folder+"/"+ base_name +"_"+lang+'.srt'
			print("%s [%.2fs -> %.2fs] %s" % ((time.time() - segment_time),segment.start, segment.end, segment.text))
			with open(srt_file, 'a') as f:
				f.write(str(i+1) + '\n')
				f.write(str(start_time_seg) + ' --> ' + str(end_time) + '\n')
				f.write(segment_text + '\n\n')
			segment_time=time.time()
			gc.collect()
			i=i+1
			check_cpu_temps()
	
		'''	  
		# Write subtitle segments to SRT file
		base_name, extension = os.path.splitext(filename)
		srt_file = folder+"/"+ base_name + '.srt'
		gc.collect()
		with open(srt_file, 'w') as f:
			for i, segment in enumerate(subtitle_segments):
				start_time_srt = segment[0]
				end_time = segment[1]
				segment_text = segment[2]
				f.write(str(i+1) + '\n')
				f.write(str(start_time_srt) + ' --> ' + str(end_time) + '\n')
				f.write(segment_text + '\n\n')
		''' 
	
		print("Segment took %s seconds" % (time.time() - segments_start_time))
	print("Whole process took %s seconds" % (time.time() - start_time))
	#del model
	#model = None
	gc.collect()
	return

def transcribe_wrapper(file_path, file_name, folder):
	try:
		transcribe(file_path, file_name, folder,'sv')
		#transcribe(file_path, file_name, folder,'en')
		doneFiles["files"].append(file_path)
		util.save_data(doneFiles, "doneFiles")
		print(file_path + " transcribed")
	except Exception as e:
		print("An error occurred during transcription:", str(e))


def process_files(root_dir):
	for entry in os.scandir(root_dir):
		if entry.is_file():
			file_path = entry.path
			file_name = entry.name
			if (file_name.endswith('.mp4') or file_name.endswith('.flv') or file_name.endswith('.mkv') or file_name.endswith('.avi')) and file_path not in seenFiles["files"] and os.path.getmtime(file_path) < time.time() - 10:
				print("Going to transcribe " + file_path)
				seenFiles["files"].append(file_path)
				util.save_data(seenFiles, "seenFiles")
				gc.collect()
				p = multiprocessing.Process(target=transcribe_wrapper, args=(file_path, file_name, os.path.dirname(file_path)))
				p.start()
				p.join()
		elif entry.is_dir():
			process_files(entry.path)  # Recursive call to process files in subfolders

   
while True:
		process_files(root_dir)
		time.sleep(1800)
