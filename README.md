# Brush SFX
This plugin adds pencil and pen noise sound effect when you draw 


## Installation 

1.  Click the &rsquo;<> Code&rsquo; drop-down near the top of the github repository
    page and select &rsquo;Download ZIP&rsquo;
2.  In the Krita menu bar go to `Tools > Scripts > Import Python Plugin from File`&#x2026;
3.  Select the downloaded zip file and select &rsquo;Yes&rsquo; when prompted to
    enable the plugin.
4.  Restart Krita.

## Usage

On krita's menu bar go to `Settings > Dockers > Brush SFX`.
The SFX option enables and disables the sound effects and it will be On by default.
The Sound Choice option lets you choose which sound you want for your brush. Currently
there are 2 options: pen-1(default) and pencil-1. When you press your pen or your cursor
on the canvas widget it should play the chosen sound.

## To do

- Persist changes in the plugin's options
- Move the plugin's options UI from a docker to it's own window
- Fine tune the pencil's noises

## Known Issues

- If you open a second krita window and change the options from the second window it will affect all windows. 
Dockers are intended to have oan instance for every krita window, so it is not ideal for global options.


