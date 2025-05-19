from mido import MidiFile, tick2second
import json
import re
import sys
from collections import defaultdict

TICKS_PER_BEAT = 480

def fixNoteTimeStamps(result):
    for track in result.keys():
        # skip over the keys that aren't midi tracks
        if track in ["TimeSig", "Tempo", "TotalNotes", "NoteRange", "MeasureStart"]:
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
                deltaTime += tick2second(tempotrack[currentTempoIndex + 1]["start"] - ticksElapsed, TICKS_PER_BEAT, currentTempo)

                ticksElapsed = tempotrack[currentTempoIndex + 1]["start"]

                # advance past the tempo change
                currentTempo = tempotrack[currentTempoIndex + 1]["tempo"]
                currentTempoIndex += 1
            
            deltaTime += tick2second(note["start"] - ticksElapsed, TICKS_PER_BEAT, currentTempo)
            ticksElapsed = note["start"]

            timeElapsed += deltaTime

            # update "start" to seconds from ticks
            result[track][currentNoteIndex]["start"] = timeElapsed
            currentNoteIndex += 1

                
def fixDuration(result):
    for track in result.keys():
        if track in ["TimeSig", "Tempo", "TotalNotes", "NoteRange", "MeasureStart"]:
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
                deltaTime += tick2second(tempotrack[currentTempoIndex + 1]["start"] - ticksElapsed, TICKS_PER_BEAT, currentTempo)

                ticksElapsed = tempotrack[currentTempoIndex + 1]["start"]

                # advance past the tempo change
                currentTempo = tempotrack[currentTempoIndex + 1]["tempo"]
                currentTempoIndex += 1
            
            deltaTime += tick2second(note["end"] - ticksElapsed, TICKS_PER_BEAT, currentTempo)
            ticksElapsed = note["end"]

            timeElapsed += deltaTime

            # update "end" to seconds from ticks
            result[track][currentNoteIndex]["end"] = timeElapsed

            #update "duration" to length of note in seconds
            result[track][currentNoteIndex]["duration"] = result[track][currentNoteIndex]["end"] - result[track][currentNoteIndex]["start"]
            
            currentNoteIndex += 1  

        # convert back to sorted by start
        result[track] = sorted(result[track], key=lambda note: note["start"])

def fixTimeSig(result):
    tempotrack = result["Tempo"]
    timesigtrack = result["TimeSig"]

    currTempoIndex = 0
    currentTempo = tempotrack[0]["tempo"]
    ticksElapsed = 0.0
    timeElapsed = 0.0

    # iterate over each time signature event in the entire track
    for timesigIndex in range(len(timesigtrack)):
        timesig = timesigtrack[timesigIndex]
        deltaTime = 0

        # For each tempo change event that exists between now and the next time sig change, process the amount of
        # ticks elapsed and covert each one to seconds.
        while currTempoIndex + 1 < len(tempotrack) and tempotrack[currTempoIndex + 1]["start"] <= timesig["start"]:
            # calculate how many ticks have passed since the previous tempo/timesig event
            deltaTicks = tempotrack[currTempoIndex + 1]["start"] - ticksElapsed
            deltaTime += tick2second(deltaTicks, TICKS_PER_BEAT, currentTempo)

            # advance the tempo track index
            currTempoIndex += 1
            currentTempo = tempotrack[currTempoIndex]["tempo"]
            ticksElapsed = tempotrack[currTempoIndex]["start"]

        # now that we've processed all the tempo changes, calculate the amount of time it takes to get from the most
        # recent tempo change event to the timesig event.
        deltaTicks = timesig["start"] - ticksElapsed
        deltaTime += tick2second(deltaTicks, TICKS_PER_BEAT, currentTempo)

        # update total time elapsed with our deltaTime
        timeElapsed += deltaTime

        # write the value to the json
        timesigtrack[timesigIndex]["start"] = timeElapsed


def fixTempoTime(result):
    tempotrack = result["Tempo"]

    prevStartTimeTicks = tempotrack[0]["start"]
    prevTempo = tempotrack[0]["tempo"]
    timeElapsed = 0

    for currTempoIndex in range(len(tempotrack)):
        # calculated how many ticks, and by extension, seconds, have passed since the last tempo update
        ticksElapsed = tempotrack[currTempoIndex]["start"] - prevStartTimeTicks
        deltaTime = tick2second(ticksElapsed, TICKS_PER_BEAT, prevTempo)
        timeElapsed += deltaTime

        # the current becomes the previous for the next iteration
        prevStartTimeTicks = tempotrack[currTempoIndex]["start"]
        prevTempo = tempotrack[currTempoIndex]["tempo"]

        # update the tempo start time in the json to be in seconds (not ticks)
        tempotrack[currTempoIndex]["start"] = timeElapsed

# Updates Tempo to BPM
def convertTempo(result):
    for track in result.keys():
        if track in ["Tempo"]:
            currTempoIndex = 0

            for tempo in result[track]:
                # tempo starts as microseconds per beat -> reciprocal -> beats per sec -> BPM
                tempoVal = result[track][currTempoIndex]["tempo"]
                tempoVal = round(1 / tempoVal * 1000000 * 60, 0)
                result[track][currTempoIndex]["tempo"] = tempoVal
                currTempoIndex += 1

def addMeasureNum(result):
    currTimeSigIndex = 0
    currNumerator = result["TimeSig"][currTimeSigIndex]["numerator"]
    currDenom = result["TimeSig"][currTimeSigIndex]["denominator"]

    measureStarts = [0.0]
    beatsSinceBarLine = 0
    currTime = 0
    currTempo = result["Tempo"][0]["tempo"]

    measureCount = 0

    for tempoChange in result["Tempo"]:
        deltaTime = tempoChange["start"] - currTime
        deltaBeats = deltaTime / (60 / currTempo) # trust that the tempo matches the denominator

        # If bar line has not been crossed
        if (beatsSinceBarLine + deltaBeats < currNumerator):
            beatsSinceBarLine += deltaBeats
            currTime += deltaTime
        # bar line has been crossed
        else:
            while (True):
                beatsLeft = currNumerator - beatsSinceBarLine
                secondsLeft = beatsLeft * (60 / currTempo) # calculate remaining time in measure

                # if there are no bar lines left break
                if (deltaBeats < beatsLeft):
                    break

                deltaBeats -= beatsLeft
                beatsSinceBarLine = 0
                currTime += secondsLeft
                measureStarts.append(currTime)
                measureCount += 1

                #check if time sig has been adjusted and adjust accordingly
                if (currTimeSigIndex + 1 < len(result["TimeSig"]) and currTime + 0.01 >= result["TimeSig"][currTimeSigIndex + 1]["start"]):
                    currTimeSigIndex += 1
                    currNumerator = result["TimeSig"][currTimeSigIndex]["numerator"]
                    currDenom = result["TimeSig"][currTimeSigIndex]["denominator"]

        currTempo = tempoChange["tempo"]

    # finish last bar
    beatsLeft = currNumerator - beatsSinceBarLine
    secondsLeft = beatsLeft * (60 / currTempo) # calculate remaining time in measure
    measureStarts.append(currTime + secondsLeft)
    measureCount += 1

    print("created " + str(measureCount) + " measure starts...")

    # insert measure starts in JSON
    result["MeasureStart"] = measureStarts



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
            fullName = None
            activeNotes = {}

        # tracks total elapsed time
        timeMatch = re.search(r'time=(\d+)', line)
        deltaTime = int(timeMatch.group(1)) if timeMatch else 0
        totalTime += deltaTime

        # Finds the name of the current track
        if "ticks_per_beat" in line:
            global TICKS_PER_BEAT
            ticksperbeatmatch = re.search(r"ticks_per_beat=(\d+)", line)
            TICKS_PER_BEAT = int(ticksperbeatmatch.group(1))

        # Finds the name of the current track
        if "track_name" in line:
            nameMatch = re.search(r"name='([^']+)'", line)
            if nameMatch:
                currInstrument = nameMatch.group(1)

        # detects channel for notes
        if "channel=" in line and currInstrument:
            channelMatch = re.search(r'channel=(\d+)', line)
            if channelMatch:
                channel = channelMatch.group(1)
                fullName = f"{currInstrument}, {channel}"

        # Detects start of a new note and adds it to a list until
        # its corresponding note_off is found
        if "note_on" in line and "velocity=0" not in line:
            totalNotes += 1
            noteMatch = re.search(r'note=(\d+)', line)
            if noteMatch and currInstrument:
                noteVal = int(noteMatch.group(1))

                if noteVal < 21:
                    continue

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

                    output[fullName].append({
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
    output["MeasureStart"].append([])

    return dict(output)

def createTxt(filepath):
    mid = MidiFile(filename=filepath, clip=True)
    with open("trackOutput.txt", "w") as f:
        f.write(str(mid))

def main():
    if len(sys.argv) != 3:
        print("Usage: python parser.py <input.mid> <output.json>")
        sys.exit(1)

    midiIn = sys.argv[1]
    outputFile = sys.argv[2]
    createTxt(midiIn)
    result = parseMidi("trackOutput.txt")

    fixNoteTimeStamps(result)
    fixDuration(result)
    fixTimeSig(result)
    fixTempoTime(result)

    convertTempo(result)
    addMeasureNum(result)

    with open(outputFile, 'w') as f:
        json.dump(result, f, indent=4)

    print(f"Output written to {outputFile}")

if __name__ == "__main__":
    main()