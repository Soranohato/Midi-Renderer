extends Node

@onready var audionode : AudioStreamPlayer = $song

signal update_song_timestamp(current_timestamp)
signal update_note_count(note_count, total_notes)

var notes_counter : int = 0
var total_notes : int = 0

func _ready() -> void:
	begin_song()

func begin_song()->void:
	
	# begin playback of the song
	audionode.play()


func _process(delta : float):
	# emit a signal that sends out the current playback position of the song
	
	# since audio is chunked, we need to add the time since the last mix to avoid jitter
	var current_time = audionode.get_playback_position() + AudioServer.get_time_since_last_mix()
	emit_signal("update_song_timestamp", current_time)


# THIS IS USED FOR DEBUGGING PURPOSES - DELETE LATER
func _input(event):
	if event is InputEventKey:
		if event.pressed and event.keycode == KEY_SPACE:
			print('seek!')
			audionode.seek(161.0)
			var notemanager = get_parent().get_node("NoteManager")
			
			notemanager.currentmeasure = 50
			notemanager.currentnote = notemanager.loadedmidi["Flute"].size() - 10 - 1
			
func note_played():
	notes_counter += 1
	update_note_count.emit(notes_counter, total_notes)
	
func set_total_notes(totalNotes):
	total_notes = totalNotes
	update_note_count.emit(notes_counter, total_notes)
