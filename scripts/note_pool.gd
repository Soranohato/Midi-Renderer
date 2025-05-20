extends Control

const NOTES_TO_START = 30
const NoteScene = preload("res://Note.tscn")

"""
This class is used to generate note objects without constantly wasting resources
by deleting and recreating the same note object. Instead, we will "deactivate"
them without fully deleting them to allow the reuse of the allocated memory.
"""

@onready var objs = []
@onready var conductor = get_tree().get_nodes_in_group('conductor')[0]


func _ready() -> void:
	# instantiate all of those starting notes before the song really starts
	for x in range(NOTES_TO_START):
		var scene = NoteScene.instantiate()
		add_child(scene)
		objs.append(scene)
		scene.index = x
		
		
	conductor.begin_song()

func allocate_note() -> Node:
	# Iterate through the pool and attempt to locate an unused note
	var i = 0
	while i < objs.size():
		if not objs[i].is_alloc:
			break;
		i += 1
	
	# no node was found
	if i >= objs.size():
		# create new node (no space to realloc)
		var scene = NoteScene.instantiate()
		scene.index = objs.size()
		
		add_child(scene)
		objs.append(scene)
		objs[i].is_alloc = true
		print("total alloc %d" % objs.size())
		return scene
		
	else:
		# located node, realloc
		objs[i].is_alloc = true
		return objs[i]
		
func free_note(index) -> void:
	objs[index].is_alloc = false
