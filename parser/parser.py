from mido import MidiFile, tick2second
import json
import re
import sys
from collections import defaultdict

def fixTimeStamps(result):
    for track in result.keys():
        # skip over the keys that aren't midi tracks
        if track in ["TimeSig", "Tempo", "TotalNotes", "NoteRange"]:
            continue

        # track the tempo while iterating over each note, then convert
        # the timestamps into seconds (for Godot purposes!!)
        tempotrack = result["Tempo"]
        currentTempo = tempotrack[0]["tempo"]
        currentTempoIndex = 0
        currentNoteIndex = 0
        ticksElapsed = 0
        timeElapsed = 0

        # formula for getting note start time
        for note in result[track]:
            deltaTime = 0

            # move forward to the next tempo change event
            while currentTempoIndex + 1 < len(tempotrack) and tempotrack[currentTempoIndex + 1]["start"] <= note["start"]:
                deltaTime += tick2second(tempotrack[currentTempoIndex + 1]["start"] - ticksElapsed, 1024, currentTempo)

                ticksElapsed = tempotrack[currentTempoIndex + 1]["start"]

                # advance past the tempo change
                currentTempo = tempotrack[currentTempoIndex + 1]["tempo"]
                currentTempoIndex += 1
            
            deltaTime += tick2second(note["start"] - ticksElapsed, 1024, currentTempo)
            ticksElapsed = note["start"]

            timeElapsed += deltaTime

            # update "start" to seconds from ticks
            result[track][currentNoteIndex]["start"] = timeElapsed
            currentNoteIndex += 1

                
def fixDuration(result):
    for track in result.keys():
        if track in ["TimeSig", "Tempo", "TotalNotes", "NoteRange"]:
            continue

        # sort by note ends
        result[track] = sorted(result[track], key=lambda note: note["end"])

        # track the tempo while iterating over each note, then convert
        # the timestamps into seconds (for Godot purposes!!)
        tempotrack = result["Tempo"]
        currentTempo = tempotrack[0]["tempo"]
        currentTempoIndex = 0
        currentNoteIndex = 0
        ticksElapsed = 0
        timeElapsed = 0

        # formula for getting note start time
        for note in result[track]:
            deltaTime = 0

            # move forward to the next tempo change event
            while currentTempoIndex + 1 < len(tempotrack) and tempotrack[currentTempoIndex + 1]["start"] <= note["end"]:
                deltaTime += tick2second(tempotrack[currentTempoIndex + 1]["start"] - ticksElapsed, 1024, currentTempo)

                ticksElapsed = tempotrack[currentTempoIndex + 1]["start"]

                # advance past the tempo change
                currentTempo = tempotrack[currentTempoIndex + 1]["tempo"]
                currentTempoIndex += 1
            
            deltaTime += tick2second(note["end"] - ticksElapsed, 1024, currentTempo)
            ticksElapsed = note["end"]

            timeElapsed += deltaTime

            # update "end" to seconds from ticks
            result[track][currentNoteIndex]["end"] = timeElapsed

            #update "duration" to length of note in seconds
            result[track][currentNoteIndex]["duration"] = result[track][currentNoteIndex]["end"] - result[track][currentNoteIndex]["start"]
            
            currentNoteIndex += 1  

        # convert back to sorted by start
        result[track] = sorted(result[track], key=lambda note: note["start"])

def fixTempoTime(result):
    for track in result.keys():
        if track in ["TimeSig"]:
            tempotrack = result["Tempo"]
            currentTempo = tempotrack[0]["tempo"]
            currentTempoIndex = 0
            currentSigIndex = 0
            ticksElapsed = 0
            timeElapsed = 0

            for tempo in result[track]:
                deltaTime = 0

                # advance to next tempo change event
                while currentTempoIndex + 1 < len(tempotrack) and tempotrack[currentTempoIndex + 1]["start"] <= tempo["start"]:
                    deltaTime += tick2second(tempotrack[currentTempoIndex + 1]["start"] - ticksElapsed, 1024, currentTempo)

                    ticksElapsed = tempotrack[currentTempoIndex + 1]["start"]

                    # advance past the tempo change
                    currentTempo = tempotrack[currentTempoIndex + 1]["tempo"]
                    currentTempoIndex += 1

                deltaTime += tick2second(tempo["start"] - ticksElapsed, 1024, currentTempo)
                ticksElapsed = tempo["start"]

                timeElapsed += deltaTime

                # update "start" to seconds from ticks
                result[track][currentSigIndex]["start"] = timeElapsed
                currentSigIndex += 1

        elif track in ["Tempo"]:
            tempotrack = result["Tempo"]
            currentTempo = tempotrack[0]["tempo"]
            currentTempoIndex = 0
            ticksElapsed = 0
            timeElapsed = 0

            for tempo in result[track]:
                deltaTime = 0

                # advance to next tempo change event
                while currentTempoIndex + 1 < len(tempotrack) and tempotrack[currentTempoIndex + 1]["start"] <= tempo["start"]:
                    deltaTime += tick2second(tempotrack[currentTempoIndex + 1]["start"] - ticksElapsed, 1024, currentTempo)

                    ticksElapsed = tempotrack[currentTempoIndex + 1]["start"]

                    # advance past the tempo change
                    currentTempo = tempotrack[currentTempoIndex + 1]["tempo"]
                    currentTempoIndex += 1

                deltaTime += tick2second(tempo["start"] - ticksElapsed, 1024, currentTempo)
                ticksElapsed = tempo["start"]

                timeElapsed += deltaTime

                # update "start" to seconds from ticks
                result[track][currentTempoIndex]["start"] = timeElapsed

        else:
            continue

# Updates Tempo to BPM
def convertTempo(result):
    for track in result.keys():
        if track in ["Tempo"]:
            currTempoIndex = 0

            for tempo in result[track]:
                # tempo starts as microseconds per beat -> reciprocal -> beats per sec -> BPM
                tempoVal = result[track][currTempoIndex]["tempo"]
                tempoVal = 1 / tempoVal * 1000000 * 60
                result[track][currTempoIndex]["tempo"] = tempoVal
                currTempoIndex += 1

def parseMidi(filename):
    output = defaultdict(list)
    currInstrument = None
    activeNotes = {}
    totalTime = 0
    totalNotes = 0
    noteLow = 127
    noteHigh = 0

    with open(filename, "r") as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()

        # Resets start time and instrument for each track
        if line.startswith('MidiTrack(['):
            totalTime = 0
            currInstrument = None
            activeNotes = {}

        # tracks total elapsed time
        timeMatch = re.search(r'time=(\d+)', line)
        deltaTime = int(timeMatch.group(1)) if timeMatch else 0
        totalTime += deltaTime

        # Finds the name of the current track
        if "track_name" in line:
            nameMatch = re.search(r"name='([^']+)'", line)
            if nameMatch:
                currInstrument = nameMatch.group(1)

        # Detects start of a new note and adds it to a list until
        # its corresponding note_off is found
        if "note_on" in line and "velocity=0" not in line:
            totalNotes += 1
            noteMatch = re.search(r'note=(\d+)', line)
            if noteMatch and currInstrument:
                noteVal = int(noteMatch.group(1))

                # adjust midi note range
                if (noteVal < noteLow and noteVal > 21):
                    noteLow = noteVal
                if (noteVal > noteHigh):
                    noteHigh = noteVal

                activeNotes.setdefault(noteVal, []).append(totalTime)

        # Finds the corresponding note_on and removes it to the list of active
        # notes if a match is found and then adds it and its length to the json
        if "note_off" in line or ("note_on" in line and "velocity=0" in line):
            noteMatch = re.search(r'note=(\d+)', line)
            if noteMatch and currInstrument:
                noteVal = int(noteMatch.group(1))
                if noteVal in activeNotes and activeNotes[noteVal]:
                    startTime = activeNotes[noteVal].pop(0)
                    duration = totalTime - startTime
                    endTime = startTime + duration
                    # convert into seconds
                    # ()


                    output[currInstrument].append({
                        "start": startTime,
                        "end": endTime,
                        "duration": duration,
                        "midiValue": noteVal
                    })

        # converts tempo markings to BPM, puts it in the json
        if "set_tempo" in line:
            tempoMatch = re.search(r'tempo=(\d+)', line)
            if tempoMatch:
                tempoVal = int(tempoMatch.group(1))
                # tempo starts as microseconds per beat -> reciprocal -> beats per sec -> BPM
                # tempoVal = 1 / tempoVal * 1000000 * 60
                output["Tempo"].append({
                    "start": totalTime,
                    "tempo": tempoVal
                })
        
        # find the time signature, put it in the json
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
    output["NoteRange"].append({
        "high": noteHigh,
        "low": noteLow
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
    print(midiTxt)
    result = parseMidi("trackOutput.txt")
    fixTimeStamps(result)
    fixDuration(result)
    fixTempoTime(result)
    convertTempo(result)

    outputFile = "output2.json"

    with open(outputFile, 'w') as f:
        json.dump(result, f, indent=4)

    print(f"Output written to {outputFile}")

if __name__ == "__main__":
    main()