extends Control

"""
This class will be used to generate notes based on the json data. It will call
upon the NotePool to instantiate notes.
"""

const MEASURELEN = 3.69230769231
var MEASURE_STARTS = []
# const MEASURE_STARTS = [0, 3.69, 7.38, 11.07]
const TRACK_NAME = "Flute"
const NOTERANGE = 90

@export var note_pool : Node

@onready var currentmeasure = -1 # represents the index of the current measure
@onready var currentnote = 0 # represents the index of the next note to be generated

var loadedmidi

func _ready()->void:
	for x in range(8):
		MEASURE_STARTS.append(x * MEASURELEN)
	loadedmidi = load_json("res://parser/output.json")
	
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
	if currentmeasure + 2 >= MEASURE_STARTS.size():
		return
	
	# check if the current frame has moved past the next measure (and generate the notes if so)
	if current_timestamp > MEASURE_STARTS[currentmeasure + 1]:
		# the current timestamp exceeds the current measure's end. Generate new notes and increment
		# the current measure!
		currentmeasure += 1
		
		# generate all notes that are in this measure
		var measurestart = MEASURE_STARTS[currentmeasure]
		var measureend = MEASURE_STARTS[currentmeasure + 1]
		var measurelen = measureend - measurestart
		
		var notescreated = 0
		
		while currentnote < loadedmidi[TRACK_NAME].size() and loadedmidi[TRACK_NAME][currentnote]["start"] < measureend: # index OoB error possible on notes array
			var notestart = loadedmidi[TRACK_NAME][currentnote]["start"]
			var notelen = loadedmidi[TRACK_NAME][currentnote]["duration"]
			var noteend = loadedmidi[TRACK_NAME][currentnote]["end"]
			var notepitch = loadedmidi[TRACK_NAME][currentnote]["midiValue"]
			
			# skip notes that are "control" notes
			if notepitch < 21: # TEMPORARY FIX - USE THE ACTUAL PITCH RANGE WHEN POSSIBLE
				currentnote += 1
				continue
			
			var newnote = note_pool.allocate_note()
			
			# calculate the values in visual space (relative to the note pool view)
			var note_x = lerp(0, note_pool.VIEW_WIDTH, (notestart - measurestart) / measurelen)
			var note_y =  ((111 - notepitch) / NOTERANGE) * note_pool.VIEW_HEIGHT
			var note_visual_len = (notelen / measurelen) * note_pool.VIEW_WIDTH
			
			# position the note in viewport space
			newnote.position = Vector2(note_x, note_y)
			newnote.target_width = note_visual_len
			newnote.note_rect.size.x = 0
			newnote.visible = true
			
			# set up the animation params of the new note
			newnote.starttime = notestart
			newnote.endtime = noteend
			newnote.deathtime = measureend
			
			# set up the newnote as a listener for the conductor
			newnote.connect_to_conductor()
			
			notescreated += 1
			
			
			currentnote += 1
		print("created " + str(notescreated) + " notes!")
