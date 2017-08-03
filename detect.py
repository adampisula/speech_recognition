import pyaudio
import wave
import sys
import os
import numpy as np
from scipy.io import wavfile

def average(val):
    sum = 0

    for el in val:
        sum += el

    return sum / len(val)

def highest(val):
    best = 0

    for el in val:
        if el > best:
            best = el

    return best

#CONFIG
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = int(RATE / 10)
NOISE_SECONDS = 5

#AUDIO CONFIG
audio = pyaudio.PyAudio()
stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK)

noiseList = [0] * 10 * NOISE_SECONDS

#NOISE FILTERING
print("Filtering noise...")

for i in range(0, 50):
    data = stream.read(CHUNK)
    amp = np.fromstring(data, np.int16).tolist()
    
    noiseList = noiseList[1:]
    noiseList.append(average(amp))

noise = int(average(noiseList))

print("Done.")
print("Noise level: " + str(noise))

#LISTENING
print("Listening...")

cache = 5
openRecord = [0] * cache
frames = []

speaking = False

i = 0

while True:
    #GET AUDIO
    data = stream.read(CHUNK)

    #GET VOLUME
    volume = np.fromstring(data, np.int16).tolist()
    volume = abs(int(average(volume)))
 
    #AVERAGE SOUND INTENSITY
    openRecord = openRecord[1:]
    openRecord.append(abs(volume - noise))

    openr = int(average(openRecord))

    #SPEECH DETECTION
    if openr > 25:
        frames.append(data)

    if (average(openRecord[-15:]) > 25) and (not speaking):
        speaking = True

    elif (average(openRecord[-15:]) < 25) and (speaking):
        speaking = False

        #SAVE TO FILE
        if (len(frames) > 10) and (len(frames) < 55):
            print("SPEECH DETECTED")
            print(len(frames))
            print("---")

            #SAVE TO .RAW FILE
            with open("resources/audio.raw", "wb") as file:
                file.write(b''.join(frames))

            #PLAY .RAW FILE
            #os.system("play -t raw -r 16k -e signed -b 16 -c 1 resources/audio.raw")

        frames = []

    #WRITE EVERY 3 VOLUME DATA
    if i % 3 == 0:
        sys.stdout.write(str(openr) + "    \r")
        sys.stdout.flush()

    i += 1
