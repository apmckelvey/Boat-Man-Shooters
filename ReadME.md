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

***App Building Status***:  [![Build App With Nuitka](https://github.com/apmckelvey/boat-man-shooters/actions/workflows/app-build.yml/badge.svg)](https://github.com/apmckelvey/boat-man-shooters/actions/workflows/app-build.yml)
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

```
├── .github/                  GitHub configuration (workflows, issue templates, etc.)  
├── Assets/                   Fonts, music, sound effects (button clicks, etc.)
│   ├── DynaPuff Font/        Font files for text in game 
│   └── Sounds/               Music, boat sounds, cannonball sound effects, etc.
├── Button-Test/              HTML test page for button animations  
├── Game_Code/                Core game source code  
├── Graphics/                 Visual assets  
│   ├── Maps/                 Map tiles & items  
│   ├── Sprites/              Character & object sprites  
│   ├── Buttons/              UI buttons  
│   └── Menus/                Game menus & screens  
├── Logos/                    All project logos and icons  
├── docs/                     GitHub Pages website source  
├── .gitignore                Files and folders ignored by Git  
├── requirements.txt          Python dependencies (for Dependabot)  
├── CODE_OF_CONDUCT.md        Contributor Covenant Code of Conduct  
├── LICENSE                   Project license  
├── MyIcon.icns               macOS app icon  
└── README.md                 You’re reading this right now!  
```

## Logic <a name="logic"></a>
<img src="Documentation/Game Logic Flowchart.png" alt="Game Logic Flowchart">

## Code <a name="code"></a>

The game's codebase is modular and loosely follows the **Model-View-Controller (MVC)** pattern to keep concerns separated and the project maintainable:

- **Model**: Manages game data and logic (players, projectiles, items, networking, prediction).
- **View**: Handles all rendering and visual presentation (renderer, shaders, buttons).
- **Controller**: Processes input, orchestrates the game loop, and ties everything together (primarily `main.py`).

The files interact through targeted imports, shared constants (`config.py`), and utility functions (`utils.py`). Execution starts at `main.py`, which initializes systems, runs the central game loop (handling events → updates → networking → rendering), and manages scene transitions (menus → lobby → gameplay).

**How the files work together**:

- **`config.py`**: The foundation—defines global constants (screen dimensions, colors, speeds, Supabase credentials, asset paths). Imported by nearly every other file to ensure consistent settings and avoid hardcoding.
- **`utils.py`**: Provides reusable helper functions (vector math, collision detection, angle calculations, distance checks). Imported by `player.py`, `cannonball.py`, `items.py`, `prediction.py`, and others for physics and logic calculations.
- **`player.py`**: Defines the `Player` class (boat state: position, rotation, health, velocity). Handles local input, movement, and shooting (spawns cannonballs). Depends on `config.py`, `utils.py`, and `cannonball.py`. Instances are created/updated in `main.py` and synced via `network.py`.
- **`cannonball.py`**: Defines the `Cannonball` projectile class (trajectory, speed, damage, lifetime). Created by `player.py` when shooting; updated in the main game loop. Uses `utils.py` for physics/collisions and interacts with `player.py` (applying damage on hit).
- **`items.py`**: Manages pickups/power-ups on the map (position, type, effects like health restore). Updated in the main loop; players collect them via collision checks (using `utils.py`). May be synced over the network for fairness.
- **`prediction.py`**: Implements client-side prediction and reconciliation to reduce perceived lag in multiplayer. Simulates future player/cannonball positions locally using `utils.py` math, then corrects based on authoritative data from `network.py`.
- **`network.py`**: Handles all multiplayer communication with Supabase (authentication, real-time database sync for player positions, shots, lobby state). Called frequently in the main loop; serializes/deserializes model data (`player.py`, `cannonball.py`) and works closely with `prediction.py` for smooth movement.
- **`shaders.py`**: Contains GLSL (*OpenGL Shading Language*) shader programs for advanced visual effects (water distortion, lighting, particles). Loaded and used exclusively by `renderer.py`.
- **`renderer.py`**: The core View—uses ModernGL to draw everything: players, cannonballs, items, UI, backgrounds, and effects. Loads textures from Graphics/ and Assets/, applies shaders from `shaders.py`, and is called every frame by `main.py`.
- **`buttons.py`**: Defines interactive UI buttons for menus (login, play, etc.), handling hover/click states, animations, and sound feedback. Drawn via `renderer.py` and processed in `main.py`'s event loop.
- **`main.py`**: The primary Controller and entry point. Initializes Pygame/ModernGL, loads assets, sets up the window, authenticates via `network.py`, and runs the infinite game loop: process input/events, update model (players, cannonballs, items), sync/predict network state, render via `renderer.py`, and cap FPS.
- **`multiplayer-tester.py`**: A standalone development tool that imports most of the above modules to simulate multiple clients or test networking/prediction in isolation (e.g., fake players). Not used in production but shares the same core logic.

This structure ensures loose coupling: rendering changes don't affect physics, and multiplayer logic can be tested independently. All assets (Graphics/, Assets/) are loaded dynamically at runtime, primarily by `renderer.py` and `buttons.py`.

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

### Option 1: Download Release  

Download the app for your desired operating system:   
**Website:** [https://apmckelvey.github.io/boat-man-shooters/](https://apmckelvey.github.io/boat-man-shooters/)  
**Releases Page:** [https://github.com/apmckelvey/boat-man-shooters/releases](https://github.com/apmckelvey/boat-man-shooters/releases)    

### Option 2: Build-it-Yoursef (macOS) From the Code  

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

### Option 2: Build-it-Yourself (`macOS`, `Windows`, `Linux`)  

You can use the repository's GitHub Actions workflow (`build-boat-man-shooters.yml`) to automatically build standalone executables for macOS, Windows, and Linux using Nuitka. This runs entirely in the cloud on GitHub's servers—no local installation, dependencies, or code changes required on your part.  
The workflow triggers automatically on pushes to the main branch and uploads the built apps as artifacts (downloadable files) to each workflow run.  
How to get the builds yourself (without editing the repo):  

1. Go to the repository's Actions tab: [https://github.com/apmckelvey/boat-man-shooters/actions](https://github.com/apmckelvey/boat-man-shooters/actions)  

2. In the left sidebar, select the workflow named `Build App With Nuitka`.  

3. You will see a list of past workflow runs. Look for the most recent successful run (marked with a green checkmark).  

4. Click on that run to open its details.  

5. Scroll down to the `Artifacts` section at the bottom of the page.  

6. Download the artifact that matches your operating system:  
 
  - macOS: a `.app` and the build data in a seperate folder  
  - Windows: an `.exe` and the build data in a seperate folder  
  - Linux: a `.bin` and the build data in a seperate folder  

7. Extract/unzip the downloaded artifact if necessary, then run the app directly.  

> *NOTE:* Artifacts are available for about 90 days after the run completes. Always use the most recent successful run for the latest build.  
> *NOTE:* New builds are only created when the repository owner pushes changes to the main branch. If no recent successful builds are available or you need one for the current code, you’ll need to ask the repository owner to trigger a new build (e.g., by making a small commit). Users cannot start the workflow manually without the owner enabling that feature.  

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

*Loading GIF* **load-33** by BlenderTimer found on [Pixabay](https://pixabay.com/):
[https://pixabay.com/gifs/load-loading-process-wait-delay-33/](https://pixabay.com/gifs/load-loading-process-wait-delay-33/)
Under the following license:  
[https://pixabay.com/service/license-summary/](https://pixabay.com/service/license-summary/)  


*Sprites (Including Player and Enemy)* Made by **Liam Blackmon**

## License <a name="license"></a>

This project is made open-source by the MIT license, which can be found in `LICENSE` on the main page of the repository.

## Contributing <a name="contributing"></a>

Please read our Code of Conduct before contributing, which can be found in `CODE_OF_CONDUCT.md` on the main page of the repository.
