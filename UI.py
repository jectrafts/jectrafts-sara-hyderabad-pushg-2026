import os
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0" 
import pygame
import numpy as np
import soundfile as sf
import math

import time

# Audio file path
AUDIO_FILE = 'output.mp3'
STATUS_FILE = 'ui_status.txt'

# Load initial audio data
def load_audio():
    if os.path.exists(AUDIO_FILE):
        data, samplerate = sf.read(AUDIO_FILE)
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)  # Convert to mono if stereo
        return data, samplerate
    else:
        return np.zeros(1), 44100

data, samplerate = load_audio()

# Pygame setup
pygame.init()
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sara UI - Circular Visualizer")

# Visualization settings
FPS = 60
DOT_COUNT = 200  # Main circle smoothness
EXTRA_DOT_COUNT = 300  # Extra shapes smoothness
RADIUS = 180
MAX_RADIUS_VARIATION = 60
SINE_AMPLITUDE = 100  # Base sine amplitude
SINE_FREQUENCY = 4
ROTATION_SPEED = 0.03
ALEXA_BLUE = (0, 60, 255)  # Alexa's signature shade

# Status-related settings
IDLE_RADIUS = 100
LISTENING_RADIUS = 180
LISTENING_SINE_AMPLITUDE = 50  # Reduced amplitude for listening
PROCESSING_PULSE_RATE = 0.005
PROCESSING_MIN_RADIUS = 150
PROCESSING_MAX_RADIUS = 220
chunk_size = samplerate // FPS

# Initial values
angles = np.linspace(0, 2 * math.pi, DOT_COUNT, endpoint=False)
extra_angles = np.linspace(0, 2 * math.pi, EXTRA_DOT_COUNT, endpoint=False)
rotation_angle = 0
SMOOTHING_FACTOR = 0.1
TRANSITION_SPEED = 0.1
prev_intensity = 0
frame = 0
current_status = "idle"
target_radius = IDLE_RADIUS
target_amplitude = 0

# Read status from file
def read_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'r') as f:
            return f.read().strip().lower()
    return "idle"

# Load audio if status changes to speaking
def reload_audio():
    global data, samplerate
    data, samplerate = load_audio()

def get_audio_intensity(data_chunk):
    """Calculate audio intensity for the given chunk."""
    return np.linalg.norm(data_chunk) / len(data_chunk)

def smooth_transition(current, target, speed=TRANSITION_SPEED):
    """Smooth transition between current and target values."""
    return current + (target - current) * speed

def generate_seamless_wave(intensity, frame, dot_count, amplitude):
    """Generate a seamless sine wave wrapped around the circle."""
    wave = np.sin(np.linspace(0, 2 * np.pi, dot_count) + frame * 0.1)
    wave *= intensity ** 1.2 * amplitude
    return wave

def draw_sine_wave_dots(intensity, frame, radius, amplitude):
    """Draw main sine wave pattern with seamless circular connection."""
    global rotation_angle
    radius_variation = MAX_RADIUS_VARIATION * intensity
    wave_offsets = generate_seamless_wave(intensity, frame, DOT_COUNT, amplitude)

    for i, angle in enumerate(angles):
        dynamic_radius = radius + radius_variation + wave_offsets[i]
        x = WIDTH // 2 + dynamic_radius * math.cos(angle + rotation_angle)
        y = HEIGHT // 2 + dynamic_radius * math.sin(angle + rotation_angle)
        dot_size = int(2 + 3 * intensity)
        pygame.draw.circle(screen, ALEXA_BLUE, (int(x), int(y)), dot_size)

    rotation_angle += ROTATION_SPEED

def draw_extra_shapes(intensity, frame, radius, amplitude):
    """Draw overlapping extra shapes switching between sin and cos."""
    phase_shift = frame * 0.05
    for i, angle in enumerate(extra_angles):
        sin_radius_offset = radius + (amplitude * intensity * np.sin(SINE_FREQUENCY * angle + phase_shift))
        x1 = WIDTH // 2 + sin_radius_offset * math.cos(angle)
        y1 = HEIGHT // 2 + sin_radius_offset * math.sin(angle)
        pygame.draw.circle(screen, ALEXA_BLUE, (int(x1), int(y1)), 2)

        cos_radius_offset = radius + (amplitude * intensity * np.cos(SINE_FREQUENCY * angle - phase_shift))
        x2 = WIDTH // 2 + cos_radius_offset * math.cos(angle)
        y2 = HEIGHT // 2 + cos_radius_offset * math.sin(angle)
        pygame.draw.circle(screen, ALEXA_BLUE, (int(x2), int(y2)), 2)

def draw_processing_circle(frame):
    """Draw a single pulsating circle for processing mode."""
    pulse_radius = PROCESSING_MIN_RADIUS + (PROCESSING_MAX_RADIUS - PROCESSING_MIN_RADIUS) * (
            0.5 + 0.5 * np.sin(frame * PROCESSING_PULSE_RATE * 2 * np.pi))
    pygame.draw.circle(screen, ALEXA_BLUE, (WIDTH // 2, HEIGHT // 2), int(pulse_radius), 2)

# Main loop
running = True
clock = pygame.time.Clock()

current_radius = IDLE_RADIUS
current_amplitude = 0

while running:
    # Read the current status from the text file
    new_status = read_status()

    if new_status != current_status:
        current_status = new_status
        if current_status == "speaking":
            reload_audio()
        print(f"Status updated: {current_status}")

    if current_status == "speaking":
        # Handle audio chunks when speaking (check status dynamically)
        num_chunks = len(data) // chunk_size
        for i in range(num_chunks):
            # Check status mid-loop to break if it changes
            if read_status() != "speaking":
                break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            if not running:
                break

            data_chunk = data[i * chunk_size:(i + 1) * chunk_size]
            intensity = get_audio_intensity(data_chunk)
            intensity = np.clip(intensity * 20, 0, 1)

            smoothed_intensity = SMOOTHING_FACTOR * intensity + (1 - SMOOTHING_FACTOR) * prev_intensity
            prev_intensity = smoothed_intensity

            # Smoothly transition to target values
            current_radius = smooth_transition(current_radius, RADIUS)
            current_amplitude = smooth_transition(current_amplitude, SINE_AMPLITUDE)

            screen.fill((0, 0, 0))
            draw_sine_wave_dots(smoothed_intensity, frame, current_radius, current_amplitude)
            draw_extra_shapes(smoothed_intensity, frame, current_radius, current_amplitude)
            pygame.display.flip()
            frame += 1
            clock.tick(FPS)

    elif current_status == "idle":
        target_radius = IDLE_RADIUS
        target_amplitude = 0

    elif current_status == "processing":
        target_radius = LISTENING_RADIUS
        target_amplitude = LISTENING_SINE_AMPLITUDE

    elif current_status == "listening":
        # Only draw pulsating circle without sine waves
        screen.fill((0, 0, 0))
        draw_processing_circle(frame)
        pygame.display.flip()
        frame += 1
        clock.tick(FPS)
        continue

    # Smoothly transition to target values in non-processing states
    current_radius = smooth_transition(current_radius, target_radius)
    current_amplitude = smooth_transition(current_amplitude, target_amplitude)

    # Draw normal sine waves with smooth transitions in other states
    screen.fill((0, 0, 0))
    draw_sine_wave_dots(0.3, frame, current_radius, current_amplitude)
    draw_extra_shapes(0.3, frame, current_radius, current_amplitude)
    pygame.display.flip()

    # Event handling for window close
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    frame += 1
    clock.tick(FPS)

pygame.quit()
