extends RichTextLabel

func _on_conductor_update_song_timestamp(current_timestamp: Variant) -> void:
	text = "%.2f" % current_timestamp
