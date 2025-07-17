#!/usr/bin/python3

import subprocess
import time
import random
import logging
from systemd.journal import JournalHandler

# Set up logging to systemd journal
log = logging.getLogger('vpn_switcher')
log.addHandler(JournalHandler())
log.setLevel(logging.INFO)

# Countries with good P2P support (your original list)
P2P_OPTIMIZED_COUNTRIES = [
    'nl', 'ch', 'se', 'es', 'ro', 'hk', 'sg', 'is',
    'lk', 'fr', 'ca', 'uk', 'us', 'fi', 'no', 'dk'
]

def setup_nordvpn_settings():
    """Sets initial NordVPN configuration for torrenting."""
    try:
        # Disabling these ensures they don't interfere with P2P or auto-connect logic
        subprocess.run(['nordvpn', 'set', 'killswitch', 'off'], check=True, capture_output=True, text=True)
        subprocess.run(['nordvpn', 'set', 'cybersec', 'off'], check=True, capture_output=True, text=True)
        subprocess.run(['nordvpn', 'set', 'autoconnect', 'off'], check=True, capture_output=True, text=True)
        # Uncomment the line below if you specifically want UDP, generally good for torrents
        # subprocess.run(['nordvpn', 'set', 'protocol', 'udp'], check=True, capture_output=True, text=True)
        log.info("NordVPN initial settings configured.")
    except subprocess.CalledProcessError as e:
        log.error(f"Failed to set NordVPN configuration: {e.stderr.strip()}")
    except Exception as e:
        log.error(f"Unexpected error during NordVPN setup: {str(e)}")

def connect_p2p_vpn():
    """Connects to a random P2P-optimized server."""
    country = random.choice(P2P_OPTIMIZED_COUNTRIES)
    log.info(f"Attempting to connect to a P2P server in {country}...")
    try:
        # Ensure disconnected before trying to connect
        subprocess.run(['nordvpn', 'disconnect'], timeout=30, capture_output=True, text=True)
        time.sleep(2) # Give NordVPN a moment to disconnect cleanly

        # Connect to P2P-optimized server with UDP protocol (NordVPN usually handles this best)
        result = subprocess.run(
            ['nordvpn', 'connect', country, '--group', 'p2p'],
            check=True,
            capture_output=True,
            text=True,
            timeout=90 # Increased timeout for connection stability
        )
        log.info(f"Successfully initiated connection to {country}. Output: {result.stdout.strip()}")

        # Verify connection is active - crucial for robustness
        time.sleep(10) # Wait longer for connection to stabilize
        status_check = subprocess.run(['nordvpn', 'status'], capture_output=True, text=True, timeout=30)
        if "Status: Connected" in status_check.stdout:
            log.info(f"VPN connection to {country} verified as active.")
            return True
        else:
            log.warning(f"VPN connection to {country} reported as not connected after wait. Status: {status_check.stdout.strip()}")
            return False

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        error_output = e.stderr.strip() if hasattr(e, 'stderr') else str(e)
        log.error(f"Failed to connect to {country}: {error_output}")
        return False
    except Exception as e:
        log.error(f"Unexpected error during VPN connection attempt: {str(e)}")
        return False

def main_vpn_loop():
    """Main loop for connecting and managing the VPN."""
    # Ensure initial settings are applied once at startup
    setup_nordvpn_settings()

    consecutive_failures = 0
    # Base interval for switching (e.g., every 1-2 hours)
    # This simplifies the logic by removing the torrent activity check.
    base_switch_interval_seconds = random.randint(3600, 7200) # 1 to 2 hours

    while True:
        success = connect_p2p_vpn()

        if success:
            consecutive_failures = 0
            # Randomize the next switch interval around the base
            current_interval = random.randint(
                int(base_switch_interval_seconds * 0.9),
                int(base_switch_interval_seconds * 1.1)
            )
            log.info(f"VPN active. Next switch in {current_interval // 60} minutes.")
            time.sleep(current_interval) # Wait for the next cycle
        else:
            consecutive_failures += 1
            # Exponential back-off with a cap to avoid extremely long delays
            retry_delay = min(60 * (2 ** (consecutive_failures - 1)), 1800) # Max 30 min delay
            log.warning(f"VPN connection failed. Retrying in {retry_delay // 60} minutes. (Consecutive failures: {consecutive_failures})")
            time.sleep(retry_delay)

if __name__ == "__main__":
    log.info("Starting VPN switching service (simplified version).")
    try:
        # Initial disconnect to ensure a clean slate at service start
        subprocess.run(['nordvpn', 'disconnect'], timeout=30, capture_output=True, text=True)
        time.sleep(2) # Give it a moment
        main_vpn_loop()
    except KeyboardInterrupt:
        log.info("Script stopped by user (KeyboardInterrupt).")
    except Exception as e:
        log.critical(f"Fatal unhandled error in main execution: {str(e)}")
    finally:
        # Attempt to disconnect VPN on script exit (e.g., service stop)
        log.info("Service stopping. Attempting to disconnect VPN.")
        try:
            subprocess.run(['nordvpn', 'disconnect'], timeout=30, capture_output=True, text=True)
        except Exception as e:
            log.error(f"Error during final VPN disconnect: {str(e)}")
        log.info("Service stopped.")
