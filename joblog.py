import tkinter as tk
from tkinter import simpledialog, messagebox, Toplevel, Listbox, Scrollbar
import keyboard
import datetime
import os
from pystray import Icon, Menu, MenuItem
from PIL import Image
import threading

# Create a hidden Tkinter root window
root = tk.Tk()
root.withdraw()

# Helper function to get the current month's log filename
def get_log_filename():
    now = datetime.datetime.now()
    return f"log{now.strftime('%Y%m')}.txt"

# Logs a new entry with description, decimal number, and timestamp
def log_entry():
    root.after(0, _log_entry)

def _log_entry():
    description = simpledialog.askstring("Input", "Enter description:", parent=root)
    if description is None:
        return

    number = simpledialog.askfloat("Input", "Enter decimal number:", parent=root)
    if number is None:
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = get_log_filename()

    with open(log_file, "a") as file:
        file.write(f"{timestamp} - {description} - {number}\n")

# Reads and displays the current month's log file in reverse order
def read_log():
    root.after(0, _read_log)

def _read_log():
    log_file = get_log_filename()

    if not os.path.exists(log_file):
        messagebox.showinfo("Log Viewer", "No log entries found for this month.", parent=root)
        return

    with open(log_file, "r") as file:
        lines = file.readlines()

    if not lines:
        messagebox.showinfo("Log Viewer", "The log file is empty.", parent=root)
        return

    lines.reverse()
    log_content = "".join(lines)
    messagebox.showinfo("Log Viewer", log_content, parent=root)

# Opens a window to select and edit an existing log entry
def edit_log_entry():
    root.after(0, _edit_log_entry)

def _edit_log_entry():
    log_file = get_log_filename()

    if not os.path.exists(log_file):
        messagebox.showinfo("Edit Log Entry", "No log entries found for this month.", parent=root)
        return

    with open(log_file, "r") as file:
        lines = file.readlines()

    if not lines:
        messagebox.showinfo("Edit Log Entry", "The log file is empty.", parent=root)
        return

    lines.reverse()

    selection_window = Toplevel(root)
    selection_window.title("Select Entry to Edit")
    selection_window.geometry("400x300")

    scrollbar = Scrollbar(selection_window)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    listbox = Listbox(selection_window, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set)
    for line in lines:
        listbox.insert(tk.END, line.strip())

    listbox.pack(fill=tk.BOTH, expand=True)
    scrollbar.config(command=listbox.yview)

    def on_select():
        try:
            selected_index = listbox.curselection()[0]
            selected_entry = lines[selected_index]

            try:
                timestamp, description, number = selected_entry.strip().split(" - ", 2)
            except ValueError:
                messagebox.showerror("Error", "Failed to parse the selected entry.", parent=root)
                selection_window.destroy()
                return

            new_description = simpledialog.askstring("Edit Description", "Edit description:", initialvalue=description, parent=root)
            if new_description is None:
                selection_window.destroy()
                return

            new_number = simpledialog.askfloat("Edit Number", "Edit number:", initialvalue=float(number), parent=root)
            if new_number is None:
                selection_window.destroy()
                return

            updated_entry = f"{timestamp} - {new_description} - {new_number}\n"
            lines[selected_index] = updated_entry

            lines.reverse()
            with open(log_file, "w") as file:
                file.writelines(lines)

            messagebox.showinfo("Success", "Entry updated successfully!", parent=root)
            selection_window.destroy()

        except IndexError:
            messagebox.showinfo("No Selection", "Please select an entry to edit.", parent=root)

    edit_button = tk.Button(selection_window, text="Edit Selected Entry", command=on_select)
    edit_button.pack(pady=5)

# Shows a message indicating the app is running
def show_command_window():
    root.after(0, _show_command_window)

def _show_command_window():
    messagebox.showinfo("Log App", "The logging app is running in the background.", parent=root)

# Exits the app and closes the system tray icon
def exit_app(icon, item):
    icon.stop()
    root.quit()
    os._exit(0)

# Sets up the system tray icon and menu
def setup_tray_icon():
    icon_image = Image.new('RGB', (64, 64), (0, 128, 255))

    menu = Menu(
        MenuItem("Show Command Window", show_command_window),
        MenuItem("Log New Entry", log_entry),
        MenuItem("Open Log File", read_log),
        MenuItem("Edit Log Entry", edit_log_entry),
        MenuItem("Exit", exit_app)
    )

    icon = Icon("log_app", icon_image, "Log App", menu)

    # Start the tray icon in a separate thread so it doesn’t block
    threading.Thread(target=icon.run, daemon=True).start()

# Hotkeys
keyboard.add_hotkey("ctrl+alt+l", log_entry)
keyboard.add_hotkey("ctrl+alt+r", read_log)

# Start the system tray icon
setup_tray_icon()

# Keep the Tkinter event loop running in the background
root.mainloop()
