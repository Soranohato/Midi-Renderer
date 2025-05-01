extends Node

# @export var filename()

func _ready() -> void:
	var file = FileAccess.open("res://parser/output.json", FileAccess.READ)
	var parsed_data = JSON.parse_string(file.get_as_text())
	
	print(parsed_data["TimeSig"])
	# print(parsed_data)
