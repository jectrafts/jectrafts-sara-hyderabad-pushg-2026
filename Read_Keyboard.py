from pynput import keyboard

# Define the file name
file_name = 'status.txt'

def on_press(key):
    try:
        # Check if the key is a letter or number
        if key.char.isalnum():
            key_pressed = f'Key pressed: {key.char}'
    except AttributeError:
        # Check for spacebar
        if key == keyboard.Key.space:
            key_pressed = 'spacebar'
        # Check for function keys (F1 to F12)
        elif key in [
            keyboard.Key.f1, keyboard.Key.f2, keyboard.Key.f3, keyboard.Key.f4,
            keyboard.Key.f5, keyboard.Key.f6, keyboard.Key.f7, keyboard.Key.f8,
            keyboard.Key.f9, keyboard.Key.f10, keyboard.Key.f11, keyboard.Key.f12
        ]:
            key_pressed = f'Key pressed: {str(key).replace("Key.", "").upper()}'
        # Handle other special keys if needed
        else:
            key_pressed = f'Key pressed: {key}'

    # Print key press information to the terminal
    print(key_pressed, end='\r', flush=True)

    # Write the key press information to the file (overwrite the same line)
    with open(file_name, 'w') as file:
        file.write(key_pressed)
while True: 
    try:
        # Start listening for key presses
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
    except Exception as e:
        print ("")