# 3dprinter-dance
Experiments with making a 3d printer (_creality ender_) "dance" via gcode and python. 
This project allows you to create a choreography for a 3D printer based on audio input. The printer moves in response to detected musical notes and audio frequencies.
In the simplest version, the python script listens to the microphone for sound and tries and translate sound into gcode movements. 


## Table of Contents
- [Disclaimer](#disclaimer)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Example of Use](#example-of-use)
- [How it Works](#how-it-works)


    
## Disclaimer
1.**Sending arbitrary code to your 3d printer can be dangerous**. Be sure to match your printer's paramaters to avoid breaking things. The main thing that can break, is pushing to hard on the plate. The rest should be safe-r. Try something like [Cura](https://ultimaker.com/software/ultimaker-cura/) to simulate and visualize before sending it to your printer. 

2.**This is messy.** The code here was produced very fast during a [workshop](https://www.instagram.com/p/DFBHI3SumZL/), and quite honestly I've been procrastinating cleaning it up :D

3.**This is very lightly tested.**: There is at least one known (logic) bug. The printer gets stuck high, and you need to play it *a lot* of F notes to get it to come down. 

Maybe one day I (or you) will clean this up and/or improve it, but until then, enjoy it **_as is_**  ```¯\_(ツ)_/¯```.


## Requirements
* Python 3.x
* Libraries: ```pyserial```, ```numpy```, ```sounddevice```, ```scipy```, ```pydub```
* FFmpeg (for handling MP3 files)


## Installation

1. Clone the repository:

```
git clone https://github.com/torobotaki/3dprinter-dance.git
cd 3dprinter-dance
```

2. Install the required libraries:

```
pip install pyserial numpy sounddevice scipy pydub
```

3. Install FFmpeg:

* On macOS: ```brew install ffmpeg ```
* On Windows: ```Download from FFmpeg website ```
* On Linux (Debian/Ubuntu): ```sudo apt-get install ffmpeg ```

## Configuration

* Serial Port: Update the ```SERIAL_PORT``` variable in the script to match your printer's serial port.
* Parameters: Adjust parameters like  the *important* ```MIN_Z```, and others like ```PLATE_CENTER```, ```LAYER_HEIGHT```, etc., to match your setup. **Attention!** Don't break your 3d printer by sending wrong parameters and have its arm break the plate, check and adjust ```MIN_Z```.


## Example of use
Launch it using ```python3```. You can then choose 
* if you want it to connect ```live``` (via serial/USB) to a printer able to receive GCODE commands, or if you want to write the gcode commands to a ```file``` that you can later give to a printer (by using a card or othewrise), or maybe a visualization/simulation tool 
* if you want to listen to the ```mic```, feed it an _audio_ ```file``` (wav or mp3), or even the system output (_Attention: this might not work the way you think it will_).
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


## How it works

The sound, whatever its chosen source, is translated into frequencies and loudness (RMS). 

#### Tone -> Direction ####
The frequencies, are mapped to notes and then the different notes are mapped to movements as follows: 

- A moves x right
- B moves x left
- C moves y right
- D moves y left
- E moves z up
- F moves z down
- G changes x,y directions randomly

In addition to notes, the accidental also influences movement as follows: 
- Sharp changes x direction randomly 
- Flat changes y direction randomly 

Feel free to play around with this by editing the ```MOVEMENTS``` mapping in the main script. 

#### Loudness -> speed ####
Loudness (RMS) is encoded as follows: 

- silent (0) stops movement
- loudness translates into speed, louder is faster


