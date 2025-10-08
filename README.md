# Brush SFX
This plugin adds sound effects when you draw. Choose from 6 different sounds and assing one for
each of your brushes. This plugin comes with sounds pre-assigneds for every default brush on krita 


## Installation 

1.  Click the &rsquo;<> Code&rsquo; drop-down near the top of the github repository
    page and select &rsquo;Download ZIP&rsquo;
2.  In the Krita menu bar go to `Tools > Scripts > Import Python Plugin from File`&#x2026;
3.  Select the downloaded zip file and select &rsquo;Yes&rsquo; when prompted to
    enable the plugin.
4.  Restart Krita.

## Usage

On krita's menu bar go to `Tools > Scripts > Brush SFX`.
The `SFX` option enables and disables the sound effects and it will be On by default.
The `Volume` option lets you choose the general volume of the sound effect. The `Brush sound` 
and `Eraser sound` option lets you choose which sound you want for your brush and eraser. 
If the `Sound for eraser` option is marked, the plugin will use the selected eraser sound when
using the brush's eraser mode, if it's not marked it will play no sound when using the 
eraser mode. The `Use different sound on current preset` lets you assing a configuration 
different from the general configuration to your current brush preset. The `Volume` of 
the current preset only changes the volume relatively to the general volume, that is,
setting it higher than the general volume will not make it play louder than setting
the general volume to max

## Sound Effects

When you press your pen or your cursor on the canvas widget it should play the chosen sound.
Currently there are 6 choices of sound effects:

0. [no sound] (doesn't count) 
1. eraser
2. pencil
3. pen
4. paintbrush
5. airbrush
6. spray can




