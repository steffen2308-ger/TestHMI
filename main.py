import json
import threading
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime, timezone
from tkinter import ttk

import grpc
from google.protobuf import empty_pb2
from google.protobuf import timestamp_pb2

from generated import openWriteStreamZuweisung_pb2
from generated import testhmi_pb2
from generated import testhmi_pb2_grpc


def _validate_float(text: str) -> bool:
    """Allow intermediate float input while the user types."""
    if text == "" or text == "-" or text == "." or text == "-.":
        return True
    try:
        float(text)
        return True
    except ValueError:
        return False


def _validate_int(text: str) -> bool:
    """Allow intermediate int input while the user types."""
    if text == "" or text == "-":
        return True
    try:
        int(text)
        return True
    except ValueError:
        return False


@dataclass(frozen=True)
class GrpcConfig:
    address: str = "localhost:50051"


def load_grpc_config(path: str = "grpc_config.json") -> GrpcConfig:
    """Load the gRPC address from JSON, falling back to defaults on errors."""
    default_config = GrpcConfig()
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return default_config
    except (json.JSONDecodeError, OSError):
        return default_config
    address = data.get("address", default_config.address)
    return GrpcConfig(address=address)


class TestHMIApp:
    def __init__(self, root: tk.Tk, grpc_config: GrpcConfig) -> None:
        """Initialize the UI, background threads, and gRPC client."""
        self.root = root
        self.root.title("TestHMI")

        self.content = ttk.Frame(self.root, padding=16)
        self.content.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        for col in range(4):
            self.content.columnconfigure(col, weight=1)

        self.float_vcmd = (self.root.register(_validate_float), "%P")
        self.int_vcmd = (self.root.register(_validate_int), "%P")

        # UI state variables.
        self.green_mode = tk.BooleanVar(value=False)
        self._zuweisung_stop_event = threading.Event()
        self._zuweisung_thread: threading.Thread | None = None
        self._aktion_stop_event = threading.Event()
        self._aktion_thread: threading.Thread | None = None
        self._aktion_stream_started = False
        self._status_stop_event = threading.Event()
        self._status_thread: threading.Thread | None = None
        self.grpc_client = GrpcClient(address=grpc_config.address)
        self.zuweisung_result_var = tk.StringVar(value="")
        self.status_message_var = tk.StringVar(value="")
        self.output_message_var = tk.StringVar(value="")
        self.operation_mode = tk.StringVar(value="mode1")
        self._stream_wait_timeout = 5.0

        self._build_layout()
        self._fit_window_to_content()
        # Always keep the status stream running in the background.
        self._start_status_stream()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self) -> None:
        """Construct the visible UI and wire up callbacks."""
        # Zuweisung row (writes a stream when green mode is enabled).
        ttk.Label(self.content, text="Nummer").grid(row=0, column=0, sticky="w", pady=6)
        self.assign_number_entry = ttk.Entry(
            self.content,
            validate="key",
            validatecommand=self.int_vcmd,
        )
        self.assign_number_entry.insert(0, "1234")
        self.assign_number_entry.grid(
            row=0, column=1, sticky="ew", padx=(8, 12), pady=6
        )
        ttk.Button(
            self.content,
            text="ZUweisen",
            command=self._on_assign_clicked,
        ).grid(row=0, column=2, sticky="ew", pady=6)
        ttk.Entry(
            self.content,
            textvariable=self.zuweisung_result_var,
            state="readonly",
        ).grid(row=0, column=3, sticky="ew", pady=6, padx=(8, 0))

        # Mode selection.
        ttk.Label(self.content, text="Mode").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Checkbutton(
            self.content,
            text="Green Mode",
            variable=self.green_mode,
            command=self._on_green_mode_changed,
        ).grid(row=1, column=1, sticky="w", pady=6)

        ttk.Label(self.content, text="Operation2").grid(
            row=2, column=0, sticky="w", pady=4
        )
        ttk.Radiobutton(
            self.content,
            text="Operation Mode 1",
            value="mode1",
            variable=self.operation_mode,
            command=self._on_operation_changed,
        ).grid(row=2, column=1, sticky="w", pady=4)
        ttk.Radiobutton(
            self.content,
            text="Operation Mode 2",
            value="mode2",
            variable=self.operation_mode,
            command=self._on_operation_changed,
        ).grid(row=3, column=1, sticky="w", pady=4)

        # Button actions based on a numeric ID.
        ttk.Label(self.content, text="Nummer").grid(row=4, column=0, sticky="w", pady=6)
        self.delete_number_entry = ttk.Entry(
            self.content,
            validate="key",
            validatecommand=self.int_vcmd,
        )
        self.delete_number_entry.grid(
            row=4, column=1, sticky="ew", padx=(8, 12), pady=6
        )
        ttk.Button(
            self.content,
            text="Button 2",
            command=self._on_button2_clicked,
        ).grid(
            row=4,
            column=2,
            sticky="ew",
            pady=6,
            padx=(0, 8),
        )
        ttk.Button(
            self.content,
            text="Button 3",
            command=self._on_button3_clicked,
        ).grid(row=4, column=3, sticky="ew", pady=6)

        # Live readouts from backend streams.
        ttk.Label(self.content, text="Status").grid(
            row=5, column=0, sticky="w", pady=6
        )
        ttk.Entry(
            self.content,
            textvariable=self.status_message_var,
            state="readonly",
        ).grid(row=5, column=1, columnspan=3, sticky="ew", pady=6, padx=(8, 0))

        ttk.Label(self.content, text="Output").grid(
            row=6, column=0, sticky="w", pady=6
        )
        ttk.Entry(
            self.content,
            textvariable=self.output_message_var,
            state="readonly",
        ).grid(row=6, column=1, columnspan=3, sticky="ew", pady=6, padx=(8, 0))

        self._on_operation_changed()

    def _on_assign_clicked(self) -> None:
        """Start a new write stream if green mode is active."""
        if self.green_mode.get():
            self._restart_zuweisung_stream()

    def _on_green_mode_changed(self) -> None:
        """Stop streaming when green mode is turned off."""
        if not self.green_mode.get():
            self._stop_zuweisung_stream()

    def _on_button3_clicked(self) -> None:
        """Call DeleteZuweisung and show its result."""
        target_id = self._parse_int(self.delete_number_entry.get())
        response = self.grpc_client.delete_zuweisung(target_id)
        if response is None:
            self._set_status_message(self._grpc_error_message("RPC-Fehler"))
            return
        result_name = testhmi_pb2.DeleteZuweisungResult_e.Name(
            response.success_state
        )
        self._set_status_message(result_name)

    def _on_button2_clicked(self) -> None:
        """Call Button2Aktion and show its result."""
        raw_id = self.delete_number_entry.get().strip()
        nummer = self._parse_int(raw_id)
        request_id = raw_id or str(nummer)
        response = self.grpc_client.button2_aktion(request_id, nummer)
        if response is None:
            self._set_status_message(self._grpc_error_message("RPC-Fehler"))
            return
        result_name = testhmi_pb2.Button2Result_e.Name(response.button2_result)
        self._set_status_message(result_name)

    def _on_operation_changed(self) -> None:
        """Update the output text based on the radio selection."""
        mode = self.operation_mode.get()
        if mode == "mode1":
            self._set_output_message("Operation1")
        elif mode == "mode2":
            self._set_output_message("Operation2")
        else:
            self._set_output_message("")

    def _start_zuweisung_stream(self) -> None:
        """Start the write stream thread (if not already running)."""
        if self._zuweisung_thread and self._zuweisung_thread.is_alive():
            return
        self._aktion_stream_started = False
        self._set_zuweisung_result("")
        self._zuweisung_stop_event.clear()
        self._zuweisung_thread = threading.Thread(
            target=self._run_zuweisung_stream,
            name="zuweisung-stream",
            daemon=True,
        )
        self._zuweisung_thread.start()

    def _restart_zuweisung_stream(self) -> None:
        """Stop any existing stream and start a new one."""
        self._stop_zuweisung_stream()
        self._start_zuweisung_stream()

    def _stop_zuweisung_stream(self) -> None:
        """Stop the write stream and its dependent read stream."""
        self._zuweisung_stop_event.set()
        if self._zuweisung_thread and self._zuweisung_thread.is_alive():
            self._zuweisung_thread.join(timeout=2.0)
        self._stop_aktion_stream()

    def _start_status_stream(self) -> None:
        """Start the status read stream thread (if not already running)."""
        if self._status_thread and self._status_thread.is_alive():
            return
        self._status_stop_event.clear()
        self._status_thread = threading.Thread(
            target=self._run_status_stream,
            name="status-stream",
            daemon=True,
        )
        self._status_thread.start()

    def _stop_status_stream(self) -> None:
        """Stop the status read stream thread."""
        self._status_stop_event.set()
        if self._status_thread and self._status_thread.is_alive():
            self._status_thread.join(timeout=2.0)

    def _run_zuweisung_stream(self) -> None:
        """Background worker that sends periodic Zuweisung entries."""
        response = self.grpc_client.open_write_stream_zuweisung(
            self._zuweisung_entry_generator()
        )
        if response is None:
            self._set_zuweisung_result("RPC-Fehler")
            self._set_status_message(self._grpc_error_message("Stream-Fehler"))
        else:
            self._set_zuweisung_result("OK")

    def _zuweisung_entry_generator(self):
        """Yield entries once per second until green mode is turned off."""
        while not self._zuweisung_stop_event.is_set() and self.green_mode.get():
            if not self._aktion_stream_started:
                self._aktion_stream_started = True
                self._start_aktion_stream()
            entry = self._build_zuweisung_entry()
            yield entry
            self._zuweisung_stop_event.wait(1.0)

    def _start_aktion_stream(self) -> None:
        """Start the Aktion read stream thread (if not already running)."""
        if self._aktion_thread and self._aktion_thread.is_alive():
            return
        self._aktion_stop_event.clear()
        self._aktion_thread = threading.Thread(
            target=self._run_aktion_stream,
            name="aktion-stream",
            daemon=True,
        )
        self._aktion_thread.start()

    def _stop_aktion_stream(self) -> None:
        """Stop the Aktion read stream thread."""
        self._aktion_stop_event.set()
        if self._aktion_thread and self._aktion_thread.is_alive():
            self._aktion_thread.join(timeout=2.0)

    def _run_aktion_stream(self) -> None:
        """Background worker that listens for Aktion status updates."""
        while not self._aktion_stop_event.is_set():
            try:
                for entry in self.grpc_client.open_read_stream_aktion(
                    timeout=self._stream_wait_timeout
                ):
                    if self._aktion_stop_event.is_set():
                        break
                    if (
                        entry.aktion.aktions_status
                        == testhmi_pb2.AKTIONS_STATUS_CLOSED
                    ):
                        self._aktion_stop_event.set()
                        break
            except grpc.RpcError as error:
                if error.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                    self._log_stream_wait("Aktion")
                    continue
                self._set_status_message(self._format_grpc_error(error))
                return

    def _run_status_stream(self) -> None:
        """Background worker that listens for Status updates."""
        while not self._status_stop_event.is_set():
            received_message = False
            try:
                for entry in self.grpc_client.open_read_stream_status(
                    timeout=self._stream_wait_timeout
                ):
                    if self._status_stop_event.is_set():
                        break
                    received_message = True
                    status_name = testhmi_pb2.OperationsStatus_e.Name(
                        entry.aktion.operations_status
                    )
                    self._set_status_message(status_name)
            except grpc.RpcError as error:
                if error.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                    self._log_stream_wait("Status")
                    continue
                if not received_message:
                    self._set_status_message(self._format_grpc_error(error))
            self._status_stop_event.wait(1.0)

    def _on_close(self) -> None:
        """Cleanly stop threads before closing the window."""
        self._stop_status_stream()
        self._stop_zuweisung_stream()
        self.root.destroy()

    def _build_zuweisung_entry(self):
        """Create a data object for the current UI values."""
        entry_id = self._parse_int(self.assign_number_entry.get())
        timestamp = datetime.now(timezone.utc)
        return ZuweisungEntry(
            entry_id=entry_id,
            entry_id_string=str(entry_id),
            timestamp=timestamp,
        )

    def _set_zuweisung_result(self, text: str) -> None:
        """Update the assignment result field on the UI thread."""
        self.root.after(0, self.zuweisung_result_var.set, text)

    def _set_status_message(self, text: str) -> None:
        """Update the status field on the UI thread."""
        self.root.after(0, self.status_message_var.set, text)

    def _set_output_message(self, text: str) -> None:
        """Update the output field on the UI thread."""
        self.root.after(0, self.output_message_var.set, text)

    def _grpc_error_message(self, fallback: str) -> str:
        """Return the last gRPC error if available, otherwise a fallback."""
        message = self.grpc_client.last_error
        return message if message else fallback

    def _log_stream_wait(self, stream_name: str) -> None:
        """Log that we're still waiting for stream data."""
        print(f"Warte auf {stream_name}-Nachrichten...")

    @staticmethod
    def _format_grpc_error(error: grpc.RpcError) -> str:
        """Return a readable gRPC error message."""
        details = error.details()
        if details:
            return details
        return str(error)

    @staticmethod
    def _parse_int(value: str) -> int:
        """Parse integer input safely, returning 0 on invalid input."""
        try:
            return int(value)
        except ValueError:
            return 0

    def _fit_window_to_content(self) -> None:
        """Resize the window to fit the current layout."""
        self.root.update_idletasks()
        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()
        self.root.geometry(f"{width}x{height}")


@dataclass(frozen=True)
class ZuweisungEntry:
    """Simple data holder for the write stream payload."""

    entry_id: int
    entry_id_string: str
    timestamp: datetime


class GrpcClient:
    def __init__(self, address: str = "localhost:50051") -> None:
        """Wrap gRPC calls with simple error handling."""
        self.address = address
        self._channel = None
        self._stub = None
        self._last_error = ""
        self._enabled = self._initialize_grpc()

    def _initialize_grpc(self) -> bool:
        """Create the channel and stub; return whether gRPC is enabled."""
        self._channel = grpc.insecure_channel(self.address)
        self._stub = testhmi_pb2_grpc.TestHmiServiceStub(self._channel)
        return True

    def open_write_stream_zuweisung(self, entries) -> empty_pb2.Empty | None:
        """Send Zuweisung entries to the write stream."""
        if not self._enabled:
            return None
        try:
            return self._stub.openWriteStreamZuweisung(self._convert_entries(entries))
        except grpc.RpcError as error:
            self._record_error("openWriteStreamZuweisung", error)
            return None

    def open_read_stream_aktion(self, timeout: float | None = None):
        """Read Aktion entries until the stream ends."""
        if not self._enabled:
            return iter(())
        try:
            return self._stub.openReadStreamAktion(
                empty_pb2.Empty(), timeout=timeout
            )
        except grpc.RpcError as error:
            self._record_error("openReadStreamAktion", error)
            return iter(())

    def open_read_stream_status(self, timeout: float | None = None):
        """Read Status entries until the stream ends."""
        if not self._enabled:
            return iter(())
        try:
            return self._stub.openReadStreamStatus(empty_pb2.Empty(), timeout=timeout)
        except grpc.RpcError as error:
            self._record_error("openReadStreamStatus", error)
            return iter(())

    def delete_zuweisung(
        self, target_id: int
    ) -> testhmi_pb2.DeleteZuweisungResponse | None:
        """Call DeleteZuweisung RPC."""
        if not self._enabled:
            return None
        request = testhmi_pb2.DeleteZuweisungRequest(target_id=target_id)
        try:
            return self._stub.DeleteZuweisung(request)
        except grpc.RpcError as error:
            self._record_error("DeleteZuweisung", error)
            return None

    def button2_aktion(
        self, request_id: str, nummer: int
    ) -> testhmi_pb2.Button2Response | None:
        """Call Button2Aktion RPC."""
        if not self._enabled:
            return None
        request = testhmi_pb2.Button2Request(id=request_id, nummer=nummer)
        try:
            return self._stub.Button2Aktion(request)
        except grpc.RpcError as error:
            self._record_error("Button2Aktion", error)
            return None

    @property
    def last_error(self) -> str:
        return self._last_error

    def _record_error(self, context: str, error: grpc.RpcError) -> None:
        details = error.details() or str(error)
        code = error.code()
        self._last_error = f"{context}: {code} - {details}"
        print(f"[gRPC] {self._last_error}")

    def _convert_entries(self, entries):
        """Yield proto payloads from UI data objects."""
        for entry in entries:
            yield self._build_proto_entry(entry)

    def _build_proto_entry(self, entry: ZuweisungEntry):
        """Convert a ZuweisungEntry into a protobuf message."""
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(entry.timestamp)
        return openWriteStreamZuweisung_pb2.ZuweisungEntry_m(
            id=entry.entry_id,
            id_string=entry.entry_id_string,
            timestamp=timestamp,
        )


def main() -> None:
    """Launch the Tkinter app."""
    root = tk.Tk()
    grpc_config = load_grpc_config()
    TestHMIApp(root, grpc_config)
    root.mainloop()


if __name__ == "__main__":
    main()
