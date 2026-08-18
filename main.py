import pyrealsense2 as rs
import queue
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

SCALE = 2000

class T265GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("T265 Letter Recognizer")

        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        controls = ttk.Frame(root)
        controls.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(controls, text="Start drawing", command=self.start_drawing).pack(side=tk.LEFT)
        ttk.Button(controls, text="Stop drawing", command=self.stop_drawing).pack(side=tk.LEFT)
        ttk.Button(controls, text="Clear drawing", command=self.clear).pack(side=tk.LEFT)
        ttk.Button(controls, text="Save drawing", command=self.save_drawing).pack(side=tk.LEFT)
        ttk.Button(controls, text="Load drawing", command=self.load_drawing).pack(side=tk.LEFT)

        self.camera_status = ttk.Label(controls, text="Starting camera.")
        self.camera_status.pack(side=tk.LEFT)

        self.camera_data = ttk.Label(controls, text="No data.")
        self.camera_data.pack(side=tk.LEFT)

        self.pose_queue = queue.Queue()
        self.stop_event = threading.Event()

        self.drawing = False
        self.origin = None
        self.last_canvas_point = None
        self.points = []
        self.lines = []
        self.pen_cursor = None

        self.camera_thread = threading.Thread(target=self.camera_loop)
        self.camera_thread.start()

        self.root.after(20, self.update_gui)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def camera_loop(self):
        pipe = rs.pipeline()
        cfg = rs.config()
        cfg.enable_stream(rs.stream.pose)

        try:
            pipe.start(cfg)
            self.pose_queue.put(("status", "Camera connected."))

            while not self.stop_event.is_set():
                frames = pipe.wait_for_frames()
                pose_frame = frames.get_pose_frame()

                if not pose_frame:
                    continue

                pose = pose_frame.get_pose_data()

                x = pose.translation.x
                y = pose.translation.y
                z = pose.translation.z

                self.pose_queue.put(("pose", (x, y, z)))

        except Exception as e:
            self.pose_queue.put(("status", f"Camera error: {e}"))

        finally:
            pipe.stop()

    def start_drawing(self):
        self.drawing = True
        self.points = []
        self.camera_status.config(text="Drawing.")

    def stop_drawing(self):
        self.drawing = False
        self.last_canvas_point = None

        if self.points:
            self.lines.append(self.points)

        self.camera_data.config(text=f"Captured {len(self.points)} points.")
        self.camera_status.config(text="Stopped.")

    def save_drawing(self):
        path = filedialog.asksaveasfilename(defaultextension=".drawing")
        if path:
            with open(path, "w") as f:
                for line in self.lines:
                    l = " ".join(f"{x},{y}" for x, y in line)
                    f.write(l + "\n")

    def load_drawing(self):
        path = filedialog.askopenfilename(filetypes=[("Drawings", "*.drawing")])
        if not path:
            return

        with open(path, "r") as f:
            for line in f:
                points = []
                for p in line.split():
                    x, y = p.split(",")
                    points.append((float(x), float(y)))

                for i in range(1, len(points)):
                    dx1, dy1 = points[i - 1]
                    dx2, dy2 = points[i]
                
                    canvas_width = self.canvas.winfo_width()
                    canvas_height = self.canvas.winfo_height()
                
                    px1 = canvas_width / 2 + dx1 * SCALE
                    py1 = canvas_height / 2 - dy1 * SCALE
                    px2 = canvas_width / 2 + dx2 * SCALE
                    py2 = canvas_height / 2 - dy2 * SCALE

                    self.points.append((dx1, dy1))
                    self.points.append((dx2, dy2))
                    
                    self.canvas.create_line(px1, py1, px2, py2, fill="Black", width=4)

                self.lines.append(points)
                

    def clear(self):
        self.canvas.delete("all")
        self.origin = None
        self.last_canvas_point = None
        self.points = []
        self.lines = []
        self.pen_cursor = None
        self.camera_status.config(text="Cleared.")
        self.camera_data.config(text="No data.")

    def update_gui(self):
        while not self.pose_queue.empty():
            message_type, data = self.pose_queue.get()

            if message_type == "status":
                self.camera_status.config(text=data)
            elif message_type == "pose":
                self.handle_pose(data)

        self.root.after(20, self.update_gui)

    def handle_pose(self, pose):
        x, y, z = pose

        if self.origin is None:
            self.origin = (x, y, z)

        ox, oy, oz = self.origin

        dx = z - oz
        dy = y - oy

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        px = canvas_width / 2 + dx * SCALE
        py = canvas_height / 2 - dy * SCALE

        r = 4
        if self.pen_cursor is None:
            self.pen_cursor = self.canvas.create_oval(px - r, py - r, px + r, py + r, fill="blue")
        else:
            self.canvas.coords(self.pen_cursor, px - r, py - r, px + r, py + r)

        if not self.drawing:
            return
        
        if self.last_canvas_point is not None:
            lx, ly = self.last_canvas_point
            self.canvas.create_line(lx, ly, px, py, fill="black", width=4)

        self.points.append((dx, dy))
        self.last_canvas_point = (px, py)

        self.camera_data.config(text=f"Polling {len(self.points)} points.")

    def close(self):
        self.stop_event.set()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = T265GUI(root)
    root.mainloop()