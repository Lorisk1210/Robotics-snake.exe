<!-- 2d0ee47d-98df-468a-a8e1-71625b9f4344 3623ba3c-b254-42e7-817a-f87c2e8dec74 -->
# xArm7 Dice Game Project Plan

## Project Overview

A robotics system where an xArm7 arm plays a board game: detects dice via overhead camera, grasps and throws it, reads the result via CV, and moves game pieces accordingly.

## Recommended Hardware Specifications

### Dice & Game Pieces

- **Dice**: 3D print larger dice (4-5cm side length) with:
  - High contrast dots/pips (black dots on white, or white on dark)
  - Sharp, clear edges for better detection
  - Weighted enough for consistent throws
- **Character Pieces**: 3-4cm tokens with distinct colors/shapes per player
- **Playing Field**: 30-50cm × 30-50cm board with grid markings

## Software Stack & Libraries

### Core Libraries

1. **Python 3.9+** - Main development language
2. **OpenCV (cv2)** - Image processing, camera calibration, pose estimation
3. **NumPy** - Numerical computations for coordinate transformations
4. **Requests** - HTTP client for xArm API calls
5. **MediaPipe or YOLOv8** - Object detection for dice and pieces

   - MediaPipe: Faster, good for known objects
   - YOLOv8: More robust, can train custom model

### Additional Libraries

6. **scikit-image** - Image processing utilities
7. **pygame or tkinter** - Optional game UI/visualization
8. **json** - API response handling (built-in)

## System Architecture

### 1. Camera Calibration Module (`calibration/`)

- **Camera calibration** - Intrinsic parameters (focal length, distortion)
- **Coordinate transformation** - Map camera pixel coordinates to robot world coordinates
- **Perspective correction** - Handle camera angle/height for accurate positioning

### 2. Computer Vision Module (`vision/`)

- **Dice detection** - Detect dice position/orientation on field
- **Dice recognition** - Read dice face value (before/after throw)
  - Option A: Template matching (simpler, faster)
  - Option B: CNN classifier (more robust to variations)
- **Character tracking** - Detect and track game pieces positions

### 3. Robot Control Module (`robot/`)

- **API client** - Wrapper for xArm REST API
- **Motion planning** - Calculate trajectories for:
  - Picking dice from detected location
  - Throwing motion (upward/downward arc)
  - Moving character pieces
- **Gripper control** - Open/close with appropriate force

### 4. Game Logic Module (`game/`)

- **State management** - Track board state, player positions
- **Turn management** - Robot vs human turns
- **Win condition** - Detect when goal is reached

### 5. Main Orchestration (`main.py`)

- **Integration** - Coordinate vision → robot → game logic
- **Error handling** - Retry mechanisms, safety checks
- **User interface** - Simple CLI or GUI for game control

## Implementation Approach

### Phase 1: Setup & Calibration

1. Set up Python environment and install dependencies
2. Create API client wrapper for xArm7 endpoints
3. Implement camera capture and calibration
4. Create coordinate transformation system (camera pixels → robot coordinates)
5. Test with known positions on playing field

### Phase 2: Computer Vision Pipeline

1. **Dice Detection**:

   - Use color thresholding or object detection to find dice
   - Calculate dice center and orientation
   - Handle multiple dice (select closest/best candidate)

2. **Dice Number Reading**:

   - After throw, detect dice and read top face
   - Template matching against known dice patterns (1-6)
   - Fallback: OCR or contour analysis for pip counting

3. **Character Tracking**:

   - Detect colored markers/tokens
   - Track positions on grid

### Phase 3: Robot Control

1. **Grasping Strategy**:

   - Approach dice from above with slight angle
   - Use inverse kinematics to reach detected position
   - Implement collision avoidance (safe approach/departure paths)

2. **Throwing Motion**:

   - Lift dice above throwing zone
   - Execute throwing trajectory (arc motion)
   - Release at optimal point for fair roll

3. **Piece Movement**:

   - Calculate target grid position based on dice result
   - Plan path to move character piece
   - Execute movement with precision

### Phase 4: Integration & Game Logic

1. Implement turn-based game loop
2. Combine vision → robot → game state updates
3. Add human input handling (their turn)
4. Win condition detection
5. Error recovery and retry logic

## Key Technical Challenges & Solutions

### Challenge 1: Camera-to-Robot Coordinate Transformation

**Solution**: Calibration routine using known reference points

- Place markers at known robot coordinates
- Capture with camera, establish transformation matrix
- Use perspective transformation + scaling

### Challenge 2: Dice Number Recognition

**Solution**: Multi-method approach

- Template matching for standard orientations
- Contour analysis to count pips
- ML classifier as fallback (if needed)

### Challenge 3: Reliable Grasping

**Solution**: Robust approach strategy

- Pre-grasp pose: approach from safe height
- Gripper alignment based on dice orientation detection
- Force feedback (if API supports) or position-based verification

### Challenge 4: Consistent Dice Throwing

**Solution**: Controlled release mechanism

- Use throwing motion with consistent velocity
- Release timing based on trajectory
- Throw zone with boundaries to keep dice on field

## File Structure

```
Project/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── config.yaml             # Configuration (API endpoints, calibration data)
├── calibration/
│   ├── __init__.py
│   ├── camera_calib.py    # Camera intrinsics calibration
│   └── coord_transform.py # Camera ↔ Robot coordinate conversion
├── vision/
│   ├── __init__.py
│   ├── dice_detector.py   # Detect dice position
│   ├── dice_reader.py     # Read dice number
│   └── piece_tracker.py   # Track game pieces
├── robot/
│   ├── __init__.py
│   ├── api_client.py      # xArm API wrapper
│   ├── motion_planner.py  # Trajectory planning
│   └── gripper_control.py # Gripper operations
├── game/
│   ├── __init__.py
│   ├── game_state.py      # Board state management
│   └── game_logic.py      # Turn management, win conditions
└── utils/
    ├── __init__.py
    └── helpers.py         # Utility functions
```

## Team Assignments (3-Person Team)

### Team Member 1: Robot Control & Motion Planning
**Primary Focus**: xArm API integration, robot movements, and grasping

**Tasks**:
1. **API Client Development** (`robot/api_client.py`)
   - Study xArm API Swagger documentation
   - Create HTTP client wrapper for all robot endpoints
   - Implement status checking and error handling
   - Test basic robot movement commands

2. **Motion Planning** (`robot/motion_planner.py`)
   - Develop trajectory planning for:
     - Picking dice from arbitrary positions
     - Throwing motion (arc trajectory)
     - Moving character pieces on board
   - Calculate safe approach/departure paths
   - Implement collision avoidance

3. **Gripper Control** (`robot/gripper_control.py`)
   - Integrate gripper API endpoints
   - Implement open/close with appropriate force
   - Test gripping force for dice and pieces

4. **Grasping Strategy Implementation**
   - Design approach angles for dice pickup
   - Implement position verification after grasp
   - Test reliability with various dice orientations

**Deliverables**: Functional robot control module that can move arm, control gripper, and execute planned trajectories

**Dependencies**: Needs coordinate transformation from Team Member 2 for accurate positioning

---

### Team Member 2: Computer Vision & Calibration
**Primary Focus**: Camera setup, object detection, and coordinate transformations

**Tasks**:
1. **Camera Calibration** (`calibration/camera_calib.py`)
   - Set up camera capture pipeline
   - Implement camera intrinsic calibration (focal length, distortion)
   - Create calibration routine with checkerboard/calibration pattern
   - Test and validate calibration accuracy

2. **Coordinate Transformation** (`calibration/coord_transform.py`)
   - Develop camera-to-robot coordinate mapping
   - Implement perspective transformation
   - Create calibration routine with known reference points
   - Test accuracy with test positions

3. **Dice Detection** (`vision/dice_detector.py`)
   - Implement dice detection using OpenCV (color thresholding, contour detection)
   - Calculate dice center position and orientation
   - Handle multiple dice scenarios (select best candidate)
   - Return coordinates in both camera and robot frames

4. **Dice Number Reading** (`vision/dice_reader.py`)
   - Implement template matching for dice faces (1-6)
   - Alternative: Contour analysis to count pips
   - Test accuracy across various orientations and lighting
   - Return dice value after throw

5. **Character Piece Tracking** (`vision/piece_tracker.py`)
   - Detect and track game pieces by color/shape
   - Determine piece positions on grid
   - Track piece movements

**Deliverables**: Complete vision pipeline that detects dice, reads numbers, and provides accurate robot coordinates

**Dependencies**: Needs initial setup collaboration (shared requirements.txt)

---

### Team Member 3: Game Logic & Integration
**Primary Focus**: Game state, turn management, and system integration

**Tasks**:
1. **Project Setup** (Shared initially, but Team Member 3 manages)
   - Set up Python virtual environment
   - Create `requirements.txt` with all dependencies
   - Set up project structure and file organization
   - Create `config.yaml` for API endpoints, calibration data

2. **Game State Management** (`game/game_state.py`)
   - Design board state representation
   - Track player positions
   - Implement grid/board coordinate system
   - Store game history

3. **Game Logic** (`game/game_logic.py`)
   - Implement turn-based system (robot vs human)
   - Handle dice result integration
   - Calculate valid moves based on dice roll
   - Implement win condition detection
   - Add game rules validation

4. **Main Orchestration** (`main.py`)
   - Integrate all modules:
     - Vision pipeline → Robot control → Game logic
   - Implement error handling and retry logic
   - Create game loop with turn management
   - Add user interface (CLI or simple GUI)
   - Implement logging and debugging tools

5. **Integration Testing & Debugging**
   - Test end-to-end workflows
   - Coordinate testing sessions with team
   - Debug integration issues
   - Refine error handling

**Deliverables**: Complete integrated system with game logic and user interface

**Dependencies**: Requires both robot control and vision modules to be functional

---

## Shared Tasks & Collaboration Points

### Initial Setup (All Team Members)
- Week 1: Review API documentation together
- Set up shared repository and coding standards
- Agree on coordinate system conventions
- Define interface contracts between modules

### Key Integration Points
1. **Coordinate System**: Team Member 2 provides transformation functions that Team Member 1 uses
2. **Vision → Robot**: Dice position from CV module feeds into motion planner
3. **Dice Reading → Game Logic**: Dice value from CV feeds into game state
4. **Testing**: All members test integration as modules become available

### Communication Protocol
- **Interface Definitions**: Define function signatures early
- **Coordinate System**: Agree on units (mm, cm) and origin point
- **Error Handling**: Standardize error codes and exception handling
- **Testing**: Regular integration testing sessions

## Next Steps

1. **Immediate** (Week 1):
   - All: Review xArm API documentation
   - Team Member 3: Set up project structure and environment
   - Team Member 1: Start API client development
   - Team Member 2: Begin camera setup and calibration

2. **Short-term** (Weeks 2-3):
   - Team Member 1: Basic robot movements working
   - Team Member 2: Camera calibration and basic dice detection
   - Team Member 3: Game logic framework ready

3. **Integration Phase** (Week 4+):
   - Coordinate transformation testing (Member 1 + 2)
   - End-to-end testing (All members)
   - Refinement and error handling