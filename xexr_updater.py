#!/usr/bin/env python3

import requests
import json
import os
import subprocess
import re
import time

# Constants
BESU_CONFIG = '/etc/systemd/system/besu.service'
NIMBUS_CONFIG = '/etc/systemd/system/nimbus.service'
MULLVAD_API_URL = 'https://am.i.mullvad.net/json'
MULLVAD_DISCONNECT_CMD = 'mullvad disconnect'
MULLVAD_CONNECT_CMD = 'mullvad connect'
BESU_IP_STR = '--p2p-host='
NIMBUS_IP_STR = '--nat:extip:'
BESU_PATTERN = r'--p2p-host=(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
NIMBUS_PATTERN = r'--nat:extip:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
SYSTEMCTL_RELOAD_CMD = 'sudo systemctl daemon-reload'
BESU_SYSTEMCTL_RESTART_CMD = 'sudo systemctl restart besu'
NIMBUS_SYSTEMCTL_RESTART_CMD = 'sudo systemctl restart nimbus'
SLEEP_INTERVAL = 60


def get_connection_status_and_ip():
    try:
        response = requests.get(MULLVAD_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        connected = data.get('mullvad_exit_ip', False)
        connectedStr = 'connected' if connected else 'disconnected'
        current_ip = data.get('ip', None)
        print(f'VPN {connectedStr}, IP: {current_ip}')
        return connected, current_ip
    except requests.exceptions.RequestException:
        return False, None

def reconnect_mullvad_vpn():
    try:
        subprocess.run(MULLVAD_DISCONNECT_CMD.split(), check=True)
        subprocess.run(MULLVAD_CONNECT_CMD.split(), check=True)
    except subprocess.CalledProcessError:
        print("Error: Failed to reconnect Mullvad VPN.")

def load_config(config, pattern):
    if not os.path.exists(config):
        print(f"Error: Config file '{config}' not found.")
        return

    with open(config, 'r') as f:
        content = f.read()
        match = re.search(pattern, content)
        return match.group(1) if match else None


def save_config(new_ip, config, pattern, ip_str):
    if not os.path.exists(config):
        print(f"Error: Config file '{config}' not found.")
        return

    with open(config, 'r') as f:
        content = f.read()

    updated_content = re.sub(pattern, f'{ip_str}{new_ip}', content)

    with open(config, 'w') as f:
        f.write(updated_content)

def systemctl_action(command):
    try:
        subprocess.run(command.split(), check=True)
    except subprocess.CalledProcessError:
        print(f"Error: Failed to {command}")

def update_config_if_ip_changed():
    connected, current_ip = get_connection_status_and_ip()

    if current_ip is None or not connected:
        print("No IP obtained or not connected. Reconnecting Mullvad VPN...")
        reconnect_mullvad_vpn()
        connected, current_ip = get_connection_status_and_ip()

    if current_ip is None or not connected:
        print("Error: Failed to reconnect to Mullvad VPN")
        return

    previous_ip_besu = load_config(BESU_CONFIG, BESU_PATTERN)
    previous_ip_nimbus = load_config(NIMBUS_CONFIG, NIMBUS_PATTERN)

    if previous_ip_besu is None:
        print("Error: Could not load besu config.")
        return

    if current_ip != previous_ip_besu:
        print(f'Besu IP changed: {previous_ip_besu} -> {current_ip}')
        save_config(current_ip, BESU_CONFIG, BESU_PATTERN, BESU_IP_STR)
        print('Updated BESU config.')
        systemctl_action(SYSTEMCTL_RELOAD_CMD)
        print('Reloaded systemctl configuration.')
        systemctl_action(BESU_SYSTEMCTL_RESTART_CMD)
        print('Restarted Besu.')
    else:
        print('Besu IP has not changed.')

    if previous_ip_nimbus is None:
        print("Error: Could not load nimbus config.")
        return

    if current_ip != previous_ip_nimbus:
        print(f'Nimbus IP changed: {previous_ip_nimbus} -> {current_ip}')
        save_config(current_ip, NIMBUS_CONFIG, NIMBUS_PATTERN, NIMBUS_IP_STR)
        print('Updated NIMBUS config.')
        systemctl_action(SYSTEMCTL_RELOAD_CMD)
        print('Reloaded systemctl configuration.')
        systemctl_action(NIMBUS_SYSTEMCTL_RESTART_CMD)
        print('Restarted Nimbus.')
    else:
        print('Nimbus IP has not changed.')


if __name__ == '__main__':
    print('Starting IP updater...')
    while True:
        update_config_if_ip_changed()
        print(f'Sleeping for {SLEEP_INTERVAL} seconds...')
        time.sleep(SLEEP_INTERVAL)