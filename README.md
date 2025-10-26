# About the Project
***

This is an open source renderer that is a two step process for turning your midi file into a measure by measure visualization. 
This was heavily inspired by Kashiwade's measure by measure visualization with a few changes and personal improvements, please check out their music and support them!
Note: You will need some knowledge of how to use Godot in order to use this renderer.
Note: This project was made on Godot 4.4 and has not been fully tested in version 4.5, please mark an issue so it can be fixed if a bug is found

# Getting Started
***

1. The first step to using this is to convert your midi to a readable json file. Start by navigating to the folder with parser.py in a cmd window and executing with the following syntax: `python parser.py <input.mid> <output.json>`
    1. I recommend leaving the output in the parser folder so you have to change less later
3. Open up the project in Godot (both Steam or official release works)
    1. To import a project click the import button then navigate to the folder with the file `project.godot`
4. Set the json file for the project
    1. We must set the json file we made earlier in step one. This is found in the script "note_manager.gd" on line 40. Change the variable path from "res://parser/compass.json" to the path of your json.
5. Set the audio file in the project
    1. We must change the audio playing from the current default to what you want to hear. This can be done by clicking the "song" node and changing the Stream under AudioStreamPlayer on the right by dragging and dropping your audio file onto Stream.
6. Change the Title and Artist lables
    1. To change what displays for title and artist make sure "test-scene" is still open in the tab view at the top then click on "2D" to change the view. Then just click the text in the upper left and on the right you will see a spot to change your text field.
8. Run the project
    1. That is all you need to do to get the basic rendering done. It is up to you how you record the rendering since there is not a great one built into Godot as of now. Further customization options will be discussed in the next section.

# Customization
***

Right now there are a few options for customizing how the renderer appears. At present you can change the note colors, the position of each track, the background color, if you want note effects on/off, and which tracks are rendered.

### Note Color
To access the current note colors click the NoteManager node and on the right you will see an arry of "Track Colors". This array MUST have at least one color present in it and can be as long as you want (although no color past your number of tracks in your midi will be used)
To set which color will be assigned to each instrument simply go to the array below labeled "Tracks to Use" and fill out the array with each instrument found in the json file. The first color in the color list will go to the first instrument in the to use list.
If you have less colors than instruments the color list will loop back to the first color and iterate through until all instruments are accounted for.

### Track Postition
If you have an instrument that you would like to have its notes appear in a spot that does not correspond to its true midi position you can use this array. You can find it again by clicking NoteManager and scrolling down to transposes. This array behaves just like note color where each array element corresponds to the same number in "Tracks to Use". The number you set in the array is the number of semitones up or down you want to set the track to be moved. Positive numbers go up, negative numbers to go down.

### Background Color
To change the background color simply click the ColorRect node and then where you see color change it to the color you want.

### Note effects
This one unfortunately is a little trickier to turn off at the moment but it can be done. Head to note.gd and find lines 50-62. Comment out all of these lines of code and the particle effects for notes will be turned off. If you want to turn them back on just reverse this process. This will be streamlined in the future.

### Rendered Tracks
If you wish to only render certain tracks of your midi file that can also be done. By default all tracks are rendered. To render specific tracks click the NoteManager node and find the array "Tracks to Use". Here just add in the names of each track you wish to use and that is it.

# Future Features
***

* Toggleable note effects
* Easy conversion to verticle screen
* Fix note overhang on left side of screen
* Fix minor transpose bug

# Contributing
***

If you wish to contribute this project is open to the public, just make a pull request and my friend and I will review the code!

# Contributors
***

Soranohato, Rhishit Khare

