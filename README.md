# Brush SFX
This plugin adds sound effects when you draw on canvas. Choose from 6 different sound effects and 
assing one for each of your brushes. This plugin comes with sounds pre-assigned for every default brush on krita 


## Installation 

1.  On the top of this github repository page, click the &rsquo;<> Code&rsquo; drop-down select &rsquo;Download ZIP&rsquo;
2.  In the Krita's menu bar go to `Tools > Scripts > Import Python Plugin from File`&#x2026;
3.  Select the downloaded zip file and select &rsquo;Yes&rsquo; when prompted to
    enable the plugin.
4.  Restart Krita.

### Linux
You will also need to install the portaudio library

### On Ubuntu
`sudo apt install portaudio19-dev`

### On Arch
`sudo pacman -S portaudio`

## Configuration

On krita's menu bar go to `Tools > Scripts > Brush SFX` or press `F8`.
The `Sound Effects` option enables and disables the sound effects.
The `Master Volume` option controls the global volume of the sound effects. The `Brush sound` 
and `Sound for eraser` and `Eraser sound` options control the sound effects that will play
when using your brush on canvas. The `Use different sound on current preset` lets you assing
a different configuration to your current brush preset.
Preset configurations are attached to the brush's name

## Sound Effects

When you press your pen or your cursor on the canvas widget it should play the chosen sound.
These are your choices for sound effects:

0. [no sound]
1. eraser
2. pencil
3. pen
4. paintbrush
5. airbrush
6. spray can




