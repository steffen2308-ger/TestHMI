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


def main() -> None:
    root = tk.Tk()
    root.title("TestHMI")
    root.geometry("640x420")

    content = ttk.Frame(root, padding=16)
    content.grid(row=0, column=0, sticky="nsew")

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    content.columnconfigure(1, weight=1)

    buttons_frame = ttk.LabelFrame(content, text="Aktionen", padding=10)
    buttons_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
    for i in range(3):
        buttons_frame.columnconfigure(i, weight=1)

    ttk.Button(buttons_frame, text="Button 1").grid(row=0, column=0, padx=6, sticky="ew")
    ttk.Button(buttons_frame, text="Button 2").grid(row=0, column=1, padx=6, sticky="ew")
    ttk.Button(buttons_frame, text="Button 3").grid(row=0, column=2, padx=6, sticky="ew")

    radio_frame = ttk.LabelFrame(content, text="Modus", padding=10)
    radio_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))

    radio_value = tk.StringVar(value="A")
    ttk.Radiobutton(radio_frame, text="Option A", variable=radio_value, value="A").grid(
        row=0, column=0, padx=6, sticky="w"
    )
    ttk.Radiobutton(radio_frame, text="Option B", variable=radio_value, value="B").grid(
        row=0, column=1, padx=6, sticky="w"
    )

    text_frame = ttk.LabelFrame(content, text="Textfelder", padding=10)
    text_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 12))
    text_frame.columnconfigure(1, weight=1)

    for i in range(5):
        ttk.Label(text_frame, text=f"Textfeld {i + 1}:").grid(row=i, column=0, sticky="w", pady=4)
        ttk.Entry(text_frame).grid(row=i, column=1, sticky="ew", pady=4)

    inputs_frame = ttk.LabelFrame(content, text="Eingabefelder", padding=10)
    inputs_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
    inputs_frame.columnconfigure(1, weight=1)

    float_vcmd = (root.register(_validate_float), "%P")
    int_vcmd = (root.register(_validate_int), "%P")

    ttk.Label(inputs_frame, text="Float 1:").grid(row=0, column=0, sticky="w", pady=4)
    ttk.Entry(inputs_frame, validate="key", validatecommand=float_vcmd).grid(
        row=0, column=1, sticky="ew", pady=4
    )

    ttk.Label(inputs_frame, text="Float 2:").grid(row=1, column=0, sticky="w", pady=4)
    ttk.Entry(inputs_frame, validate="key", validatecommand=float_vcmd).grid(
        row=1, column=1, sticky="ew", pady=4
    )

    ttk.Label(inputs_frame, text="Integer:").grid(row=2, column=0, sticky="w", pady=4)
    ttk.Entry(inputs_frame, validate="key", validatecommand=int_vcmd).grid(
        row=2, column=1, sticky="ew", pady=4
    )

    root.mainloop()


if __name__ == "__main__":
    main()
