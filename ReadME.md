<h1 align = center> Welcome to Boat Man Shooters 👋</h1>
<p align="center">
  <img height="50%" width="50%" src="/Logos/logo.png">
</p>

## Table of Contents

1. [Overview](#overview)  
   1.1. [Features](#features)  
2. [Mechanics](#mechanics)  
   2.1. [File Structure](#file_structure)  
   2.2. [Logic](#logic)  
   2.3. [Code](#code)  
3. [Usage](#usage)  
   3.1. [Installation of Dependencies](#installation_of_dependencies)  
   3.2. [How to Run](#how_to_run)  
   3.3. [How to Play](#how_to_play)
4. [Legal Stuff](#legal_stuff)
   
# Overview <a name="overview"></a>

This is a online multiple player game where the intention is to shoot other boats and be the person with the most *(kills/time alive?)*. It is a constant lobby in which there can be a winner at any given time, given who has the most *(kills/time alive?)*. 

## Features <a name="features"></a>

- Online multiplayer game
- Account system
- Fluid UI interface/animations
- Sounds and background music
- Both keyboard and controller input

# Mechanics <a name="mechanics"></a>

## File Structure <a name="file_structure"></a>

The game has the following structure:  
├── .github &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;***Configuration files for GitHub***  
├── Assets &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;***Contains the font, music, and button sounds***  
├── Game_Code &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;***Contains all the game code***  
├── Graphics &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;***Contains Map Items, Sprites, Butons, and Menus***  
├── Logos &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; ***All the logos and icons for our project***  
├── .gitignore &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; ***Tells GitHub to ignore specific files when commiting***  
├── requirements.txt &nbsp; &nbsp; &nbsp; ***Tells GitHub Dependabot what dependencies are needed to update***  
├── LICENSE &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;***The license for this project.***  
└── ReadME.md &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; ***This documentation file you are reading right now.***  

## Logic <a name="logic"></a>
<img src="Documentation/Game Logic Flowchart.png" alt="Game Logic Flowchart">

## Code <a name="code"></a>

Explain flow between files - tell reader that explainations of code can be found in deep dive.

# Usage <a name="usage"></a>

## Installation of Dependencies <a name="installation_of_dependencies">

This project uses the dependencies `pygame-ce`, `moderngl`, `numpy`, and `supabase`, which are not built in to the Python system. To install these dependencies, you will have to use pip in your terminal if you are in a local environment.

1. ### Install `pip` if Needed
   1. First, get the `get-pip.py` file from the following link:  
   [https://bootstrap.pypa.io/get-pip.py](https://bootstrap.pypa.io/get-pip.py)
   2. Run it in your local Python environment or alternatively use `cd` in your terminal to get into the file and run it with `python3`:
      
```Bash
cd /Directory/to/get-pip.py
python3 get-pip.py
```
> *NOTE:* Replace *"/Directory/to/get-pip.py"* with the actual directory to `get-pip.py`

2. ### Remove Basic `pygame` (if installed)
If you don't have pygame installed, you may skip the following step to delete the basic pygame. If you do have this command, run the following in your terminal to delete pygame so that you may replace it with `pygame-ce`.

```Bash
pip uninstall pygame
```

If that did not work, you can alternatively try the following command:

```Bash
pip3 uninstall pygame
```

3. ### Install `pygame-ce`

> ##### Why `pygame-ce`?
>
> We decided to use `pygame-ce`, the community fork of pygame, because of its continuous updates and security fixes. It also helps our game work faster than the original. Codewise, it's very similar; you can just call `import pygame` just like the original!

You may now install `pygame-ce`:

```Bash
pip install pygame-ce
```

If that did not work, you can alternatively try the following command:

```Bash
pip3 install pygame-ce
```

> ***NOTE:*** These directions are assuming you are running Python verison 3 or higher.

4. ### Get Other Dependencies
Run the following commands in your terminal to install the rest of the dependencies using `pip`.

```Bash
pip install supabase moderngl numpy
```

If that did not work, you can alternatively try the following command:

```Bash
pip3 install supabase moderngl numpy
```

> ***NOTE:*** These directions are assuming you are running Python verison 3 or higher.

## How to Run <a name="how_to_run"></a>



## How to Play <a name="how_to_play"></a>


# Legal Stuff <a name="legal_stuff"></a>


## Credits <a name="credits"></a>

*Background Music:* **Ocean wave loops** by DesiFreeMusic found on [Pixabay](https://pixabay.com/):  
[https://pixabay.com/music/upbeat-ocean-wave-loops-377890/](https://pixabay.com/music/upbeat-ocean-wave-loops-377890/)  
Under the following license:  
[https://pixabay.com/service/license-summary/](https://pixabay.com/service/license-summary/)

*Cannonball:* found on [pngimg.com](pngimg.com):  
[https://pngimg.com/image/108033](https://pngimg.com/image/108033)  
Under the following license:  
[Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](https://pngimg.com/license)

*Button Sounds:* **Casual Click Pop UI 3** and **casual Click Pop UI 2** by floraphonic found on [Pixabay](https://pixabay.com/):<br>
[https://pixabay.com/sound-effects/casual-click-pop-ui-2-262119/](https://pixabay.com/sound-effects/casual-click-pop-ui-2-262119/)<br>
[https://pixabay.com/sound-effects/casual-click-pop-ui-3-262120/](https://pixabay.com/sound-effects/casual-click-pop-ui-3-262120/)<br>
Under the following license:  
[https://pixabay.com/service/license-summary/](https://pixabay.com/service/license-summary/)

*Boat Moving Sounds:* **Boat on River** by paulprit (Freesound) found on [Pixabay](https://pixabay.com/):  
[https://pixabay.com/sound-effects/boat-on-river-26388/](https://pixabay.com/sound-effects/boat-on-river-26388/)  
Under the following license:  
[https://pixabay.com/service/license-summary/](https://pixabay.com/service/license-summary/)  

*Boat Resting Sound* **big motor** by Kibelon (Freesound) found on [Pixabay](https://pixabay.com/):  
[https://pixabay.com/sound-effects/big-motor-90117/](https://pixabay.com/sound-effects/big-motor-90117/)  
Under the following license:  
[https://pixabay.com/service/license-summary/](https://pixabay.com/service/license-summary/)  

*Sprites (Including Player and Enemy)* Made by **Liam Blackmon**

## License

This project is made open-source by the MIT license, which can be found in `LICENSE` on the main page of the repository.
