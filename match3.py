import argparse
import copy
import datetime
import time
import librosa
import numpy as np
from scipy.signal import correlate
import math
import matplotlib.pyplot as plt

import ffmpeg
import librosa
import soundfile as sf

#import pyaudio

method_count = 0

'''
use ffmpeg steaming, which supports more format for streaming
'''

def load_audio_file(file_path, sr=None):
    # Create ffmpeg process
    process = (
        ffmpeg
        .input(file_path)
        .output('pipe:', format='wav', acodec='pcm_s16le', ac=1, ar=sr, loglevel="quiet")
        .run_async(pipe_stdout=True)
    )
    data = process.stdout.read()
    process.wait()
    return np.frombuffer(data, dtype="int16")
    #return librosa.load(file_path, sr=sr, mono=True)  # mono=True ensures a single channel audio


def cross_similarity_method(clip,audio,sr):
    global method_count
    hop_length = 1024
    chroma_ref = librosa.feature.chroma_cqt(y=clip, sr=sr, hop_length=hop_length)
    chroma_comp = librosa.feature.chroma_cqt(y=audio, sr=sr, hop_length=hop_length)
    # Use time-delay embedding to get a cleaner recurrence matrix
    x_ref = librosa.feature.stack_memory(chroma_ref, n_steps=10, delay=3)
    x_comp = librosa.feature.stack_memory(chroma_comp, n_steps=10, delay=3)
    xsim = librosa.segment.cross_similarity(x_comp, x_ref)
    print(xsim)
    return xsim


# sample rate needs to be the same for both or bugs will happen
def mfcc_method(clip,audio,sr):
    global method_count

    frame = len(clip)
    hop_length = 512  # Ensure this matches the hop_length used for Mel Spectrogram

    # Extract MFCC features
    clip_mfcc = librosa.feature.mfcc(y=clip, sr=sr, hop_length=hop_length)
    audio_mfcc = librosa.feature.mfcc(y=audio, sr=sr, hop_length=hop_length)


    distances = []
    for i in range(audio_mfcc.shape[1] - clip_mfcc.shape[1] + 1):
        dist = np.linalg.norm(clip_mfcc - audio_mfcc[:, i:i+clip_mfcc.shape[1]])
        distances.append(dist)

    # Find minimum distance and its index
    match_index = np.argmin(distances)
    min_distance = distances[match_index]

    # # Optional: plot the two MFCC sequences
    # plt.figure(figsize=(10, 4))
    # plt.subplot(1, 2, 1)
    # plt.title('Main Audio MFCC')
    # plt.imshow(audio_mfcc.T, aspect='auto', origin='lower')
    # plt.subplot(1, 2, 2)
    # plt.title('Pattern Audio MFCC')
    # plt.imshow(clip_mfcc.T, aspect='auto', origin='lower')
    # plt.tight_layout()
    # plt.savefig(f'./tmp/MFCC.png')
    # plt.close()

    #distances_ratio = [dist / min_distance for dist in distances]

    # Optional: plot the correlation graph to visualize
    plt.figure(figsize=(20,8))
    plt.plot(distances)
    plt.title('distances')
    plt.xlabel('index')
    plt.ylabel('distance')
    plt.savefig(f'./tmp/mfcc{method_count}.png')

    distances_selected = np.where(distances / min_distance <= 1.05)[0]


    # Convert match index to timestamp
    match_times = (distances_selected * hop_length) / sr  # sr is the sampling rate of audio

    method_count = method_count + 1
    return match_times

def correlation_method(clip,audio,sr):
    global method_count
    threshold = 0.4  # Threshold for distinguishing peaks, need to be smaller for larger clips
    # Cross-correlate and normalize correlation
    correlation = correlate(audio, clip, mode='valid')
    correlation = np.abs(correlation)
    correlation /= np.max(correlation)
    print("correlation")
    print(len(correlation))
    print(len(audio))
    correlation=correlation[:-len(clip)]

    # Optional: plot the correlation graph to visualize
    plt.figure(figsize=(10, 4))
    plt.plot(correlation)
    plt.title('Cross-correlation between the audio clip and full track')
    plt.xlabel('Lag')
    plt.ylabel('Correlation coefficient')
    plt.savefig(f'./tmp/cross_correlation{method_count}.png')
    plt.close()

    peak_max = np.max(correlation)
    index_max = np.argmax(correlation)
    print("peak_max",peak_max)
    #print("peak_before",correlation[index_max-sr])
    #print("peak_after",correlation[index_max+sr])
    print("index_max",index_max)

    # Detect if there are peaks exceeding the threshold
    peaks = []

    for i,col in enumerate(correlation):
        if i >= len(correlation)-len(clip) - 1:
            #print("skipping placeholder peak",i)
            continue
        if col >= threshold:
            peaks.append(i)
            #print("peak",col)
            #print("peak_before",correlation[i-sr])
            #print("peak_after",correlation[i+sr])

    peak_times = np.array(peaks) / sr
    method_count=method_count+1
    return peak_times

# sliding_window: for previous_chunk in seconds from end
# index: for debugging by saving a file for audio_section
# seconds_per_chunk: default seconds_per_chunk
def process_chunk(chunk, clip, sr, previous_chunk,sliding_window,index,seconds_per_chunk,norm,method="correlation"):
    clip_length = len(clip)
    new_seconds = len(chunk)/sr
    # Concatenate previous chunk for continuity in processing
    if(previous_chunk is not None):
        print("prev",len(previous_chunk)/sr)
        if(new_seconds < seconds_per_chunk): # too small
            subtract_seconds = -(new_seconds-(sliding_window+seconds_per_chunk))
            audio_section_temp = np.concatenate((previous_chunk, chunk))[(-(sliding_window+seconds_per_chunk)*sr):]    
            audio_section = np.concatenate((audio_section_temp,clip))
        else:
            subtract_seconds = sliding_window
            audio_section = np.concatenate((previous_chunk[(-sliding_window*sr):], chunk,clip))
    else:
        subtract_seconds = 0
        audio_section = np.concatenate((chunk,clip))


    print(f"subtract_seconds: {subtract_seconds}")
    print(f"new_seconds: {new_seconds}")    


    #sf.write(f"./tmp/audio_section{index}.wav", copy.deepcopy(audio_section), sr)
    # Normalize the current chunk
    audio_section = audio_section / np.max(np.abs(audio_section))

    sf.write(f"./tmp/audio_section{index}.wav", copy.deepcopy(audio_section), sr)

    if method == "correlation":
        peak_times = correlation_method(clip, audio=audio_section, sr=sr)
    elif method == "mfcc":
        peak_times = mfcc_method(clip, audio=audio_section, sr=sr)
    elif method == "cross_similarity_method":
        peak_times = cross_similarity_method(clip, audio=audio_section, sr=sr)
    else:
        raise "unknown method"
    print(peak_times)
    # look back just in case missed something
    peak_times_final = [peak_time - subtract_seconds for peak_time in peak_times]
    #for item in correlation:
    #    if item > threshold:
    #        print(item)
    return peak_times_final

def find_clip_in_audio_in_chunks(clip_path, full_audio_path, method="correlation"):
    target_sample_rate = 16000

    # Load the audio clip
    clip = load_audio_file(clip_path,sr=target_sample_rate) # 16k

    norm=np.max(np.abs(clip))
    # Normalize the clip
    #clip = clip / np.max(np.abs(clip))

    sf.write(f"./tmp/clip.wav", copy.deepcopy(clip), target_sample_rate)

    # Initialize parameters

    previous_chunk = None  # Buffer to maintain continuity between chunks
    #print("previous_chunk")
    #print(previous_chunk)
    #print(len(previous_chunk))
    all_peak_times = []

    # Create ffmpeg process
    process = (
        ffmpeg
        .input(full_audio_path)
        .output('pipe:', format='wav', acodec='pcm_s16le', ac=1, ar=target_sample_rate, loglevel="quiet")
        .run_async(pipe_stdout=True)
    )

    seconds_per_chunk = 200
    sliding_window = 10

    # for streaming
    frame_length = (seconds_per_chunk * target_sample_rate)
    chunk_size=frame_length * 2   # times two because it is 2 bytes per sample
    i = 0
    # Process audio in chunks
    while True:
        in_bytes = process.stdout.read(chunk_size)
        if not in_bytes:
            break
        # Convert bytes to numpy array
        chunk = np.frombuffer(in_bytes, dtype="int16")
        #sf.write(f"./tmp/sound{i}.wav", copy.deepcopy(chunk), target_sample_rate)
        #print("chunk....")
        #print(len(chunk))
        #exit(1)
        # Process audio data with Librosa (e.g., feature extraction)
        # ... your Librosa processing here ...
        peak_times = process_chunk(chunk=chunk, clip=clip, sr=target_sample_rate, 
                                                previous_chunk=previous_chunk,
                                                sliding_window=sliding_window,index=i,
                                                seconds_per_chunk=seconds_per_chunk, method=method,norm=norm)
        if len(peak_times):
            peak_times_from_beginning = [time + (i*seconds_per_chunk) for time in peak_times]
            #print(f"Found occurrences at: {peak_times} seconds, chunk {i}")
            all_peak_times.extend(peak_times_from_beginning)
            #all_correlation.extend(correlation)
        
        # Update previous_chunk to current chunk
        previous_chunk = chunk
        i = i + 1

    process.wait()

    return all_peak_times


# def find_clip_in_audio_in_chunks2(clip_path, full_audio_path, chunk_duration=10):
#     target_sample_rate = 16000

#     # Load the audio clip
#     clip, sr_clip = load_audio_file(clip_path, sr=target_sample_rate)

#     # Check if sampling rates match, resample if necessary
#     if sr_clip != target_sample_rate:
#         raise "mismatch"

#     # Write the audio data to a new WAV file
#     sf.write("./tmp/test.wav", copy.deepcopy(clip), target_sample_rate)

#     # Normalize the clip
#     clip = clip / np.max(np.abs(clip))

#     # Initialize parameters
#     threshold = 0.8  # Threshold for distinguishing peaks
#     previous_chunk = np.zeros_like(clip)  # Buffer to maintain continuity between chunks
    
#     all_peak_times = []
#     all_correlation = []

#     # Create ffmpeg process
#     process = (
#         ffmpeg
#         .input(full_audio_path)
#         .output('pipe:', format='wav', acodec='pcm_s16le', ac=1, ar=target_sample_rate)
#         .run_async(pipe_stdout=True)
#     )

#     # for streaming
#     seconds_per_chunk = 10
#     #frame_length = (seconds_per_chunk * target_sample_rate)
#     #chunk_size=frame_length

#     # Calculate samples per interval
#     samples_per_interval = int(target_sample_rate * seconds_per_chunk * 2) # times two because it is 2 bytes per sample

#     chunk_size=4096
#     # Process audio in intervals
#     buffer = []

#     i = 0

#     frame_length = (2048 * sr_clip)

#     while True:
#         in_bytes = process.stdout.read(frame_length)
#         if not in_bytes:
#             break
#         buffer.append(np.frombuffer(in_bytes, dtype="int16"))
        
#         if len(buffer) * chunk_size >= samples_per_interval:
#             audio_data = np.concatenate(buffer)
#             # Process 10-second interval audio data with Librosa
#             # Write the audio data to a new WAV file
#             #sf.write(f"./tmp/sound{i}.wav", copy.deepcopy(audio_data), target_sample_rate)

#             #exit(0)    
#             peak_times, correlation = process_chunk(audio_data, clip, target_sample_rate, threshold, previous_chunk)
#             if len(peak_times):
#                 peak_times_from_beginning = [time + (i*seconds_per_chunk) for time in peak_times]
#                 print(f"Found occurrences at: {peak_times_from_beginning} seconds, chunk {i}")
#                 all_peak_times.extend(peak_times_from_beginning)
#                 all_correlation.extend(correlation)

#             # Update previous_chunk to current chunk
#             previous_chunk = audio_data
#             i = i + 1
#             # Clear buffer for next interval
#             buffer = []

#     # Process remaining audio (if any)
#     if buffer:
#         audio_data = np.concatenate(buffer)
#         # ... your Librosa processing here ...
#         peak_times, correlation = process_chunk(audio_data, clip, target_sample_rate, threshold, previous_chunk)
#         if len(peak_times):
#             peak_times_from_beginning = [time + (i*seconds_per_chunk) for time in peak_times]
#             print(f"Found occurrences at: {peak_times_from_beginning} seconds, chunk {i}")
#             all_peak_times.extend(peak_times_from_beginning)
#             all_correlation.extend(correlation)
        
#         # Update previous_chunk to current chunk
#         previous_chunk = audio_data
#         i = i + 1

#     process.wait()

#     return all_peak_times, all_correlation




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pattern-file', metavar='pattern file', type=str, help='pattern file')
    parser.add_argument('--audio-file', metavar='audio file', type=str, help='audio file to find pattern')
    parser.add_argument('--method', metavar='method', type=str, help='correlation,mfcc,melspectrogram',default="correlation")
    #parser.add_argument('--window', metavar='seconds', type=int, default=10, help='Only use first n seconds of the audio file')
    args = parser.parse_args()
    #print(args.method)

    # Find clip occurrences in the full audio
    peak_times = find_clip_in_audio_in_chunks(args.pattern_file, args.audio_file, method=args.method)

    freq = {}

    for peak in peak_times:
        i = math.floor(peak)
        cur = freq.get(i, 0)
        freq[i] = cur + 1

    print(freq)

    print({k: v for k, v in sorted(freq.items(), key=lambda item: item[1])})

    peak_times_clean = list(dict.fromkeys([math.floor(peak) for peak in peak_times]))

    #print("Clip occurs at the following times (in seconds):", peak_times_clean)

    for offset in peak_times_clean:
        print(f"Clip occurs at the following times (in seconds): {str(datetime.timedelta(seconds=offset))}" )
    #    #print(f"Offset: {offset}s" )
    


if __name__ == '__main__':
    main()
