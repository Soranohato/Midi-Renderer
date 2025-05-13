extends Node

@onready var audionode : AudioStreamPlayer = $song

signal update_song_timestamp(current_timestamp)

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
