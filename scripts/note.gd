extends Control

const OUT_ANIM_TIME = 0.2

# keep reference to conductor node
@onready var conductor = get_tree().get_nodes_in_group('conductor')[0]

@onready var note_rect = $ColorRect
@onready var particle = $particle
@onready var circle = $circle

var fired = false

@onready var is_alloc = false
var index : int

# this is the width that the note animates towards
var target_width : float
var starttime # time at which the note displays
var endtime # time at which the note reaches full length
var deathtime # time at which the note should disappear from the screen (usually at the start of next measure)

func _ready():
	note_rect.visible = false

func _on_timestamp_update(timestamp : float) -> void:
	if not note_rect.visible:
		return
	
	var t = (timestamp - starttime) / (endtime - starttime)
	t = clampf(t,0.0,1.0)
	
	# before death time, slide the note away towards the right
	if timestamp > deathtime:
		deactivate()
	# If there is enough time before death time, slide the note away towards the right
	elif timestamp > deathtime - OUT_ANIM_TIME and timestamp < deathtime:
		var death_t = 1 - ((deathtime - timestamp) / OUT_ANIM_TIME)
		
		note_rect.position.x = 0
		note_rect.size = Vector2(target_width, note_rect.size.y)
		set_note_size_right(custom_interpolate(target_width, 0, death_t, 5))
	else: 
		var lerped_size = custom_interpolate(0.0, target_width, t, 0.33)
		
		note_rect.position.x = 0
		note_rect.size = Vector2(lerped_size, note_rect.size.y)
	
	# particles emit once, also don't emit particles for short notes
	if target_width > 35:
		if timestamp < starttime:
			fired = false
		elif not fired:
			particle.emitting = true
			particle.restart()
			
			circle.emitting = true
			circle.restart()
			
			fired = true


func custom_interpolate(a,b,t,f)->float:
	return lerp(float(a), float(b), pow(t, f))
	
# set the size but keep the right edge where it is
func set_note_size_right(newsize: float) -> void:
	var clampedsize = max(newsize, 0)
	var rightedge = note_rect.position.x + note_rect.size.x
	note_rect.size = Vector2(clampedsize, note_rect.size.y)
	
	note_rect.position.x = rightedge - clampedsize
	

# de-allocate the note from the pool and also prevent it from receiving conductor updates
func deactivate():
	# attempt to disconnect this note from the conductor (putting the note to sleep until it is allocated again)
	var conductor_signal : Signal = conductor.update_song_timestamp
	conductor_signal.disconnect(_on_timestamp_update)
	
	note_rect.visible = false
	get_parent().free_note(index)

func connect_to_conductor():
	var conductor_signal : Signal = conductor.update_song_timestamp
	conductor_signal.connect(_on_timestamp_update)
