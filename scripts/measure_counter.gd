extends RichTextLabel


func _on_note_manager_send_measure_number(currMeasure: Variant, totalMeasures: Variant) -> void:
	text = str(currMeasure) + " / " + str(totalMeasures) + " Measures Played"
