# serial_comm.py - Serial communication management for the STM32 ADXL345 Space Shooter game

import serial
import json

from settings import SERIAL_PORT, BAUD_RATE


class SerialController:
    def __init__(self):
        self.ser = None
        self.serial_ok = False

        self.accel_x = 0
        self.accel_y = 0
        self.accel_z = 0

        self.fire_pressed = 0
        self.fire_hold = 0
        self.ctrl_pressed = 0
        self.calibrated = 0

        self._connect()

    def _connect(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.01)
            self.serial_ok = True
            print(f"Serial connected: {SERIAL_PORT}")
        except serial.SerialException as e:
            self.ser = None
            self.serial_ok = False
            print("Serial connection failed:", e)

    def read(self):
        if not self.serial_ok or self.ser is None:
            return

        fire_event = 0
        ctrl_event = 0
        received_data = False

        try:
            while self.ser.in_waiting > 0:
                line = self.ser.readline().decode("utf-8", errors="ignore").strip()

                if not line:
                    continue

                data = json.loads(line)
                #print(data)

                self.accel_x = int(data.get("x", self.accel_x))
                self.accel_y = int(data.get("y", self.accel_y))
                self.accel_z = int(data.get("z", self.accel_z))

                self.calibrated = int(data.get("cal", self.calibrated))
                self.fire_hold = int(data.get("fire_hold", self.fire_hold))

                if int(data.get("fire", 0)) == 1:
                    fire_event = 1

                if int(data.get("ctrl", 0)) == 1:
                    ctrl_event = 1

                received_data = True

            if not received_data:
                self.fire_pressed = 0
                self.ctrl_pressed = 0
                return

            self.fire_pressed = fire_event
            self.ctrl_pressed = ctrl_event

        except json.JSONDecodeError:
            pass
        except Exception as e:
            print("Serial read error:", e)

    def send_command(self, command):
        if not self.serial_ok or self.ser is None:
            return

        # Map game commands to single-character codes for STM32
        command_map = {
            "FIRE": "F",
            "HIT": "H",
            "BOSS": "B",
            "WIN": "W",
            "GAME_OVER": "G"
        }

        try:
            byte_command = command_map.get(command)

            if byte_command is None:
                print("Unknown STM32 command:", command)
                return

            self.ser.write(byte_command.encode("utf-8"))
            self.ser.flush()

        except Exception as e:
            print("UART command send error:", e)

    def close(self):
        if self.ser is not None:
            self.ser.close()