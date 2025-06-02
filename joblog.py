import traceback

try:
    import tkinter as tk
    from tkinter import simpledialog, messagebox, Toplevel, Listbox, Scrollbar
    import keyboard
    import os
    from pystray import Icon, Menu, MenuItem
    from PIL import Image
    import threading

    from datetime import datetime, timedelta
    import calendar

    current_month = datetime.now()

    # Create a hidden Tkinter root window
    root = tk.Tk()
    root.withdraw()

    # Helper function to get the current month's log filename
    def get_log_filename(month_str=None):
        if not month_str:
            month_str = datetime.now().strftime('%Y%m')
        os.makedirs("logs", exist_ok=True)  # Ensure folder exists
        return os.path.join("logs", f"log{month_str}.txt")

    # Logs a new entry with description, decimal number, and timestamp
    def log_entry():
        root.after(0, _log_entry)

    def _log_entry():

        global current_month
        current_month = datetime.now().replace(day=1)

        description = simpledialog.askstring("Input", "Enter description:", parent=root)
        if description is None:
            return

        number = simpledialog.askfloat("Input", "Enter decimal number:", parent=root)
        if number is None:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file = get_log_filename(current_month.strftime("%Y%m"))

        with open(log_file, "a") as file:
            file.write(f"{timestamp} - {description} - {number}\n")

    current_month = datetime.now().replace(day=1)  # Always 1st of month

    # Opens a window to select and edit an existing log entry
    def edit_log_entry():
        root.after(0, _edit_log_entry)

    def _edit_log_entry():
        global current_month

        class FocusedQueryString(simpledialog._QueryString):
            def body(self, master):
                entry = super().body(master)
                self.after(50, lambda: entry.focus_force())  # Ensure input gets focus
                return entry

        def on_select():
            try:
                selected_index = listbox.curselection()[0]
                selected_entry = lines[selected_index]

                try:
                    existing_timestamp, existing_description, existing_number = selected_entry.strip().split(" - ", 2)
                except ValueError:
                    messagebox.showerror("Error", "Failed to parse the selected entry.", parent=root)
                    selection_window.destroy()
                    return

                new_timestamp_dialog = FocusedQueryString(
                    parent=selection_window,
                    title="Edit Timestamp",
                    prompt="Edit timestamp (YYYY-MM-DD HH:MM:SS):",
                    initialvalue=existing_timestamp
                )
                new_timestamp = getattr(new_timestamp_dialog, "result", None)

                if new_timestamp is None:
                    selection_window.destroy()
                    return

                try:
                    datetime.strptime(new_timestamp, "%Y-%m-%d %H:%M:%S")  # Validate format
                except ValueError:
                    messagebox.showerror("Invalid Timestamp", "Timestamp must be in the format: YYYY-MM-DD HH:MM:SS", parent=root)
                    return

                selection_window.lift() 
                selection_window.focus_force()

                new_description_dialog = FocusedQueryString(
                    parent=selection_window,
                    title="Edit Description",
                    prompt="Edit description:",
                    initialvalue=existing_description
                )
                new_description = new_description_dialog.result

                if new_description is None:
                    selection_window.destroy()
                    return

                selection_window.lift() 
                selection_window.focus_force()

                new_number_dialog = FocusedQueryString(
                    parent=selection_window,
                    title="Edit Number",
                    prompt="Edit number:",
                    initialvalue=float(existing_number)
                )
                new_number = new_number_dialog.result

                if new_number is None:
                    selection_window.destroy()
                    return

                updated_entry = f"{new_timestamp} - {new_description} - {new_number}\n"
                lines[selected_index] = updated_entry

                lines.reverse()
                month_file = get_log_filename(current_month.strftime("%Y%m"))
                with open(month_file, "w") as file:
                    file.writelines(lines)

                messagebox.showinfo("Success", "Entry updated successfully!", parent=root)
                refresh_listbox()

            except IndexError:
                messagebox.showinfo("No Selection", "Please select an entry to edit.", parent=root)
    
        lines = []

        # Function to reorder entries by timestamp
        def reorder_entries_by_timestamp():
            import re

            # Extract valid entries with timestamp
            entry_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (.+?) - ([\d.]+)$")
            parsed = []
            for line in lines:
                match = entry_pattern.match(line.strip())
                if match:
                    ts = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
                    parsed.append((ts, line.strip()))

            # Sort by datetime ascending
            parsed.sort(key=lambda x: x[0],reverse=True)

            # Update the listbox and the lines
            lines.clear()
            lines.extend([entry[1] + "\n" for entry in parsed])

            max_len = max(len(f"{float(line.strip().split(' - ')[2]):.1f}")
              for line in lines if " - " in line and line.strip().split(" - ")[2].replace('.', '', 1).isdigit())

            listbox.delete(0, tk.END)
            for entry in lines:
                parts = entry.strip().split(" - ", 2)
                if len(parts) == 3:
                    timestamp, description, number = parts
                    num_str = f"{float(number):.1f}"
                    if float(number) < 10:
                        num_str = "  " + num_str
                    padded_number = num_str.rjust(max_len)
                    listbox.insert(tk.END, f"{timestamp} - {padded_number} - {description}")
                else:
                    listbox.insert(tk.END, entry.strip())

        def update_middle_column_count():
            count = 0
            for line in lines:
                parts = line.strip().split(" - ")
                if len(parts) >= 3 and parts[2].strip().replace('.', '', 1).isdigit():  # Ensure middle column is a valid number
                    count += 1
            count_label.config(text=f"Items: {count}")

        def update_middle_column_sum():
            total = 0.0
            for line in lines:
                parts = line.strip().split(" - ")
                if len(parts) == 3 and parts[2].strip().replace('.', '', 1).isdigit():  # Ensure middle column is a valid number
                    total += float(parts[2].strip())  # Add the number to the total
            sum_label.config(text=f"Total Hours: {total:.1f}")  # Display the total

        def refresh_listbox():
            month_file = get_log_filename(current_month.strftime("%Y%m"))
            if os.path.exists(month_file):
                with open(month_file, "r") as file:
                    refreshed_lines = file.readlines()

                lines.clear()
                lines.extend(refreshed_lines)
                reorder_entries_by_timestamp()  # Handles sorting and inserting
                update_middle_column_count()
                update_middle_column_sum()

        log_file = get_log_filename(current_month.strftime("%Y%m"))

        selection_window = Toplevel(root)
        selection_window.title("Log Entries")
        selection_window.geometry("800x300")

        scrollbar = Scrollbar(selection_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = Listbox(selection_window, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set)
        listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        count_label = tk.Label(selection_window, text="... : 0")
        count_label.pack()
        sum_label = tk.Label(selection_window, text="... : 0")
        sum_label.pack()

        # Check if the log file exists and has content
        if os.path.exists(log_file) and os.stat(log_file).st_size > 0:
            refresh_listbox()
        else:
            # If the log file is empty, show a placeholder message
            listbox.insert(tk.END, "No entries available. Add a new entry.")

        # Add buttons for new entries (without and with time control)
        def log_new_entry():
            log_entry()  # Use the existing log_entry function for normal log entry

        class FocusedQueryString(simpledialog._QueryString):
            def body(self, master):
                entry = super().body(master)
                self.after(50, lambda: entry.focus_force())  # Ensure input gets focus
                return entry

        def log_new_entry_with_time():
            # Prompt user to select a timestamp before entering the description and number      
            default_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            timestamp_dialog = FocusedQueryString(
                "Input",
                "Enter timestamp (YYYY-MM-DD HH:MM:SS):",
                initialvalue=default_ts,
                parent=selection_window
            )
            timestamp = timestamp_dialog.result

            if not timestamp:
                return  # If no timestamp entered, do nothing
    
            try:
                datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")  # Validate timestamp format
            except ValueError:
                messagebox.showerror("Invalid Timestamp", "Timestamp must be in the format: YYYY-MM-DD HH:MM:SS", parent=root)
                return

            description_dialog = FocusedQueryString("Input", "Enter description:", parent=selection_window)
            description = description_dialog.result

            if description is None:
                return

            number_dialog = FocusedQueryString(
                parent=selection_window,
                title="Edit Number",
                prompt="Edit number:",
                initialvalue=0
            )
            number = number_dialog.result      
        
            if number is None:
                return

            log_file = get_log_filename(current_month.strftime("%Y%m"))
            with open(log_file, "a") as file:
                file.write(f"{timestamp} - {description} - {number}\n")

            messagebox.showinfo("Success", "New entry logged with specified timestamp!", parent=root)
            refresh_listbox()


    

        nav_frame = tk.Frame(selection_window)
        nav_frame.pack(pady=5)

        month_label = tk.Label(
            nav_frame,
            text=current_month.strftime("%B %Y"),
            width=20,  # Adjust width as needed
            font=("Courier New", 12)  # Monospaced font
        )
    
        month_label.pack(side=tk.LEFT, padx=10)

        def change_month(delta):
            global current_month
            if delta == 1:
                # Move forward 31 days and set to the first of the new month
                new_month = current_month + timedelta(days=31)
            elif delta == -1:
                # Move backward 28 days and set to the first of the previous month
                new_month = current_month - timedelta(days=28)
    
            # Set the day to the 1st of the new month
            current_month = new_month.replace(day=1)

            # Update the month label in the UI
            month_label.config(text=current_month.strftime("%B %Y"))

            # Refresh the listbox to show the log for the new month
            refresh_listbox()

        prev_button = tk.Button(nav_frame, text="<", command=lambda: change_month(-1))
        prev_button.pack(side=tk.LEFT)

        next_button = tk.Button(nav_frame, text=">", command=lambda: change_month(1))
        next_button.pack(side=tk.LEFT)

        # Create button frame to hold buttons
        button_frame = tk.Frame(selection_window)
        button_frame.pack(pady=10)

        # Only show Edit button if there are actual entries
        if lines:
            with open(log_file, "r") as file:
                raw_lines = [line.strip() for line in file if line.strip()]
            if raw_lines:
                edit_button = tk.Button(button_frame, text="Edit Selected Entry", command=on_select)
                edit_button.pack(side=tk.LEFT, padx=5)
                reorder_button = tk.Button(button_frame, text="Reorder by Timestamp", command=reorder_entries_by_timestamp)
                reorder_button.pack(side=tk.LEFT, padx=5)

        # Always show new entry buttons
        log_button = tk.Button(button_frame, text="Log New Entry", command=log_new_entry)
        log_button.pack(side=tk.LEFT, padx=5)

        log_with_time_button = tk.Button(button_frame, text="Log New Entry with Time Control", command=log_new_entry_with_time)
        log_with_time_button.pack(side=tk.LEFT, padx=5)


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
            MenuItem("Read/Edit Log Entries", edit_log_entry),
            MenuItem("Exit", exit_app)
        )

        icon = Icon("log_app", icon_image, "Log App", menu)

        # Start the tray icon in a separate thread so it doesn’t block
        threading.Thread(target=icon.run, daemon=True).start()

    # Hotkeys
    keyboard.add_hotkey("ctrl+alt+l", log_entry)
    keyboard.add_hotkey("ctrl+alt+r", edit_log_entry)

    # Start the system tray icon
    setup_tray_icon()

    # Keep the Tkinter event loop running in the background
    root.mainloop()
except Exception:
    traceback.print_exc()
    input("Press Enter to exit...")