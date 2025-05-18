extends RichTextLabel


func _on_note_manager_send_tempo(currTempo: Variant) -> void:
	text = str(currTempo) + " BPM"
