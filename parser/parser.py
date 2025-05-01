from mido import MidiFile
import json
import re
import sys
from collections import defaultdict

def parseMidi(filename):
    output = defaultdict(list)
    currInstrument = None
    activeNotes = {}
    totalTime = 0
    totalNotes = 0

    with open(filename, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()

        if line.startswith('MidiTrack(['):
            totalTime = 0
            currInstrument = None
            activeNotes = {}

        timeMatch = re.search(r'time=(\d+)', line)
        deltaTime = int(timeMatch.group(1)) if timeMatch else 0
        totalTime += deltaTime

        if "track_name" in line:
            nameMatch = re.search(r"name='([^']+)'", line)
            if nameMatch:
                currInstrument = nameMatch.group(1)

        if "note_on" in line and "velocity=0" not in line:
            totalNotes += 1
            noteMatch = re.search(r'note=(\d+)', line)
            if noteMatch and currInstrument:
                noteVal = int(noteMatch.group(1))
                activeNotes.setdefault(noteVal, []).append(totalTime)

        if "note_off" in line or ("note_on" in line and "velocity=0" in line):
            noteMatch = re.search(r'note=(\d+)', line)
            if noteMatch and currInstrument:
                noteVal = int(noteMatch.group(1))
                if noteVal in activeNotes and activeNotes[noteVal]:
                    startTime = activeNotes[noteVal].pop(0)
                    duration = totalTime - startTime
                    output[currInstrument].append({
                        "start": startTime,
                        "duration": duration,
                        "midiValue:": noteVal
                    })

        if "set_tempo" in line:
            tempoMatch = re.search(r'tempo=(\d+)', line)
            if tempoMatch:
                tempoVal = int(tempoMatch.group(1))
                tempoVal = 1 / tempoVal * 1000000 * 60 # tempo starts as microseconds per beat -> reciprocal -> beats per sec -> BPM
                output["Tempo"].append({
                    "start": totalTime,
                    "BPM": tempoVal
                })

        if "time_signature" in line:
            numMatch = re.search(r'numerator=(\d+)', line)
            denMatch = re.search(r'denominator=(\d+)', line)
            if numMatch and denMatch:
                numerator = int(numMatch.group(1))
                denominator = int(denMatch.group(1))
                output["TimeSig"].append({
                    "start": totalTime,
                    "numerator": numerator,
                    "denominator": denominator
                })

    output["TotalNotes"].append({
        "TotalNotes": totalNotes
    })

    return dict(output)

def createTxt(filepath):
    mid = MidiFile(filename=filepath, clip=True)
    with open("trackOutput.txt", "w") as f:
        for msg in mid.tracks:
            f.write(str(msg))
            f.write("\n")

def main():
    if len(sys.argv) != 2:
        print("Usage: python parser.py <input.mid>")
        sys.exit(1)

    midiIn = sys.argv[1]
    midiTxt = createTxt(midiIn)
    result = parseMidi("trackOutput.txt")

    outputFile = "output.json"

    with open(outputFile, 'w') as f:
        json.dump(result, f, indent=4)

    print(f"Output written to {outputFile}")

if __name__ == "__main__":
    main()