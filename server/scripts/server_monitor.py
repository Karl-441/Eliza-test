import sys
import os
import time
import subprocess
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ServerMonitor")

SERVER_URL = "http://localhost:8000"
START_CMD = [sys.executable, "-m", "server.app"]
CWD = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Eliza-test root

def check_server():
    try:
        response = requests.get(f"{SERVER_URL}/", timeout=5)
        if response.status_code < 500:
            return True
    except requests.ConnectionError:
        return False
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False
    return False

def start_server():
    logger.info("Starting server...")
    try:
        # Use Popen to start in background/detached if needed, 
        # but here we might want to keep track of it.
        # For simplicity in this script, we just launch it.
        subprocess.Popen(START_CMD, cwd=CWD, shell=True) 
        logger.info("Server start command issued.")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")

def monitor_loop():
    logger.info("Starting Server Monitor...")
    while True:
        if not check_server():
            logger.warning("Server is down! Attempting to restart...")
            start_server()
            # Wait a bit for startup
            time.sleep(10)
            if check_server():
                logger.info("Server recovered successfully.")
            else:
                logger.error("Server failed to recover.")
        else:
            logger.debug("Server is healthy.")
        
        time.sleep(30)

if __name__ == "__main__":
    monitor_loop()
