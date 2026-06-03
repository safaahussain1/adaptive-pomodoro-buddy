"""
Floating always-on-top coaching overlay.

Run in a separate terminal alongside tracker.py:
    python overlay.py

It reads the latest coaching message from .overlay_msg (written by tracker.py)
and displays it in a small semi-transparent window that stays above all other apps.
Press H to hide/show, Q to quit.
"""

import tkinter as tk
import threading
import time
import os
import json

MSG_FILE = ".overlay_msg"
POLL_INTERVAL_MS = 1000   # check for new messages every second


class CoachOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("")
        self.root.overrideredirect(True)        # no title bar
        self.root.attributes("-topmost", True)  # always on top
        self.root.attributes("-alpha", 0.88)    # slight transparency
        self.root.configure(bg="#1a1a2e")

        # Position: bottom-right corner
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w, h = 380, 130
        x = sw - w - 20
        y = sh - h - 60
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # Header bar
        header_frame = tk.Frame(self.root, bg="#16213e", pady=4)
        header_frame.pack(fill="x")
        self.title_var = tk.StringVar(value="Pomodoro Buddy")
        tk.Label(header_frame, textvariable=self.title_var,
                 bg="#16213e", fg="#e94560", font=("Helvetica", 10, "bold")).pack(side="left", padx=10)
        tk.Label(header_frame, text="[H] hide  [Q] quit",
                 bg="#16213e", fg="#888", font=("Helvetica", 8)).pack(side="right", padx=8)

        # Message area
        self.msg_var = tk.StringVar(value="Waiting for session to start...")
        msg_label = tk.Label(
            self.root, textvariable=self.msg_var,
            bg="#1a1a2e", fg="#eaeaea",
            font=("Helvetica", 11),
            wraplength=355, justify="left",
            padx=12, pady=8,
        )
        msg_label.pack(fill="both", expand=True)

        # Focus / timer strip
        self.stats_var = tk.StringVar(value="")
        tk.Label(self.root, textvariable=self.stats_var,
                 bg="#0f3460", fg="#53d8fb",
                 font=("Helvetica", 9), padx=10, pady=3).pack(fill="x")

        # Drag support
        self._drag_x = 0
        self._drag_y = 0
        self.root.bind("<ButtonPress-1>", self._on_press)
        self.root.bind("<B1-Motion>", self._on_drag)

        # Key bindings
        self.hidden = False
        self.root.bind("<Key-h>", self._toggle_hide)
        self.root.bind("<Key-H>", self._toggle_hide)
        self.root.bind("<Key-q>", lambda _: self.root.destroy())
        self.root.bind("<Key-Q>", lambda _: self.root.destroy())
        self.root.focus_force()

        self._last_msg = ""
        self.root.after(POLL_INTERVAL_MS, self._poll)

    def _on_press(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _toggle_hide(self, _=None):
        self.hidden = not self.hidden
        if self.hidden:
            self.root.withdraw()
            # Show a tiny restore button
            self._restore_btn = tk.Toplevel()
            self._restore_btn.overrideredirect(True)
            self._restore_btn.attributes("-topmost", True)
            self._restore_btn.attributes("-alpha", 0.8)
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self._restore_btn.geometry(f"90x24+{sw-100}+{sh-50}")
            btn = tk.Button(self._restore_btn, text="Show Coach",
                            bg="#e94560", fg="white", font=("Helvetica", 9),
                            relief="flat", command=self._toggle_hide)
            btn.pack(fill="both", expand=True)
        else:
            if hasattr(self, "_restore_btn"):
                self._restore_btn.destroy()
            self.root.deiconify()

    def _poll(self):
        try:
            if os.path.exists(MSG_FILE):
                with open(MSG_FILE) as f:
                    data = json.load(f)
                msg = data.get("message", "")
                trigger = data.get("trigger", "")
                stats = data.get("stats", "")
                if msg != self._last_msg and msg:
                    self._last_msg = msg
                    title = data.get("title", "Pomodoro Buddy")
                    self.title_var.set(title)
                    self.msg_var.set(msg)
                    # Flash background briefly
                    self.root.configure(bg="#2d1b33")
                    self.root.after(800, lambda: self.root.configure(bg="#1a1a2e"))
                    if self.hidden:
                        self._toggle_hide()  # pop up on new message
                if stats:
                    self.stats_var.set(stats)
        except Exception:
            pass
        self.root.after(POLL_INTERVAL_MS, self._poll)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    CoachOverlay().run()
