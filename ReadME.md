<h1 align = center> Welcome to Boat Man Shooters 👋</h1>
<h1 align = center> (Work in Progress)</h1>
<p align="center">
  <img height="50%" width="50%" src="/Logos/logo.png">
</p>

<p align="center">
  <a href="https://apmckelvey.github.io/boat-man-shooters/">
    <img src="https://img.shields.io/badge/DOWNLOAD%20BOAT%20MAN%20SHOOTERS-1C7CFF?style=for-the-badge&logo=github&logoColor=white&labelColor=0969da" 
         alt="DOWNLOAD BOAT MAN SHOOTERS" 
         height="100">
  </a>
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
   3.2. [How to Run (Python Files)](#how_to_run)  
   3.3. [How to Play (App)](#how_to_play)  
4. [Legal Stuff](#legal_stuff)  
    4.1. [Credits](#credits)  
    4.2. [License](#license)  
    4.3. [Contributing](#contributing)  
   
# Overview <a name="overview"></a>

This is a online multiple player game where the intention is to shoot other boats and to stay alive. It is a constant lobby in which there can be a winner at any given time, given who is surviving. 

## Features <a name="features"></a>

- [X] Online multiplayer game
- [ ] Account system
- [ ] Fluid UI interface/animations
- [X] Sounds and background music
- [X] Both keyboard and controller input

# Mechanics <a name="mechanics"></a>

## File Structure <a name="file_structure"></a>

The game has the following structure:  
├── .github &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;***Configuration files for GitHub.***  
├── Assets &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;***Contains the font, music, and button sounds.***  
├── Button-Test &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; ***HTML test for button animations.***  
├── Game_Code &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;***Contains all the game cod.e***  
├── Graphics &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;***Contains Map Items, Sprites, Butons, and Menus.***  
├── Logos &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; ***All the logos and icons for our project.***  
├── docs &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; ***Website for GitHub Pages.***  
├── .gitignore &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; ***Tells GitHub to ignore specific files when commiting.***  
├── requirements.txt &nbsp; &nbsp; &nbsp; ***Tells GitHub Dependabot what dependencies are needed to update.***  
├── CODE_OF_CONDUCT.md &nbsp; &nbsp; &nbsp;***The code of conduct for this project.***  
├── LICENSE &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;***The license for this project.***  
├── MyIcon.icns &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;***The icon for this project used when building an app.***  
└── ReadME.md &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; ***This documentation file you are reading right now.***  

## Logic <a name="logic"></a>
<img src="Documentation/Game Logic Flowchart.png" alt="Game Logic Flowchart">

## Code <a name="code"></a>

Explain flow between files - tell reader that explainations of code can be found in deep dive.

# Usage <a name="usage"></a>

## Installation of Dependencies <a name="installation_of_dependencies">

This project uses the dependencies `pygame-ce`, `moderngl`, `numpy`, and `supabase`, which are not built in to the Python system. To install these dependencies, you will have to use pip in your terminal if you are in a local environment.

> ***NOTE: If you are running in an app, you will not need to install these dependencies. Please proceed to section 3.3***

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

## How to Run (Python Files) <a name="how_to_run"></a>
1. Clone the repository with the following command:
```Bash
git clone https://github.com/apmckelvey/boat-man-shooters.git
```

2. `cd` into the repository folder:
```Bash
cd /Directory/to/repository
```
> *NOTE:* Replace `"/Directory/to/repository"` with the actual directory to the repository

3. Run `main.py` using `Python`:
```Bash
python /Game_Code/main.py
```

If that did not work, you can alternatively try the following command:
```Bash
python3 /Game_Code/main.py
```

## How to Play (App) <a name="how_to_play"></a>
Download the app from the releases page: [https://github.com/apmckelvey/boat-man-shooters/releases](https://github.com/apmckelvey/boat-man-shooters/releases)

### Build-it-Yoursef From the Code

1. Install the dependencies as described in section 3.1 as well as the dependency `nuitka`:

```Bash
pip install nuitka
```

If that did not work, you can alternatively try the following command:

```Bash
pip3 install nuitka
```

> ***NOTE:*** These directions are assuming you are running Python verison 3 or higher.

2. Clone the repository with the following command:
```Bash
git clone https://github.com/apmckelvey/boat-man-shooters.git
```

3. `cd` into the repository folder:
```Bash
cd /Directory/to/repository
```
> *NOTE:* Replace `"/Directory/to/repository"` with the actual directory to the repository.

4. Run the following command:
```Bash
cd 'Directory/to/repository' && \
python -m nuitka --standalone \
  --macos-create-app-bundle \
  --macos-app-icon=MyIcon.icns \
  --product-name="Boat Man Shooters" \
  --macos-signed-app-name=com.apmckelvey.BoatManShooters \
  --include-data-dir=Assets=Assets \
  --include-data-dir=Graphics=Graphics \
  --include-data-dir=Logos=Logos \
  --include-data-dir=Documentation=Documentation \
  --include-data-file="./Assets/DynaPuff Font/DynaPuffFont.ttf"="Assets/DynaPuff Font/DynaPuffFont.ttf" \
  --output-dir=dist \
  Game_Code/main.py
```

If that did not work, you can alternatively try the following command:
```Bash
cd 'Directory/to/repository' && \
python3 -m nuitka --standalone \
  --macos-create-app-bundle \
  --macos-app-icon=MyIcon.icns \
  --product-name="Boat Man Shooters" \
  --macos-signed-app-name=com.apmckelvey.BoatManShooters \
  --include-data-dir=Assets=Assets \
  --include-data-dir=Graphics=Graphics \
  --include-data-dir=Logos=Logos \
  --include-data-dir=Documentation=Documentation \
  --include-data-file="./Assets/DynaPuff Font/DynaPuffFont.ttf"="Assets/DynaPuff Font/DynaPuffFont.ttf" \
  --output-dir=dist \
  Game_Code/main.py
```

This will create a folder called `dist` in the repository folder with the built app.

> *NOTE:* Replace `"/Directory/to/repository"` with the actual directory to the repository. Also, these directions are assuming you are running Python verison 3 or higher.

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

## License <a name="license"></a>

This project is made open-source by the MIT license, which can be found in `LICENSE` on the main page of the repository.

## Contributing <a name="contributing"></a>

Please read our Code of Conduct before contributing, which can be found in `CODE_OF_CONDUCT.md` on the main page of the repository.
