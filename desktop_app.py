from __future__ import annotations

import ctypes
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import webview


HOST = "127.0.0.1"
PORT = 8501
LAUNCHER_LOG_NAME = "dashboard_launcher.log"


def _show_error(message: str) -> None:
    if os.name == "nt":
        ctypes.windll.user32.MessageBoxW(0, message, "Dashboard Financeiro Executivo", 0x10)
    else:
        print(message)


def _project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _source_root() -> Path:
    if getattr(sys, "frozen", False):
        return _project_root().parent.parent
    return _project_root()


def _bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", _project_root()))
    return _project_root()


def _streamlit_app_path() -> Path:
    bundled_app = _bundle_root() / "app.py"
    if bundled_app.exists():
        return bundled_app
    return _project_root() / "app.py"


def _required_data_dir() -> Path:
    return _project_root() / "data"


def _launcher_log_path() -> Path:
    return _project_root() / LAUNCHER_LOG_NAME


def _write_log(message: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with _launcher_log_path().open("a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")


def _resolve_python_executable() -> str:
    env_python = os.getenv("DASHBOARD_PYTHON_EXECUTABLE")
    if env_python and Path(env_python).exists():
        return env_python

    venv_python = _source_root() / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)

    raise RuntimeError(
        "Não foi encontrada a .venv do projeto. Coloque a pasta .venv ao lado da raiz do projeto ou defina DASHBOARD_PYTHON_EXECUTABLE."
    )


def _port_is_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def _wait_for_port(host: str, port: int, timeout_seconds: int = 60) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if _port_is_open(host, port):
            return
        time.sleep(0.5)
    raise TimeoutError(f"O Streamlit não iniciou na porta {port} dentro do tempo esperado.")


def _validate_runtime_layout() -> None:
    app_path = _streamlit_app_path()
    data_dir = _required_data_dir()

    if not app_path.exists():
        raise FileNotFoundError(f"Arquivo principal não encontrado: {app_path}")

    if not data_dir.exists():
        raise FileNotFoundError(
            f"Pasta de dados não encontrada: {data_dir}. Coloque a pasta data ao lado do executável."
        )


def _start_streamlit() -> subprocess.Popen[str]:
    python_executable = _resolve_python_executable()
    app_path = _streamlit_app_path()
    log_file = _launcher_log_path().open("a", encoding="utf-8")
    log_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Iniciando Streamlit na porta {PORT}\n")
    log_file.flush()

    command = [
        python_executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.headless=true",
        f"--server.address={HOST}",
        f"--server.port={PORT}",
        "--browser.gatherUsageStats=false",
        "--server.fileWatcherType=none",
    ]

    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process = subprocess.Popen(
        command,
        cwd=str(_project_root()),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env={**os.environ, "DASHBOARD_APP_ROOT": str(_project_root())},
        creationflags=creationflags,
    )
    process._log_file = log_file  # type: ignore[attr-defined]
    return process


def main() -> None:
    try:
        _validate_runtime_layout()
    except FileNotFoundError as exc:
        _write_log(f"Falha de layout: {exc}")
        _show_error(str(exc))
        raise

    process = _start_streamlit()
    try:
        _wait_for_port(HOST, PORT)
        webview.create_window(
            "Dashboard Financeiro Executivo",
            f"http://{HOST}:{PORT}",
            width=1400,
            height=900,
        )
        webview.start()
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
        if hasattr(process, "_log_file"):
            try:
                process._log_file.close()  # type: ignore[attr-defined]
            except Exception:
                pass


if __name__ == "__main__":
    main()
