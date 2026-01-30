import tkinter as tk
from tkinter import ttk


def _validate_float(text: str) -> bool:
    if text == "" or text == "-" or text == "." or text == "-.":
        return True
    try:
        float(text)
        return True
    except ValueError:
        return False


def _validate_int(text: str) -> bool:
    if text == "" or text == "-":
        return True
    try:
        int(text)
        return True
    except ValueError:
        return False


class TestHMIApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("TestHMI")
        self.root.geometry("720x560")

        self.content = ttk.Frame(self.root, padding=16)
        self.content.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        for col in range(4):
            self.content.columnconfigure(col, weight=1)

        self.float_vcmd = (self.root.register(_validate_float), "%P")
        self.int_vcmd = (self.root.register(_validate_int), "%P")

        self._build_layout()

    def _build_layout(self) -> None:
        ttk.Label(self.content, text="Nummer").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Entry(self.content, validate="key", validatecommand=self.int_vcmd).grid(
            row=0, column=1, sticky="ew", padx=(8, 12), pady=6
        )
        ttk.Button(self.content, text="ZUweisen").grid(
            row=0, column=2, sticky="ew", pady=6
        )

        ttk.Label(self.content, text="Mode").grid(row=1, column=0, sticky="w", pady=6)
        green_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.content,
            text="",
            variable=green_mode,
        ).grid(row=1, column=1, sticky="w", pady=6)
        ttk.Label(self.content, text="Green Mode").grid(
            row=1, column=2, sticky="w", pady=6
        )

        operation_mode = tk.StringVar(value="mode1")
        ttk.Radiobutton(
            self.content,
            text="Operation Mode 1",
            value="mode1",
            variable=operation_mode,
        ).grid(row=2, column=1, sticky="w", pady=4)
        ttk.Radiobutton(
            self.content,
            text="Operation Mode 2",
            value="mode2",
            variable=operation_mode,
        ).grid(row=3, column=1, sticky="w", pady=4)

        ttk.Label(self.content, text="Nummer").grid(row=4, column=0, sticky="w", pady=6)
        ttk.Entry(self.content, validate="key", validatecommand=self.int_vcmd).grid(
            row=4, column=1, sticky="ew", padx=(8, 12), pady=6
        )
        ttk.Button(self.content, text="Button 2").grid(
            row=4, column=2, sticky="ew", pady=6, padx=(0, 8)
        )
        ttk.Button(self.content, text="Button 3").grid(
            row=4, column=3, sticky="ew", pady=6
        )


def main() -> None:
    root = tk.Tk()
    TestHMIApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
