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

# Countries with good P2P support and fast speeds
P2P_OPTIMIZED_COUNTRIES = [
    'nl', 'ch', 'se', 'es', 'ro', 'hk', 'sg', 'is', 
    'de', 'fr', 'ca', 'uk', 'us', 'fi', 'no', 'dk'
]

def setup_vpn():
    """Configure NordVPN for optimal torrenting"""
    try:
        subprocess.run(['nordvpn', 'set', 'killswitch', 'on'], check=True)
        subprocess.run(['nordvpn', 'set', 'cybersec', 'off'], check=True)  # May interfere with torrents
        subprocess.run(['nordvpn', 'set', 'autoconnect', 'off'], check=True)
        subprocess.run(['nordvpn', 'set', 'protocol', 'udp'], check=True)  # Better for torrent performance
        log.info("NordVPN configured for torrenting")
    except subprocess.CalledProcessError as e:
        log.error(f"Failed to configure NordVPN: {e}")

def connect_p2p_vpn():
    """Connect to a P2P-optimized server"""
    country = random.choice(P2P_OPTIMIZED_COUNTRIES)
    try:
        # Connect to P2P-optimized server with UDP protocol
        result = subprocess.run(
            ['nordvpn', 'connect', country, '--group', 'p2p'],
            check=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        log.info(f"Connected to P2P server in {country}")
        log.debug(result.stdout)
        
        # Verify connection is active
        time.sleep(5)  # Wait for connection to stabilize
        status = subprocess.run(['nordvpn', 'status'], capture_output=True, text=True)
        if "Disconnected" in status.stdout:
            raise ConnectionError("Failed to establish VPN connection")
            
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        log.error(f"Failed to connect to {country}: {e.stderr if hasattr(e, 'stderr') else str(e)}")
        return False
    except Exception as e:
        log.error(f"Unexpected error: {str(e)}")
        return False

def switch_vpn():
    """Main VPN switching loop"""
    setup_vpn()
    consecutive_failures = 0
    
    while True:
        success = connect_p2p_vpn()
        
        if success:
            consecutive_failures = 0
            # Random interval between 15-45 minutes (better for torrents)
            interval = random.randint(900, 2700)
            log.info(f"VPN active. Next switch in {interval//60} minutes")
            time.sleep(interval)
        else:
            consecutive_failures += 1
            retry_delay = min(300 * consecutive_failures, 3600)  # Exponential backoff up to 1 hour
            log.warning(f"Will retry in {retry_delay//60} minutes (failures: {consecutive_failures})")
            time.sleep(retry_delay)

if __name__ == "__main__":
    try:
        log.info("Starting VPN switching service for torrent protection")
        subprocess.run(['nordvpn', 'disconnect'], timeout=30)
        switch_vpn()
    except KeyboardInterrupt:
        log.info("Script stopped by user")
    except Exception as e:
        log.error(f"Fatal error: {str(e)}")
    finally:
        subprocess.run(['nordvpn', 'disconnect'], timeout=30)
        log.info("Service stopped")
