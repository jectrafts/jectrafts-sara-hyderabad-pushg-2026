import math
import time
import os
import shutil

# Get terminal size
width = shutil.get_terminal_size().columns
height = shutil.get_terminal_size().lines

# Torus parameters
R1 = width // 3  # Major radius
R2 = R1 // 10   # Minor radius

# Angle step and rotation
K2 = 5
K1 = 150

angle = 0

while True:
# Create a grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    # Render the torus
    for theta in range(0, 6 * 180):
        for phi in range(0, 6 * 360):
    # Calculate 3D coordinates
            x = R1 + R2 * math.cos(math.radians(theta))
            y = R2 * math.sin(math.radians(theta))
            z = R2 * math.sin(math.radians(phi))

    # Rotate around Y-axis
    rotated_x = x * math.cos(math.radians(angle)) - z * math.sin(math.radians(angle))
    rotated_z = x * math.sin(math.radians(angle)) + z * math.cos(math.radians(angle))

    # Project to 2D screen
    screen_x = int(rotated_x + width // 2)
    screen_z = R2 * 2.5

    # Calculate luminance
    if screen_z > 0:
        luminance = int(11 * math.sin(math.radians(phi)))
    if luminance > 0 and screen_x >= 0 and screen_x < width and screen_z <= height:
        grid[height - int(screen_z)][screen_x] = '*' * luminance

    # Clear terminal and print grid
    os.system('cls' if os.name == 'nt' else 'clear')
    for row in grid:
        print(''.join(row))

    # Update angle for rotation
    angle += 1
    if angle >= 360:
        angle = 0

    # Control frame rate
    time.sleep(0.1)