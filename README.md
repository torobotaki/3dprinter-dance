# 3dprinter-dance
Experiments with making a 3d printer (_creality ender_) "dance" via gcode and python. 

In the simplest version, the python script listens to the microphone for sound and tries and translate sound into gcode movements. 

## Disclaimer
**MESS**: The code here is messy, it was produced very fast during a [workshop](https://www.instagram.com/p/DFBHI3SumZL/), and quite honestly I've been procrastinating cleaning it up :D

**BUGS**: There is at least one known (logic) bug. The printer gets stuck high, and you need to play it *a lot* of F notes to get it to come down. 

Maybe one day I will clean this up, but until then, enjoy.



## Example of use
Launch it using ```python3```. You can then choose 
* if you want it to connect ```live``` (via serial/USB) to a printer able to receive GCODE commands, or if you want to write the gcode commands to a ```file``` that you can later give to a printer (by using a card or othewrise), or maybe a visualization/simulation tool 
* if you want to listen to the ```mic```, feed it an _audio_ ```file``` (wav), or even the system output (_Attention: this might not work the way you think it will_).
* the input/output file names, accordingly.

This will look a bit like this, and there is a lot of _debug_ output, so that you see what is happening. 

	python ./choreography-mic.py
	Enter mode ('live' for printer, 'file' for G-code file): file
	Select audio source ('mic' for microphone, 'file' for audio file, 'system' for system output): mic
	2025-05-18 12:19:26,924 - INFO - Starting printer initialization.
	Enter G-code output file path (e.g., output.gcode): random-stuff-test.gcode
	2025-05-18 12:19:40,860 - DEBUG - Writing: G21
	2025-05-18 12:19:40,860 - DEBUG - Writing: G90
	2025-05-18 12:19:40,860 - DEBUG - Writing: G28
	2025-05-18 12:19:40,860 - INFO - Initial position set to: X=10.50, Y=10.50, Z=10.00
	2025-05-18 12:19:40,860 - DEBUG - Writing: G1 X105.00 Y105.00 Z100.00 F500
	2025-05-18 12:19:41,866 - INFO - Detected note: ('F', 'natural'), Frequency=172.27 Hz, RMS=0.00
	2025-05-18 12:19:41,866 - INFO - Movement: dx=0.00 cm, dy=0.00 cm, dz=-1.50 cm.
	G1 X105.00 Y105.00 Z100.00 F1500.0
	New Position: X=10.50, Y=10.50, Z=10.00
	2025-05-18 12:19:42,237 - INFO - Detected note: ('F', 'natural'), Frequency=172.27 Hz, RMS=0.00
	...
 

This debug will also be *appended* to a file (printer_debug.log). 


## List of files
* ```choreography-mic.py``` is the sole survivor of the attempts as the final and most complete script. 
* in ```gcode-files``` there are some example gcode files produced. Their name is indicative of the intention :)
* ```notes.txt``` contains some documentation and explanations concerning mapping of frequencies to notes. You need to edit the actual python script to change the mapping, but I used this to not lose track and thought it might be helpful to share it ```¯\_(ツ)_/¯```.
