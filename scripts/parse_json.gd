extends Node

@onready var renderer = $NoteRenderer

func _ready():
	var data = load_json("res://data/output.json")
	if data:
		renderer.setup(data)
	
# loads json and gives an error if it fails to open or parse
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
