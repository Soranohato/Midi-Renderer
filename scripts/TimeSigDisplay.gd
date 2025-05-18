extends RichTextLabel


func _on_note_manager_send_time_signature(numerator: Variant, denominator: Variant) -> void:
	text = str(numerator) + "/" + str(denominator)
