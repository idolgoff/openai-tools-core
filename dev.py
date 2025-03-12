"""Development server with auto-reload functionality."""
import os
import sys
import time
import logging
import subprocess
import signal
from pathlib import Path
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Path to the source directory to watch
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")

# Process to run the application
APP_PROCESS = None


class SourceCodeHandler(FileSystemEventHandler):
    """Handler for file system events in the source code directory."""
    
    def __init__(self, restart_func):
        """Initialize the handler with a restart function."""
        self.restart_func = restart_func
        self.last_modified = time.time()
        
    def on_any_event(self, event):
        """Handle any file system event."""
        # Skip directories and non-Python files
        if event.is_directory or not event.src_path.endswith(".py"):
            return
            
        # Debounce events (prevent multiple restarts for the same change)
        current_time = time.time()
        if current_time - self.last_modified < 0.5:
            return
            
        self.last_modified = current_time
        logger.info(f"Detected change in {event.src_path}")
        self.restart_func()


def start_app():
    """Start the application."""
    global APP_PROCESS
    
    # Kill existing process if running
    if APP_PROCESS and APP_PROCESS.poll() is None:
        os.killpg(os.getpgid(APP_PROCESS.pid), signal.SIGTERM)
        APP_PROCESS.wait()
        
    # Force reload environment variables before starting the app
    load_dotenv(override=True)
    
    # Start new process
    logger.info("Starting application...")
    APP_PROCESS = subprocess.Popen(
        [sys.executable, "src/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        preexec_fn=os.setsid  # Create a new process group
    )
    
    # Log process output in a separate thread
    def log_output():
        for line in iter(APP_PROCESS.stdout.readline, ""):
            print(line.strip())
    
    import threading
    threading.Thread(target=log_output, daemon=True).start()


def cleanup():
    """Clean up resources before exiting."""
    global APP_PROCESS
    
    if APP_PROCESS and APP_PROCESS.poll() is None:
        logger.info("Terminating application...")
        os.killpg(os.getpgid(APP_PROCESS.pid), signal.SIGTERM)
        APP_PROCESS.wait()


def main():
    """Main entry point for the development server."""
    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutting down development server...")
        cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the application
    start_app()
    
    # Set up file watcher
    event_handler = SourceCodeHandler(start_app)
    observer = Observer()
    observer.schedule(event_handler, SRC_DIR, recursive=True)
    observer.start()
    
    logger.info(f"Watching for changes in {SRC_DIR}")
    logger.info("Press Ctrl+C to stop")

    # Force reload and print token for debugging
    load_dotenv(override=True)
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()
    cleanup()

if __name__ == "__main__":
    main()
