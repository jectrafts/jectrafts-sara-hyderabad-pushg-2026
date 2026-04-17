import customtkinter as ctk
import tkinter as tk
import time
import re

# Path to the log file
LOG_FILE = "chat_log.txt"

# Set up the main window
ctk.set_appearance_mode("dark")
root = ctk.CTk()
root.title("SARA Conversation Log")
root.geometry("700x600")

# Main frame for scrollable content
frame_container = ctk.CTkFrame(root, fg_color="#1e1e1e")
frame_container.pack(expand=True, fill="both", padx=10, pady=10)

# Create a canvas and scrollbar for scrolling
canvas = tk.Canvas(frame_container, bg="#1e1e1e", highlightthickness=0)
scrollbar = ctk.CTkScrollbar(frame_container, orientation="vertical", command=canvas.yview)
scrollable_frame = ctk.CTkFrame(canvas, fg_color="#1e1e1e")

# Configure scrolling
scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Bubble styles
def create_bubble(text, sender="sara"):
    """Creates a message bubble for user or SARA."""
    frame = ctk.CTkFrame(scrollable_frame, fg_color="#1e1e1e")
    frame.pack(anchor="e" if sender == "user" else "w", pady=5, padx=10, fill="x")

    bubble_color = "#444654" if sender == "user" else "#343541"
    text_color = "#ffffff"

    bubble = ctk.CTkLabel(
        frame,
        text=text,
        fg_color=bubble_color,
        text_color=text_color,
        corner_radius=8,
        wraplength=500,
        justify="left",
        padx=12,
        pady=8,
        font=("Arial", 12)
    )
    bubble.pack(anchor="e" if sender == "user" else "w", padx=5, pady=2)

# Code block style
# Code block style with copy button
def create_code_bubble(code_text):
    """Creates a code block bubble with copy button."""
    frame = ctk.CTkFrame(scrollable_frame, fg_color="#1e1e1e")
    frame.pack(anchor="w", pady=5, padx=10, fill="x")

    # Inner frame for code and button
    inner_frame = ctk.CTkFrame(frame, fg_color="#2e2e2e", corner_radius=8)
    inner_frame.pack(anchor="w", fill="x", padx=5, pady=2)

    # Display code
    bubble = ctk.CTkLabel(
        inner_frame,
        text=code_text,
        fg_color="#2e2e2e",
        text_color="#d1d5db",
        corner_radius=8,
        wraplength=500,
        justify="left",
        padx=12,
        pady=8,
        font=("Courier", 11)
    )
    bubble.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)

    # Copy button
    def copy_to_clipboard():
        root.clipboard_clear()
        root.clipboard_append(code_text)
        root.update()
        show_copied_label()

    copy_button = ctk.CTkButton(
        inner_frame,
        text="📋 Copy",
        command=copy_to_clipboard,
        fg_color="#3b3b3b",
        text_color="#d1d5db",
        hover_color="#4e4e4e",
        width=60,
        height=20,
        font=("Arial", 10)
    )
    copy_button.pack(side="right", padx=5, pady=5)

    # Display "Copied!" label temporarily
    def show_copied_label():
        copied_label = ctk.CTkLabel(
            inner_frame,
            text="✔️ Copied!",
            text_color="#4ade80",
            fg_color="#2e2e2e",
            font=("Arial", 10),
            padx=5
        )
        copied_label.pack(side="right", padx=(0, 5), pady=5)
        root.after(1000, copied_label.destroy)  # Remove after 1 second

# Parse and display log
def parse_and_display():
    """Continuously reads and displays new logs."""
    last_position = 0

    def update_display():
        nonlocal last_position
        try:
            with open(LOG_FILE, "r") as f:
                f.seek(last_position)
                new_lines = f.readlines()
                last_position = f.tell()

                code_block = []  # To store multiline code snippets
                inside_code_block = False
                inside_triple_backtick = False

                for line in new_lines:
                    line = line.strip()

                    # Detect CODE: block
                    if line.startswith("CODE:"):
                        inside_code_block = True
                        code_block = []
                        continue

                    # Handle end of CODE: block
                    if inside_code_block and not line:
                        inside_code_block = False
                        if code_block:
                            create_code_bubble("\n".join(code_block))
                        continue

                    # Capture CODE: block content
                    if inside_code_block:
                        code_block.append(line)

                    # Detect triple backticks block (```python or ``` or similar)
                    elif re.match(r"^```[\w]*", line):
                        inside_triple_backtick = not inside_triple_backtick
                        if not inside_triple_backtick and code_block:
                            create_code_bubble("\n".join(code_block))
                            code_block = []
                        continue

                    # Capture code inside triple backticks
                    if inside_triple_backtick:
                        code_block.append(line)

                    # Regular message handling
                    elif line.startswith("USER:"):
                        create_bubble(line.replace("USER:", "").strip(), sender="user")
                    elif line.startswith("SARA:"):
                        create_bubble(line.replace("SARA:", "").strip(), sender="sara")

                canvas.yview_moveto(1)  # Auto-scroll to the bottom

        except FileNotFoundError:
            create_bubble("Log file not found. Waiting for file to be created...", sender="sara")

        root.after(1000, update_display)

    update_display()

# Run the log parser
root.after(100, parse_and_display)
root.mainloop()