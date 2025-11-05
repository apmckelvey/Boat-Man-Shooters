<h1 align="center">Welcome to Boat Man Shooters 👋</h1>

## Literal *Table* of Contents

| Section | Subsection | Sub-subsection |
|---------|------------|----------------|
| [Overview](#overview) | [Features](#features) | |
| [Mechanics](#mechanics) | [File Structure](#file_structure) | |
| | [Logic](#logic) | [Initialization](#initialization) |
| | | [Game Setup](#game_setup) |
| | | [Main Gameplay Loop](#main_gameplay_loop) |
| | | [Feedback Generation](#feedback_generation) |
| | | [Game State Check](#game_state_check) |
| | [Code](#code) | |
| [Usage](#usage) | [Installation of Dependencies](#installation_of_dependencies) | |
| | [How to Run](#how_to_run) | |
| | [How to Play](#how_to_play) | |
   
# Overview <a name="overview"></a>

This is a version of the popular game Wordle played through the Python terminal. This Wordle game allows players to guess 5-letter words with visual feedback. Words are pulled from a CSV file with multiple difficulty levels, and the game provides hints when needed.

## Features <a name="features"></a>

- Multiple difficulty levels:
  - Easy
  - Medium
  - Hard
  - Legend
  - Brainrot (The language of Gen Z and Gen Alpha)

- Random word selection based on the chosen difficulty.

- CSV-based word storage with Definition, Difficulty, Hint, Category, and Topic included for each word.
  - There are around 30 words per difficulty.

- A timer for Hard and Legend difficulties.

- Feedback of letter placement with the colors green, yellow and gray.

# Mechanics <a name="mechanics"></a>

## File Structure <a name="file_structure"></a>

The text-based game has the following structure:  
├── main.py&emsp;&emsp; &emsp;&emsp;&emsp;&emsp;&emsp; &emsp;&emsp;&emsp;&emsp;&emsp; &emsp;Python file of the game.  
├── dictionary.csv&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;Word selection database in CSV format.  
├── english_words.csv&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;All words in the English language in CSV format.  
├── Picture.png&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;The file for the picture in `ReadMe.md`  
└── ReadME.md&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; &emsp;&emsp; This documentation file you are reading right now.  

## Logic <a name="logic"></a>


The game operates on a sequential flow controlled by a series of functions and loops. The core logic can be broken down into the following steps:

1. Initialization: Loading word lists and setting difficulty
2. Gameplay Loop: Get guess, give feedback and checking wins or loses
3. Game ends: Reveal words or the defenitions of the words


### Initialization: <a name="initialization"></a>

- The script begins by importing necessary libraries (`csv`, `time`, `threading`, `colorama`, etc.).
- A welcome message is displayed, and the `ready()` function is called to ask the player if they wish to start.

### Game Setup: <a name="game_setup"></a>

- Once the player agrees, the `difficulty_choice()` function is initiated.
- The player is prompted to select a difficulty level. This choice is stored as a global variable.
- The `choose_word()` function reads `dictionary.csv`, filters the words that match the chosen difficulty and the required 5-letter length, and then randomly selects one word to be the secret `word_to_guess`. The corresponding hint and definition are also stored.
- A comprehensive list of valid English words is loaded from `english_words.csv` into a set for fast, efficient validation of player guesses.

### Main Gameplay Loop: <a name="main_gameplay_loop"> </a>

- The game gives the player 6 guesses. A while loop runs as long as the player has guesses remaining.

#### Input Handling:

- For Hard and Legend difficulties, the game calls `get_timed_guess()`. This function uses threading to run a 15-second countdown timer in the main thread while simultaneously waiting for user input in a separate thread. If the timer expires, the guess is nullified, and the game ends.
- For other difficulties, a standard `input()` prompt is used.

#### Guess Validation:

- The player's input is checked to ensure it is exactly 5-letters long and exists within the set of valid English words loaded earlier. The player is re-prompted until a valid guess is entered.

### Feedback Generation: <a name="feedback_generation"></a>

- Once a valid guess is submitted, it is compared against the `word_to_guess` to generate colored feedback. This process correctly handles duplicate letters:
    1. A temporary copy of the secret word `word_copy` is created as a checklist.
    2. The game first iterates through the guess to find all green letters (correct letter in the correct position). When a green letter is found, it is "crossed off" from `word_copy` to prevent it from being used again.
    3. The game then iterates a second time for the remaining letters. It checks if a letter exists anywhere in the modified word_copy. If it does, it's marked as yellow (correct letter, wrong position), and that letter is "crossed off" from word_copy.
    4. Any remaining letters are marked as grey (not in the word).
- The colored feedback is printed to the console.

### Game State Check: <a name="game_state_check"></a>

- If the guess perfectly matches the secret word, the player wins. A success message is displayed along with the word's definition, and the game ends.
- If the guess is incorrect, the game offers the player a one-time hint.
- If the player runs out of guesses, a "game over" message reveals the secret word and its definition.

## Code <a name="code"></a>

To start, all the necessary modules are imported:
``` Python
import csv
import time
import sys
import random
from colorama import Fore, init
import threading
# Colorama initiated with autoresetting of colors
init(autoreset=True)
````

Then, the scroll print function is defined, which uses the sys module to print each charachter in a flush movement:

``` Python
def print_text(text):
 for char in text:
     sys.stdout.write(char)
     sys.stdout.flush()
     time.sleep(0.05) 
 print()
```

The `hint_called variable` is set to `False` at first, as the hint is not called. This is because the function then is defined after that, gives you the option to receive a hint or to keep on playing if and only if the hint was not called previously:

``` Python
hint_called = False

def offer_hint():
    global hint_called

    if not hint_called:
        hint_question = ""
        while hint_question not in ["yes", "no"]:
            print_text(f"Would you like a hint? (yes/no):")
            hint_question = input("> ").lower()

            if hint_question == "yes":
                hint_called = True
                print_text(f"Okay! Here is your hint: ")
                print_text(f"{hint}")
                break
            elif hint_question == "no":
                print_text("Okay! Back to guessing...")
                break
            else:
                print_text("Invalid input, please enter yes or no.")
```

Then the choose a random word function, which reads the csv file, and uses the data pulled from it in the form of lists to select a random word, its hint, and definition if it meets the length and dificulty criteria.

```Python
def choose_word():
    global word_to_guess, difficulty, hint, definition
    word_list = []
    hints_list = []
    definitions_list = []
    with open('dictionary.csv', 'r') as file:
        reader = csv.reader(file)
        next(reader)
        for row in reader:
            word = row[0].strip().upper()
            diff = row[2].strip().lower()
            hint_text = row[3].strip()
            definition_text = row[1].strip()
            if len(word) == 5 and word.isalpha() and diff == difficulty.lower():
                word_list.append(word)
                hints_list.append(hint_text)
                definitions_list.append(definition_text)
    if word_list:
        word_to_guess = random.choice(word_list)
        hint = hints_list[word_list.index(word_to_guess)]
        definition = definitions_list[word_list.index(word_to_guess)]
```

The start of the game is then defined and the user is asked of they want to play or not:

```Python
    def ready():
    ready_choice = ""
    while ready_choice not in ["yes", "no"]:
        print_text("Are you ready, enter yes/no:")
        ready_choice = input("> ").lower()
        if ready_choice == "yes":
            # They will choose their difficulty
            difficulty_choice()
            break
        elif ready_choice == "no":
            print_text("Goodbye")
            exit()
        else:
            print_text("Invalid input, please enter yes or no...")
```

The get input function is then defined to get inputs from a different thread. Basically, it is running both the timer function and the input frunction simultaneously by putting one of them on a different thread.

```Python
def get_input(prompt_text):
    try:
        print_text(prompt_text)
        answer[0] = input("> ").upper()
    except EOFError:
        pass
```

The timer function is then defined, which runs in the main thread as the input runs in a separate thread:

```Python
def get_timed_guess(guesses_left, timeout=15):
    answer = [None]
    prompt = f"Enter your guess ({guesses_left} guesses remaining): "
    input_thread = threading.Thread(target=get_input, args=(prompt,))
    input_thread.daemon = True
    input_thread.start()

    # Countdown loop in the main thread
    for remaining in range(timeout, 0, -1):
        input_thread.join(1)

        if not input_thread.is_alive():
            return answer[0]
            
        timer_message = f"     [{remaining - 1:2d}s remaining] "
        sys.stdout.write(timer_message)
        sys.stdout.flush()

        erase_message = '\b' * (len(timer_message))
        sys.stdout.write(erase_message)
        sys.stdout.flush()

    print("\nTIME'S UP! Your guess was not submitted.")
    return None
```

The main part of the game is defined, where the hint status is reset, the user chooses their difficulty, a word to guess is chosen from the choose word function, and all the words in the English language is pulled from the corresponding csv and stored in a set.

```Python
def difficulty_choice():
    reset_hint_status()
    global difficulty
    difficulty = ""
    while difficulty not in ["easy", "medium", "hard", "legend", "brain rot"]:
        print_text("Choose a difficulty: Easy, Medium, Hard, Legend, or Brain Rot:")
        difficulty = input("> ").lower()
        if difficulty not in ["easy", "medium", "hard", "legend", "brain rot"]:
            print_text("Please enter Easy, Medium, Hard, Legend, or Brain Rot...")
    choose_word()
    valid_words = set()
    with open('english_words.csv', 'r') as english_words:
        reader = csv.reader(english_words)
        for row in reader:
            valid_words.add(row[0].strip().upper())
```

The main gameplay then begins where the user gets a timed guess if they selected the hard/legend difficulty or a standard guess if they chose any of the other difficulties:

```Python
    guesses_left = 6
    while guesses_left > 0:
        guess = ""
        while True:
            if difficulty in ["hard", "legend"]:
                guess = get_timed_guess(guesses_left)
                if guess is None:
                    guesses_left = 0  
                    break 
            else:
                print_text(f"Enter your guess ({guesses_left} guesses remaining):")
                guess = input("> ").upper()
            if len(guess) != 5:
                print_text("Your guess must be 5-letters long.")
            elif guess not in valid_words:
                print_text("That's not a valid word.")
            else:
                break
        if guess is None:
            break
        guesses_left -= 1
```

The game then cycles through the characters of the word, and prints out the "feedback"; if the letter is in the right place it is green, if the letter is in the word, not in the right place, and is still yet to be guessed, then it is yellow. Otherwise, the letter will be printed as gray. If not guessed exactly, then a hint is offered if not offered before. If guessed right, then the user will recieve a congratulatory message.

```Python
        word_copy = list(word_to_guess)
        feedback = ""
        for i in range(len(guess)):
            if guess[i] == word_to_guess[i]:
                feedback += Fore.GREEN + guess[i]
                word_copy[i] = '*'  
            elif guess[i] in word_copy:
                feedback += Fore.YELLOW + guess[i]
                index = word_copy.index(guess[i])
                word_copy[index] = '*'
            else:
                feedback += Fore.WHITE + guess[i]
        print(feedback)
        if guess == word_to_guess:
            print_text("\nYOU GUESSED IT!!!")
            print_text(f"It means {definition}")
            return
        else:
            offer_hint()
            pass


print_text(f"\nYOU RAN OUT OF GUESSES!!! The word was {word_to_guess} - {definition}")
```

At the end of the code is the entrypoint of the game, where the user is asked if they are ready with the ready function:

```Python
print_text("Welcome to Wordle")
ready()
```

# Usage <a name="usage"></a>

## Installation of Dependencies <a name="installation_of_dependencies">

This project uses `colorama`, which is a dependency not built in to the Python system. To install this dependency, you will have to use pip in your terminal if you are in a local environment.

1. ### Install `pip` if Needed
   1. First, get the `get-pip.py` file from the following link: <ul> `https://bootstrap.pypa.io/get-pip.py` </ul>
   2. Run it in your local Python environment or alternatively use `cd` in your terminal to get into the file and run it with `python3`:
      
```Bash
cd /Directory/to/get-pip.py
python3 get-pip.py
```
> *NOTE:* Replace *"/Directory/to/get-pip.py"* with the actual directory to `get-pip.py`

2. ### Get Colorama
Run the following in your terminal to install `colorama` using `pip`.

```Bash
pip install colorama
```

If that did not work, you can alternatively try:

```Bash
pip3 install colorama
```

> ***NOTE:*** These directions is assuming you are running Python verison 3 or higher.

## How to Run <a name="how_to_run"></a>

To start, open your Python environment with a valid interpreter. The interpreter must be Python version 3 or higher. Next, open the `main.py` file and run it. Ensure that all other files, notably `english_words.csv` and `dictionary.csv`, are in the same folder. Then, open the main.py file and run it in your environment, Replit, VS Code, and Pycharm being major examples.

## How to Play <a name="how_to_play"></a>

The user should try to guess a five letter word in 6 guesses. The letters in the 5-letter word are either yellow, green, or grey. If the letter is yellow, then the letter is in the wrong place, but the letter is still in the word. If the letter is grey than the letter is not in the 5-letter word at all. If the letter is green than it is in the right place in the 5-letter word. 

> *Pro Tip!* If the user wants to ensure that they guess the correct word they should start with a word that has a lot of vowels like, "Audio" or "Adieu". 
