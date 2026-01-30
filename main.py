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
        self.content.columnconfigure(1, weight=1)

        self.float_vcmd = (self.root.register(_validate_float), "%P")
        self.int_vcmd = (self.root.register(_validate_int), "%P")

        self._build_buttons()
        self._build_toggle_buttons()
        self._build_text_fields()
        self._build_inputs()
        self._build_bottom_integer()

    def _build_buttons(self) -> None:
        buttons_frame = ttk.LabelFrame(self.content, text="Aktionen", padding=10)
        buttons_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        for i in range(3):
            buttons_frame.columnconfigure(i, weight=1)

        ttk.Button(buttons_frame, text="Button 1").grid(row=0, column=0, padx=6, sticky="ew")
        ttk.Button(buttons_frame, text="Button 2").grid(row=0, column=1, padx=6, sticky="ew")
        ttk.Button(buttons_frame, text="Button 3").grid(row=0, column=2, padx=6, sticky="ew")

    def _build_toggle_buttons(self) -> None:
        toggle_frame = ttk.LabelFrame(self.content, text="Optionen", padding=10)
        toggle_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        toggle_frame.columnconfigure((0, 1), weight=1)

        green_mode = tk.BooleanVar(value=False)
        operation_mode = tk.BooleanVar(value=False)

        ttk.Checkbutton(
            toggle_frame,
            text="Green Mode",
            variable=green_mode,
            onvalue=True,
            offvalue=False,
        ).grid(row=0, column=0, padx=6, sticky="ew")
        ttk.Checkbutton(
            toggle_frame,
            text="Operation Mode",
            variable=operation_mode,
            onvalue=True,
            offvalue=False,
        ).grid(row=0, column=1, padx=6, sticky="ew")

    def _build_text_fields(self) -> None:
        text_frame = ttk.LabelFrame(self.content, text="Textfelder", padding=10)
        text_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 12))
        text_frame.columnconfigure(1, weight=1)

        for i in range(5):
            ttk.Label(text_frame, text=f"Textfeld {i + 1}:").grid(
                row=i, column=0, sticky="w", pady=4
            )
            ttk.Entry(text_frame).grid(row=i, column=1, sticky="ew", pady=4)

    def _build_inputs(self) -> None:
        inputs_frame = ttk.LabelFrame(self.content, text="Eingabefelder", padding=10)
        inputs_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        inputs_frame.columnconfigure(1, weight=1)

        ttk.Label(inputs_frame, text="Float 1:").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(inputs_frame, validate="key", validatecommand=self.float_vcmd).grid(
            row=0, column=1, sticky="ew", pady=4
        )

        ttk.Label(inputs_frame, text="Float 2:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(inputs_frame, validate="key", validatecommand=self.float_vcmd).grid(
            row=1, column=1, sticky="ew", pady=4
        )

        ttk.Label(inputs_frame, text="Integer:").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(inputs_frame, validate="key", validatecommand=self.int_vcmd).grid(
            row=2, column=1, sticky="ew", pady=4
        )

    def _build_bottom_integer(self) -> None:
        bottom_frame = ttk.Frame(self.content)
        bottom_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        bottom_frame.columnconfigure(1, weight=1)

        ttk.Label(bottom_frame, text="Ganzzahl (unten):").grid(
            row=0, column=0, sticky="w", pady=4
        )
        ttk.Entry(bottom_frame, validate="key", validatecommand=self.int_vcmd).grid(
            row=0, column=1, sticky="ew", pady=4
        )


def main() -> None:
    root = tk.Tk()
    TestHMIApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
