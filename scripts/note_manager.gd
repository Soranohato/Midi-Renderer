extends Control

"""
This class will be used to generate notes based on the json data. It will call
upon the NotePool to instantiate notes.
"""
const METADATA_TRACKS = ["TimeSig", "Tempo", "TotalNotes", "NoteRange", "MeasureStart"]
var TRACK_NAMES = []
const DEFAULT_COLOR = Color("6ed47c")

@export var note_pool : Node
@export var track_colors : Array[Color]
@export var tracks_to_use : Array[String]
@export var transposes : Array[int]

@onready var currentmeasure = 0 # represents the index of the current measure
@onready var currentnotes = [] # represents the index of the next note to be generated
@onready var carryovernotes = [] # array of arrays that represents the carry-over notes from the previous measure

@onready var conductor = get_tree().get_nodes_in_group('conductor')[0]

signal send_measure_number(currMeasure, totalMeasures) # for the measure counter info
signal send_time_signature(numerator, denominator) # for time sig display
signal send_tempo(currTempo) # for tempo display

var loadedmidi
var noterange
var totalNotes
var totalMeasures
var currTimeSig = 0
var numerator : int
var denominator : int
var currTempoInd = 0
var currTempo : int
var songLen

var pitchoffset # in order to make room for the upwards transpositions, we will be artificially pushing all the other notes down.

func _ready()->void:
	loadedmidi = load_json("res://parser/compass.json")
	
	# if user has not specified tracks to use, do all of them
	if tracks_to_use.is_empty():
		for track in loadedmidi.keys():
			if track in METADATA_TRACKS:
				continue
			
			TRACK_NAMES.append(track)
	else:
		TRACK_NAMES = tracks_to_use
		
	# if transpose array is wrong length, fix it
	while transposes.size() < TRACK_NAMES.size():
		transposes.append(0)
	
	# retrieve noterange from midi file
	noterange = loadedmidi["NoteRange"][0]["high"] - loadedmidi["NoteRange"][0]["low"]
	
	# adjust noterange based on transposes
	var mintranspose = transposes[0] # minimum value in transpose array
	var maxtranspose = transposes[0] # maximum value in transpose array
	for x in transposes:
		if x < mintranspose:
			mintranspose = x
		if x > maxtranspose:
			maxtranspose = x
	
	noterange += abs(mintranspose) + abs(maxtranspose)
	pitchoffset = maxtranspose
	
		
	
	# initialize the note index of each track
	# initialize the carry-over arrays of each track
	for x in TRACK_NAMES:
		currentnotes.append(0)
		carryovernotes.append([])
	
	noterange = loadedmidi["NoteRange"][0]["high"] - loadedmidi["NoteRange"][0]["low"]
	totalNotes = loadedmidi["TotalNotes"][0]["TotalNotes"]
	conductor.set_total_notes(totalNotes)
	totalMeasures = loadedmidi["MeasureStart"].size()
	numerator = loadedmidi["TimeSig"][0]["numerator"]
	denominator = loadedmidi["TimeSig"][0]["denominator"]
	currTempo = loadedmidi["Tempo"][0]["tempo"]
	
	# extrapolates the total measure count
	songLen = conductor.get_node("song").stream.get_length()
	var measures_size = loadedmidi["MeasureStart"].size()
	var measurestart = loadedmidi["MeasureStart"][measures_size - 2]
	var measureend = loadedmidi["MeasureStart"][measures_size - 1]
	totalMeasures += int((songLen - measureend) / (measureend - measurestart))
	
	conductor.begin_song()
	
func load_json(path: String) -> Dictionary:
	var file = FileAccess.open(path, FileAccess.READ)
	if not file:
		push_error("Failed to open JSON")
		return {}
	
	var content = file.get_as_text()
	var result = JSON.parse_string(content)
	if result is Dictionary:
		return result
	else:
		push_error("Failed to parse JSON")
		return {}


func _on_conductor_update_song_timestamp(current_timestamp: Variant) -> void:
	# (TEMPORARY FIX: DO NOT GENERATE NOTES PAST THE PLACEHOLDER MEASURE ENDS)
	var measurestart
	var measureend
	var measurelen
	if currentmeasure + 2 < loadedmidi["MeasureStart"].size():
		measurestart = loadedmidi["MeasureStart"][currentmeasure]
		measureend = loadedmidi["MeasureStart"][currentmeasure + 1]
		measurelen = measureend - measurestart
	else:
		# extrapolate the measure start and end based on the last 2 values
		# of the measures array
		var measures_size = loadedmidi["MeasureStart"].size()
		measurestart = loadedmidi["MeasureStart"][measures_size - 2]
		measureend = loadedmidi["MeasureStart"][measures_size - 1]
		measurelen = measureend - measurestart
		
		var measuresover = currentmeasure - (measures_size - 1)
		measurestart += measurelen * measuresover
		measureend += measurelen * measuresover
	
	# check if the current frame has moved past the next measure (and generate the notes if so)
	if current_timestamp > measurestart:
		# the current timestamp exceeds the current measure's end. Generate new notes and increment
		# the current measure!
		currentmeasure += 1
		
		# emit signal to measure counter
		send_measure_number.emit(currentmeasure, totalMeasures)
		
		# generate all notes that are in this measure
		for track_index in range(TRACK_NAMES.size()):
			generate_notes(measurestart, measureend, track_index)
			
	# check if current time signature has advanced or not
	if current_timestamp > loadedmidi["TimeSig"][currTimeSig]["start"]:
		send_time_signature.emit(numerator, denominator)
		# get next numerator and denominator and advance index
		if currTimeSig + 1 < loadedmidi["TimeSig"].size():
			currTimeSig += 1
			numerator = loadedmidi["TimeSig"][currTimeSig]["numerator"]
			denominator = loadedmidi["TimeSig"][currTimeSig]["denominator"]
			
	# check if tempo has changed
	if current_timestamp > loadedmidi["Tempo"][currTempoInd]["start"]:
		send_tempo.emit(currTempo)
		#get next tempo
		if currTempoInd + 1 < loadedmidi["Tempo"].size():
			currTempoInd += 1
			currTempo = loadedmidi["Tempo"][currTempoInd]["tempo"]


func initialize_note(track_index, measurestart, measureend, noteinfo, notecolor, particleeffects) -> bool:
	var track_name = TRACK_NAMES[track_index]
	var notestart = noteinfo["start"]
	var notelen = noteinfo["duration"]
	var noteend = noteinfo["end"]
	var notepitch = noteinfo["midiValue"]
	
	var measurelen = measureend - measurestart
	
	# skip notes that are "control" notes
	if notepitch < loadedmidi["NoteRange"][0]['low']:
		return false
		
	# skip notes that have a start time less than 0 seconds
	if notestart < 0:
		return false
		
	# if the note extends past the measure
	if noteend > measureend:
		# create a "fake" note that starts at the next measure and extends to the same note end
		var myfakenote = {}
		myfakenote["start"] = measureend
		myfakenote["end"] = noteend
		myfakenote["duration"] = noteend - measureend
		myfakenote["midiValue"] = notepitch
		
		carryovernotes[track_index].append(myfakenote)
		
		noteend = measureend
		notelen = noteend - notestart
	
	var newnote = note_pool.allocate_note()
	
	# adjust pitch based on transpositions
	var adjusted_notepitch = (notepitch + transposes[track_index]) - pitchoffset
	
	# calculate the values in visual space (relative to the note pool view)
	var note_x = lerp(0, note_pool.VIEW_WIDTH, (notestart - measurestart) / measurelen)
	var note_y =  ((loadedmidi["NoteRange"][0]['high'] - adjusted_notepitch) / noterange) * note_pool.VIEW_HEIGHT
	var note_visual_len = (notelen / measurelen) * note_pool.VIEW_WIDTH
	
	# position the note in viewport space
	newnote.position = Vector2(note_x, note_y)
	newnote.target_width = note_visual_len - 5
	newnote.note_rect.size.x = 0
	newnote.note_rect.visible = true
	newnote.z_index = track_index
	
	# set up the animation params of the new note
	newnote.starttime = notestart
	newnote.endtime = noteend
	newnote.deathtime = measureend
	newnote.fired = not particleeffects
	newnote.note_rect.color = notecolor
	
	# set up the newnote as a listener for the conductor
	newnote.connect_to_conductor()
	
	return true

# Generate all the notes for a measure given the track name and the start and end times of the measure
func generate_notes(measurestart, measureend, track_index):
	var measurelen = measureend - measurestart
	
	var track_name = TRACK_NAMES[track_index]
	var currentnote = currentnotes[track_index]
	
	var notecolor = DEFAULT_COLOR
	
	if track_colors.size() != 0:
		notecolor = track_colors[track_index % track_colors.size()]
		
	# initialize all the carry-over notes from the previous measure
	var prevcarriedover = carryovernotes[track_index].duplicate(true)
	carryovernotes[track_index].clear() # clear the array so that notes can be carried over again
	
	for note in prevcarriedover:
		initialize_note(track_index, measurestart, measureend, note, notecolor, false)
	
	
	# initialize all the new notes of the new measure
	while currentnote < loadedmidi[track_name].size() and loadedmidi[track_name][currentnote]["start"] < measureend - 0.055:
		# print("generated note number " + str(currentnote))
		
		var noteinfo = loadedmidi[track_name][currentnote]
		initialize_note(track_index, measurestart, measureend, noteinfo, notecolor, true)
		
		currentnote += 1
	
	currentnotes[track_index] = currentnote
