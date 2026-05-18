# STM32 FreeRTOS Controlled Space Shooter Game

This project is a hardware-controlled retro-style space shooter game. The game interface is developed with Python and Pygame, while the player input and feedback system are handled by an STM32 Nucleo-F446RE board running FreeRTOS.

The player ship is controlled using an ADXL345 accelerometer. External buttons are used for firing and start/pause control. The STM32 sends real-time sensor and button data to the Python game over UART, while the Python game sends event commands back to the STM32 for LED feedback.

---

## Project Overview

The main goal of this project is to combine embedded systems and game development in a single interactive system.

The STM32 side handles:

- ADXL345 accelerometer reading
- Calibration and filtering
- External button event detection
- Fire button hold detection
- UART data transmission
- UART command reception
- FreeRTOS task management
- LED feedback through a FreeRTOS queue
- I2C error recovery for ADXL345 communication stability

The Python/Pygame side handles:

- Game rendering
- Player movement
- Enemy spawning
- Bullet systems
- Power-ups
- Boss fight with two phases
- Pixel-art assets
- Music and sound effects
- Game states such as start, pause, game over, and victory

---

## Hardware Components

| Component | Purpose |
|---|---|
| STM32 Nucleo-F446RE | Main embedded controller |
| ADXL345 Accelerometer | Player movement control |
| External Fire Button | Player shooting control |
| External Start/Pause Button | Game state control |
| Onboard / External LED | Game feedback from Python events |
| USB UART Connection | Communication between STM32 and Python |
| PC | Runs the Python/Pygame game |

---

## Circuit Diagram



---

## Pin Configuration

Update this table according to your final CubeMX configuration.

| Peripheral / Component | STM32 Pin / Connection | Function | Description |
|---|---|---|---|
| ADXL345 VCC | 3.3V | Power | Sensor power supply |
| ADXL345 GND | GND | Ground | Common ground |
| ADXL345 SCL | PB8 | I2C1_SCL | I2C clock line |
| ADXL345 SDA | PB9 | I2C1_SDA | I2C data line |
| ADXL345 CS | 3.3V | I2C Mode Select | Must be connected to HIGH for I2C mode |
| ADXL345 SDO | GND or 3.3V | I2C Address Select | GND → address `0x53`, 3.3V → address `0x1D` |
| Fire Button | `fire_Pin` | GPIO Input Pull-up | Sends fire event and fire-hold state |
| Start/Pause Button | `ctrl_Pin` | GPIO Input Pull-up | Sends start/pause control event |
| LED Feedback | `led_Pin` | GPIO Output | Displays game event feedback |
| UART TX | PA2 | USART2_TX | STM32 to PC serial transmission |
| UART RX | PA3 | USART2_RX | PC to STM32 serial command reception |
| USB | ST-LINK Virtual COM Port | UART Bridge | Used for Python communication |


> For ADXL345 I2C usage, `CS` must be tied to `3.3V`. The `SDO` pin determines the I2C address. In this project, the library uses `0x53 << 1`, so the `SDO` pin is connect to `GND`.

---

## System Architecture

The system is divided into two main parts:

```
STM32 + FreeRTOS
        |
        | UART JSON packets
        v
Python / Pygame Game
        |
        | UART event commands
        v
STM32 LED Feedback
```

---

### STM32 to Python Data Flow

The STM32 continuously sends JSON-formatted data to the Python game:
```
{
  "x": 12,
  "y": -4,
  "z": 1,
  "fire": 0,
  "fire_hold": 1,
  "ctrl": 0,
  "cal": 1
}
```

| Field       | Description                                  |
| ----------- | -------------------------------------------- |
| `x`         | Filtered and calibrated ADXL345 X-axis value |
| `y`         | Filtered and calibrated ADXL345 Y-axis value |
| `z`         | Filtered and calibrated ADXL345 Z-axis value |
| `fire`      | One-shot fire button event                   |
| `fire_hold` | Fire button hold state                       |
| `ctrl`      | One-shot start/pause button event            |
| `cal`       | ADXL345 calibration status                   |

--- 

### Python to STM32 Command Flow

The Python game sends single-character commands to the STM32 when specific game events occur.

| Command | Event         |
| ------- | ------------- |
| `F`     | Player fired  |
| `H`     | Player hit    |
| `B`     | Boss appeared |
| `W`     | Player won    |
| `G`     | Game over     |

These commands are received through UART interrupt and passed to a FreeRTOS queue for LED feedback handling.

---

## FreeRTOS Architecture

The STM32 firmware uses multiple FreeRTOS tasks to separate sensor reading, UART transmission, UART reception, and LED feedback.

| Object      | Type          | Purpose                                                       |
| ----------- | ------------- | ------------------------------------------------------------- |
| `dataMutex` | Mutex         | Protects shared accelerometer and button data                 |
| `ledQueue`  | Message Queue | Transfers game event commands from UART interrupt to LED task |

---

### FreeRTOS Tasks

1. ``` StartReadSensorTask```

This task is responsible for reading the ADXL345 accelerometer and detecting external button events.

Main responsibilities:

- Initializes the ADXL345 sensor
- Performs startup calibration
- Reads raw X, Y, and Z accelerometer values
- Applies offset calibration
- Applies low-pass filtering
- Detects fire button press events
- Detects fire button hold state
- Detects start/pause button press events
- Updates the shared accelData structure using dataMutex
- Performs simple I2C recovery when ADXL345 readings freeze

The ADXL345 values are first calibrated using an average of multiple samples. After calibration, raw values are converted into relative movement data by subtracting the offset values.

A low-pass filter is used to reduce noisy movement:
```
filteredX = (FILTER_ALPHA * calibratedX)
          + ((1.0f - FILTER_ALPHA) * filteredX);
```

The task also monitors whether the ADXL345 values remain unchanged for too long. If the sensor data freezes, the ADXL345 is reinitialized and the filter values are reset.

This recovery mechanism was added because the I2C communication occasionally became unstable during runtime.

2. ```StartDataSendTask```

This task sends the latest sensor and button data to the Python game over UART.

Main responsibilities:

- Copies shared data from accelData
- Protects data access using dataMutex
- Sends JSON packets over USART2
- Clears event-based fields after transmission

The fire and ctrl fields are event-based. After they are copied into the UART packet, they are reset to 0.

The fire_hold field is not reset after transmission because it represents the current button state.

3. ```StartUartRxTask```

This task starts UART reception in interrupt mode.

Main responsibilities:

- Starts HAL_UART_Receive_IT
- Keeps UART reception active

The actual command processing is handled inside the UART receive complete callback: ```HAL_UART_RxCpltCallback()```
After each byte is received, UART interrupt reception is restarted.

4. ```HAL_UART_RxCpltCallback```
This is not a FreeRTOS task, but it is an important part of the communication system.

Main responsibilities:

- Receives single-character commands from Python
- Checks whether the command is valid
- Pushes valid commands into ledQueue
- Restarts UART interrupt reception

The callback does not directly blink the LED. Instead, it sends the command to a queue: ```osMessageQueuePut(ledQueueHandle, &cmd, 0, 0);```
This avoids doing blocking LED operations inside an interrupt callback.

5. ```StartLedFeedbackTask```

This task waits for LED feedback commands from the queue.

Main responsibilities:

- Waits for commands from ledQueue
- Calls HandleGameCommand()
- Executes LED feedback patterns

| Command | LED Behavior              |
| ------- | ------------------------- |
| `F`     | Short blink for fire      |
| `H`     | Multiple blinks for hit   |
| `B`     | Boss alert pattern        |
| `W`     | Victory pattern           |
| `G`     | Long LED on for game over |

---

## Python / Pygame Game Architecture

| File             | Purpose                                               |
| ---------------- | ----------------------------------------------------- |
| `main.py`        | Main game loop and state control                      |
| `settings.py`    | Game constants and configuration                      |
| `game_state.py`  | Game state definitions                                |
| `assets.py`      | Sprite, animation, and asset loading                  |
| `serial_comm.py` | UART communication with STM32                         |
| `player.py`      | Player movement, hitbox, damage state, shield state   |
| `bullets.py`     | Player and enemy bullet systems                       |
| `enemy.py`       | Small enemy spawning, movement, hitbox, and collision |
| `boss.py`        | Boss fight logic and phase system                     |
| `powerups.py`    | Shield, rapid fire, and triple shot power-ups         |
| `explosions.py`  | Destruction animations                                |
| `ui.py`          | UI, screens, and scrolling background                 |
| `audio.py`       | Music and sound effect management                     |

---

## Game Features

### Player Control

The player ship is controlled by tilting the ADXL345 accelerometer.

The STM32 sends filtered accelerometer values to Python, and the Python game converts these values into player movement.

The player can move:

- Left
- Right
- Forward
- Backward

### Fire System

| Signal      | Purpose               |
| ----------- | --------------------- |
| `fire`      | One-shot fire event   |
| `fire_hold` | Continuous hold state |

Normal shooting uses ```fire```.

Rapid fire uses ```fire_hold```, allowing continuous shooting while the button is held.

### Power-ups

The game includes three power-up types:

| Power-up    | Effect                          |
| ----------- | ------------------------------- |
| Shield      | Blocks one hit                  |
| Rapid Fire  | Allows continuous fast shooting |
| Triple Shot | Fires three bullets at once     |

If the player already has an active shield and collects another shield, the player receives a score bonus instead of stacking shields.

### Boss Fight

The boss appears after reaching a defined score threshold.

The boss fight has two phases:

| Phase   | Condition          | Behavior                                         |
| ------- | ------------------ | ------------------------------------------------ |
| Phase 1 | HP above 50%       | Normal speed, single bullet                      |
| Phase 2 | HP at or below 50% | Faster movement, faster shooting, spread bullets |

The boss health bar changes color when Phase 2 begins.

---

## Communication Protocol

### STM32 to Python

The STM32 sends JSON packets through UART:

```{"x":12,"y":-4,"z":1,"fire":0,"fire_hold":1,"ctrl":0,"cal":1}```

### Python to STM32

Python sends single-character event commands:
```
F  -> Fire
H  -> Hit
B  -> Boss
W  -> Win
G  -> Game Over
```

---

## Reliability Improvements

During development, the ADXL345 readings occasionally froze due to I2C communication instability.

To solve this, an I2C recovery mechanism was added. If the sensor values remain unchanged for a defined timeout, the ADXL345 is reinitialized and the filter state is reset.

This improved runtime stability and prevented the player movement from freezing during gameplay.

---

## How to Run

### STM32 Side

1. Open the STM32 project in STM32CubeIDE.
2. Check the .ioc configuration.
3. Connect the ADXL345 and external buttons according to the pin table.
4. Build and flash the firmware to the STM32 Nucleo-F446RE.
5. Keep the board connected through USB.

### Python Side

1. Install Python dependencies:
```
pip install pygame pyserial
```

2. Check the serial port in ```settings.py```:
```
SERIAL_PORT = "COM5"
BAUD_RATE = 115200
```

3. Run the game:
```
python main.py
```

---

## Libraries and Assets

- ADXL345 Library: [ADXL345]([Repo](https://github.com/arifmandal/STM32-ile-Sensor-Kutuphaneleri-Gelistirme-Kursu/tree/ADXL345))

- Player Assets: [Void Main Ship by Foozle](https://foozlecc.itch.io/void-main-ship)

- Enemy Assets: [Void Fleet Pack 1 Kla'ed by Foozle](https://foozlecc.itch.io/void-fleet-pack-1)

- Power-up Assets: [Void Pickups Pack by Foozle](https://foozlecc.itch.io/void-pickups-pack)

- Background: [Space Background Generator by Deep-Fold](https://deep-fold.itch.io/space-background-generator)

- Audio Asset 1: [7 Space Sounds by Joth](https://opengameart.org/content/7-space-sounds)

- Audio Asset 2: [63 Digital sound effects (lasers, phasers, space etc.) by Kenney](https://opengameart.org/content/63-digital-sound-effects-lasers-phasers-space-etc)

- Audio Asset 3: [Battle Zero by Bobjt](https://opengameart.org/content/battle-zero)

- Audio Asset 4: [Space Shoot Sounds by Robin Lamb](https://opengameart.org/content/space-shoot-sounds)

- Audio Asset 5: [Retro Shooter Sound Effects by Muncheybobo](https://opengameart.org/content/retro-shooter-sound-effects)

## Demo Video

You can watch the demo video from here:

[Watch Demo Video](https://youtu.be/xA2_12lr0Jk)