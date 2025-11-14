# xArm7 Snakes and Ladders Dice Game

A robotics system where an xArm7 arm plays Snakes and Ladders with a human player. The robot detects dice via camera, picks and throws the dice, reads the result, and moves game pieces.

## Setup

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```
2. **Configure robot** in `config.py`:

   - Update robot IP and coordinates if needed

## Usage

### CLI Game

```bash
python app.py
```

- Player goes first, rolls physical dice and enters value
- Robot automatically rolls, reads result, and moves
- First to reach field 30 wins

### Web Frontend

```bash
python start_frontend.py
```

Open `http://localhost:5001` in your browser

## Game Rules

**Ladders**: 3→7, 11→19, 15→23

**Snakes**: 6→4, 18→10, 27→16, 29→20

**Collision**: Landing on opponent sends them back to field 1

**Win**: First to field 30 wins

## Project Structure

```
├── app.py                    # CLI game entry point
├── start_frontend.py        # Web interface entry point
├── config.py                # Robot coordinates and config
├── robot/                   # Robot control (API, movement, gripper)
├── game/                    # Game logic and state
├── vision/                  # Dice detection and reading
└── frontend/                # Web UI
```

## Dependencies

numpy, opencv-python, pandas, scikit-learn, requests, flask, flask-sock
