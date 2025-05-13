extends Control

# keep reference to conductor node
@onready var conductor = get_tree().get_nodes_in_group('conductor')[0]

@onready var note_rect = $ColorRect

@onready var is_alloc = false
var index : int

# this is the width that the note animates towards
var target_width : float
var starttime # time at which the note displays
var endtime # time at which the note reaches full length
var deathtime # time at which the note should disappear from the screen (usually at the start of next measure)

func _ready():
	visible = false

func _on_timestamp_update(timestamp : float) -> void:
	var t = (timestamp - starttime) / (endtime - starttime)
	t = clampf(t,0.0,1.0)
	
	var lerped_size = custom_interpolate(0.0, target_width, t)
	
	note_rect.size = Vector2(lerped_size, note_rect.size.y)
	
	if timestamp > deathtime:
		deactivate()
		
func custom_interpolate(a,b,t)->float:
	var value = lerp(a,b,pow(t, 0.33))
	
	return clampf(value, a, b)

# de-allocate the note from the pool and also prevent it from receiving conductor updates
func deactivate():
	visible = false
	get_parent().free_note(index)
	
	# attempt to disconnect this note from the conductor (putting the note to sleep until it is allocated again)
	var conductor_signal : Signal = conductor.update_song_timestamp
	if conductor_signal.is_connected(_on_timestamp_update):
		conductor_signal.disconnect(_on_timestamp_update)

func connect_to_conductor():
	var conductor_signal : Signal = conductor.update_song_timestamp
	conductor_signal.connect(_on_timestamp_update)
