# VPN Switcher V3

A Python-based **NordVPN P2P VPN switching service** that automatically connects to randomly selected P2P-optimized countries and periodically changes the VPN connection.

The script is designed for Linux systems running the **NordVPN CLI** and can run continuously as a background service.

## 🚀 Features

- Automatically connects to a random P2P-optimized country.
- Supports a large list of NordVPN P2P countries.
- Automatically disconnects before establishing a new VPN connection.
- Verifies that the VPN connection is actually active.
- Automatically switches VPN locations at randomized intervals.
- Switch interval is approximately **1–2 hours**.
- Uses randomized timing to avoid predictable switching patterns.
- Automatically retries failed VPN connections.
- Implements **exponential backoff** for repeated connection failures.
- Logs events to the **systemd journal**.
- Automatically configures required NordVPN settings at startup.
- Performs a clean VPN disconnect when the service stops.

## 🏗️ How It Works

The script follows this workflow:

```text
                ┌──────────────────────┐
                │     Start Script     │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Configure NordVPN    │
                │ Settings              │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Select Random P2P    │
                │ Country              │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Disconnect Existing  │
                │ VPN Connection       │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Connect to P2P       │
                │ NordVPN Server       │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │ Verify VPN Status    │
                └───────┬───────┬──────┘
                        │         │
                     Success    Failure
                        │         │
                        ▼         ▼
               ┌────────────┐  ┌──────────────┐
               │ Wait ~1–2h │  │ Exponential  │
               │            │  │ Backoff      │
               └─────┬──────┘  └──────┬───────┘
                     │                │
                     └───────┬────────┘
                             ▼
                    Start Next Connection
```

## 🌍 P2P Countries

The script maintains a list of countries intended for P2P connections, including:

- Netherlands
- Switzerland
- Sweden
- Spain
- Romania
- Hong Kong
- Singapore
- Iceland
- France
- Canada
- United Kingdom
- United States
- Finland
- Norway
- Denmark
- Austria
- Australia
- Germany
- Ireland
- Italy
- Japan
- South Korea
- Malaysia
- Thailand
- Taiwan
- Vietnam
- Sri Lanka
- and several others.

The country list is automatically deduplicated and sorted when the script starts.

## ⚙️ NordVPN Configuration

At startup, the script checks and configures NordVPN.

The following settings are managed:

```text
Meshnet     → Enabled
Kill Switch → Disabled
CyberSec    → Disabled
Autoconnect → Disabled
Firewall    → Disabled
```

Meshnet is enabled if it is not already active, and the Meshnet peer list is refreshed.

> **Note:** These settings are intentionally configured by the script for this particular VPN-switching setup. Review them carefully before deploying the script on a production or security-sensitive system.

## 🔄 VPN Switching

A country is randomly selected from the P2P country list:

```python
country = random.choice(P2P_OPTIMIZED_COUNTRIES)
```

The script then disconnects the existing VPN connection and connects to the selected country using the NordVPN P2P group:

```bash
nordvpn disconnect
nordvpn connect <country> --group p2p
```

After connecting, the script waits for the connection to stabilize and verifies the VPN status before considering the connection successful.

## ⏱️ Randomized Switching Interval

After a successful connection, the script waits approximately **1–2 hours** before switching again.

The base interval is randomly selected:

```python
base_switch_interval_seconds = random.randint(3600, 7200)
```

The next switching interval is then randomized around that base interval by approximately ±10%.

This prevents the switching interval from being completely predictable.

## 🔁 Connection Failure Handling

If a VPN connection attempt fails, the script does not immediately retry continuously.

Instead, it uses exponential backoff:

```text
1st failure  → 1 minute
2nd failure  → 2 minutes
3rd failure  → 4 minutes
4th failure  → 8 minutes
...
Maximum     → 30 minutes
```

This reduces repeated connection attempts when NordVPN or the network is temporarily unavailable.

## 📋 Logging

The script uses Python's `logging` module together with `systemd.journal.JournalHandler`.

This allows VPN switching events, connection failures, retries, and service status messages to be viewed through the systemd journal.

View the logs with:

```bash
journalctl -u vpn-switcher.service
```

Follow the logs live:

```bash
journalctl -u vpn-switcher.service -f
```

## 🛠️ Requirements

- Linux
- Python 3
- NordVPN Linux CLI
- Active NordVPN account
- `systemd`
- Python `systemd` journal module

Check Python:

```bash
python3 --version
```

Check NordVPN:

```bash
nordvpn --version
```

Check NordVPN status:

```bash
nordvpn status
```

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/<YOUR-USERNAME>/<YOUR-REPOSITORY>.git
cd <YOUR-REPOSITORY>
```

Make the script executable:

```bash
chmod +x vpn_switcherV3.py
```

Run it:

```bash
sudo python3 vpn_switcherV3.py
```

Before running, make sure you are authenticated with NordVPN:

```bash
nordvpn login
```

## 🔧 Running as a systemd Service

Create a service file:

```bash
sudo nano /etc/systemd/system/vpn-switcher.service
```

Example:

```ini
[Unit]
Description=NordVPN Automatic P2P VPN Switcher
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /path/to/vpn_switcherV3.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Reload systemd:

```bash
sudo systemctl daemon-reload
```

Enable the service at boot:

```bash
sudo systemctl enable vpn-switcher.service
```

Start the service:

```bash
sudo systemctl start vpn-switcher.service
```

Check status:

```bash
sudo systemctl status vpn-switcher.service
```

## 🧪 Testing

Check the current VPN connection:

```bash
nordvpn status
```

Check the public IP:

```bash
curl ifconfig.me
```

Watch the service logs:

```bash
journalctl -u vpn-switcher.service -f
```

You should see messages similar to:

```text
Attempting to connect to a P2P server in nl...
VPN connection to nl verified as active.
VPN active. Next switch in 72 minutes.
```

## 🛡️ Important Security Considerations

This project changes several NordVPN security-related settings, including disabling the NordVPN kill switch and firewall.

Therefore:

- Understand the implications before using it.
- Do not assume the VPN is always active.
- Verify the VPN connection before transferring sensitive traffic.
- Consider implementing an independent network-level kill switch if required.
- Test the configuration in a controlled environment before deploying it permanently.

## 📁 Project Structure

```text
VPN-Switcher/
│
├── vpn_switcherV3.py
└── README.md
```

## 🎯 Project Purpose

This project was created to automate VPN location switching on a Linux system while maintaining a P2P-oriented NordVPN connection.

The project also provided hands-on experience with:

- Python automation
- Linux process management
- NordVPN CLI
- systemd services
- systemd journal logging
- Network troubleshooting
- VPN connectivity verification
- Retry mechanisms
- Exponential backoff
- Linux automation

## ⚠️ Disclaimer

This project is intended for **educational, automation, privacy, and networking purposes**.

You are responsible for complying with:

- NordVPN's terms of service
- Your ISP's terms and policies
- Local laws and regulations
- The laws applicable to your network traffic and activities

Use the project responsibly.

## 📜 License

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

**Author:** Naveen Bose
