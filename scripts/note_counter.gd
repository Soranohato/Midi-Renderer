extends RichTextLabel

func _on_conductor_update_note_count(note_count: Variant, total_notes: Variant) -> void:
	text = str(note_count) + " / " + str(total_notes) + " Notes Played"
