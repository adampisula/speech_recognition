import pyaudio
import wave
import sys
import os
import threading
import numpy as np
from scipy.io import wavfile
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

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

def recognize(audio):
    audio = types.RecognitionAudio(content=audio)
    response = client.recognize(config, audio)

    if len(response.results) >= 1:
        alternatives = response.results[0].alternatives

        for alternative in alternatives:
            return alternative.transcript
    
    else:
        return None

def letter(word):
    letters = []
    count = []

    for z in range(0, len(word)):
        letter = word[z]

        if letter not in letters:
            letters.append(letter)
            count.append(word.count(letter))

    return count

def compareLetters(word1, word2):
    word1sim = 0
    word2sim = 0
    
    for l in word1:
        if l in word2:
            word2.replace(l, "", 1)
            word1sim += 1

    for l in word2:
        if l in word1:
            word1.replace(l, "", 1)
            word2sim += 1

    word1sim = float(word1sim) / len(word1)
    word2sim = float(word2sim) / len(word1)
    lengthSim = float(len(word2)) / float(len(word1))

    return (word1sim + word2sim + lengthSim) / 3

def comparePosition(word1, word2, position=-1):
    if position == -1:
        w2sim = 0

        for z in range(0, len(word2)):
            if word1[z] == word2[z]:
                w2sim += 1

        return float(w2sim) / float(len(word2))

    elif position == 1:
        w2sim = 0

        for z in range(0, len(word2)):
            if word1[len(word1) - z - 1] == word2[len(word2) - z - 1]:
                w2sim += 1

        return float(w2sim) / float(len(word2))

    else:
        off = int((len(word1) - len(word2)) / 2)
        w2sim = 0

        for z in range(0, len(word2)):
            if word1[z + off] == word2[z]:
                w2sim += 1

        return float(w2sim) / float(len(word2))

def similarity(word1, word2):
    testLeft = comparePosition(word1, word2, position=-1)
    testRight = comparePosition(word1, word2, position=1)
    testCenter = comparePosition(word1, word2, position=0)
    
    if testLeft >= testRight:
        result = testLeft

    else:
        result = testRight

    result += 2 * compareLetters(word1, word2)

    tests = 3
    
    if testCenter > 0.5:
        result += testCenter
        tests += 1 

    return result / tests

def bestMatch(val):
    if val == None:
        return None

    words = val.split(" ")
    
    best = 0
    bestId = 0
    curr = 0

    for i in range(0, len(words)):
        bestId = 0
        best = 0

        for j in range(0, len(fuw)):
            w1 = words[i]
            w2 = fuw[j]

            if len(w1) < len(w2):
                c = w1
                w1 = w2
                w2 = c

            curr = similarity(w1, w2)

            if curr > best:
                best = curr
                bestId = j

        if best > 0.7:
            words[i] = fuw[bestId]

    return ' '.join(words)

def filterNoise(duration):
    #NOISE FILTERING
    noiseList = [0] * 10 * duration

    for i in range(0, len(noiseList)):
        data = stream.read(CHUNK)
        amp = np.fromstring(data, np.int16).tolist()

        noiseList = noiseList[1:]
        noiseList.append(average(amp))

    n = int(average(noiseList))

    #print("\tNoise level: " + str(n))

    return n

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

#RECOGNITION CONFIG
client = speech.SpeechClient()

config = types.RecognitionConfig(
    encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code='pl-PL')

#FREQUENTLY USED WORDS
fuw = []

with open("data.txt", "r") as file:
    for line in file:
        fuw.append(line.strip().lower())

#LISTENING
print("Listening...")

cache = 5
openRecord = [0] * cache
frames = []

speaking = False

i = 0

while True:
    #NOISE FILTERING
    if (i % 200 == 0) and (not speaking):
        noise = filterNoise(2)
        i = 0

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

    if (average(openRecord[-20:]) > 25) and (not speaking):
        speaking = True

    elif (average(openRecord[-25:]) < 25) and (speaking):
        speaking = False

        #SAVE TO FILE
        if (len(frames) > 10) and (len(frames) < 70):
            #RECOGNIZE AUDIO
            recognized = bestMatch(recognize(b''.join(frames)))

            if recognized != None:
                print(str(recognized))

            #SAVE TO .RAW FILE
            #with open("resources/audio.raw", "wb") as file:
            #    file.write(b''.join(frames))

            #PLAY .RAW FILE
            #os.system("play -t raw -r 16k -e signed -b 16 -c 1 resources/audio.raw")

        frames = []

    #WRITE EVERY 3 VOLUME DATA
    #if i % 3 == 0:
    #    sys.stdout.write(str(openr) + "    \r")
    #    sys.stdout.flush()

    i += 1
