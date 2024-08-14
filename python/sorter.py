import base64
import json
import requests
import re
import socket
import os
import time

def get_country_code(ip_address):
    try:
        # Try to resolve the hostname to an IP address
        ip_address = socket.gethostbyname(ip_address)
    except socket.gaierror:
        print(f"Unable to resolve hostname: {ip_address}")
        return None
    except UnicodeError:
        print(f"Hostname violates IDNA rules: {ip_address}")
        return None

    try:
        # Define the base URL for ip-api
        base_url = 'http://ip-api.com/line'

        # Send a GET request to ip-api
        response = requests.get(f'{base_url}/{ip_address}')
        
        # Introduce a delay to respect the rate limit
        time.sleep(1.33)  # Delay for 1.33 seconds

        # Check if the request was successful
        if response.status_code == 429:
            print("Rate limit exceeded. Waiting before retrying...")
            time.sleep(60)  # Wait for 60 seconds before retrying
            return get_country_code(ip_address)  # Retry after delay
        
        if response.status_code != 200:
            print(f"Error fetching data: HTTP {response.status_code}")
            return None

        # Split the response into lines
        response_lines = response.text.splitlines()

        # Check if the first line is 'success'
        if response_lines[0].strip().lower() == 'success':
            # Return the country code from the third line
            return response_lines[2].strip()
        else:
            print(f"Failed to get country code for IP: {ip_address}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return None

def country_code_to_emoji(country_code):
    # Convert the country code to corresponding Unicode regional indicator symbols
    return ''.join(chr(ord(letter) + 127397) for letter in country_code.upper())

# Counter for all proxies
proxy_counter = 0

def process_vmess(proxy):
    global proxy_counter
    base64_str = proxy.split('://')[1]
    missing_padding = len(base64_str) % 4
    if missing_padding:
        base64_str += '='* (4 - missing_padding)
    try:
        decoded_str = base64.b64decode(base64_str).decode('utf-8')
        proxy_json = json.loads(decoded_str)
        ip_address = proxy_json['add']
        country_code = get_country_code(ip_address)
        if country_code is None:
            return None
        flag_emoji = country_code_to_emoji(country_code)
        proxy_counter += 1
        remarks = flag_emoji + country_code + '_' + str(proxy_counter) + '_' + '@Surfboardv2ray'
        proxy_json['ps'] = remarks
        encoded_str = base64.b64encode(json.dumps(proxy_json).encode('utf-8')).decode('utf-8')
        processed_proxy = 'vmess://' + encoded_str
        return processed_proxy
    except Exception as e:
        print("Error processing vmess proxy: ", e)
        return None

def process_vless(proxy):
    global proxy_counter
    ip_address = proxy.split('@')[1].split(':')[0]
    country_code = get_country_code(ip_address)
    if country_code is None:
        return None
    flag_emoji = country_code_to_emoji(country_code)
    proxy_counter += 1
    remarks = flag_emoji + country_code + '_' + str(proxy_counter) + '_' + '@Surfboardv2ray'
    processed_proxy = proxy.split('#')[0] + '#' + remarks
    return processed_proxy

# Process the proxies and write them to converted.txt
with open('input/proxies.txt', 'r') as f, open('output/converted.txt', 'w') as out_f:
    proxies = f.readlines()
    for proxy in proxies:
        proxy = proxy.strip()
        if proxy.startswith('vmess://'):
            processed_proxy = process_vmess(proxy)
        elif proxy.startswith('vless://'):
            processed_proxy = process_vless(proxy)
        if processed_proxy is not None:
            out_f.write(processed_proxy + '\n')

# Read from converted.txt and separate the proxies based on the country code
country_files = {
    'IR': 'output/IR.txt',
    'US': 'output/US.txt',
    'JP': 'output/JP.txt',
    'RU': 'output/RU.txt',
    # Add more countries as needed
}

# Open all files in a dictionary
open_files = {}

try:
    # Attempt to open files for each country
    for country_code, file_path in country_files.items():
        open_files[country_code] = open(file_path, 'w')
    
    # Process the proxies
    with open('output/converted.txt', 'r') as in_f:
        proxies = in_f.readlines()
        
        for proxy in proxies:
            matched = False
            for country_code, file in open_files.items():
                if f'{country_code}_' in proxy:
                    file.write(proxy)
                    matched = True
                    break  # Stop checking other country codes once a match is found
            
            if not matched:
                print(f"No matching country code found for proxy: {proxy.strip()}")

finally:
    # Ensure all files are closed
    for file in open_files.values():
        file.close()
