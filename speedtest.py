import socket
import time
import sys
import argparse
import random
import string
import ssl
import subprocess
from datetime import datetime
import os
import math
import re

class CustomSpeedTest:
    def __init__(self):
        self.results = {
            'download': 0,
            'upload': 0,
            'ping': 0,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'server': None
        }
        self.log_file = os.path.expanduser("~/speedtest_results.log")

    def test_ping(self, host, count=10):
        """Test ping to a host"""
        print(f"Testing ping to {host}...")

        try:
            # Try using the ping command
            ping_cmd = ["ping", "-c", str(count), "-q", host]
            result = subprocess.run(ping_cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # Extract average ping time from ping output
                match = re.search(r"rtt min/avg/max/mdev = [\d.]+/([\d.]+)/", result.stdout)
                if match:
                    ping_time = float(match.group(1))
                    self.results['ping'] = ping_time
                    print(f"Ping: {ping_time:.2f} ms")
                    return ping_time

            raise Exception("Ping command failed or could not parse result")

        except Exception as e:
            print(f"System ping failed ({str(e)}), using TCP handshake timing instead...")

            # Fall back to TCP handshake timing
            start_time = time.time()
            port = 443  # HTTPS port

            # Do multiple attempts and average
            successful = 0
            total_time = 0

            for _ in range(count):
                try:
                    # Create a socket and connect to measure TCP handshake time
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2.0)

                    t_start = time.time()
                    sock.connect((host, port))
                    t_end = time.time()

                    handshake_time = (t_end - t_start) * 1000  # Convert to ms
                    total_time += handshake_time
                    successful += 1

                    sock.close()

                except Exception:
                    pass

            if successful > 0:
                avg_ping = total_time / successful
                self.results['ping'] = avg_ping
                print(f"TCP Handshake Ping: {avg_ping:.2f} ms")
                return avg_ping
            else:
                print("Failed to measure ping")
                return None

    def test_download(self, url, size_mb=10, timeout=60):
        """Test download speed using a file download"""
        print(f"Testing download speed ({size_mb} MB)...")

        try:
            # Use curl to download a file and measure the speed
            curl_cmd = [
                "curl", "-L", "-s", "-o", "/dev/null",
                "-w", "%{speed_download}",
                "--connect-timeout", "5",
                "--max-time", str(timeout),
                url
            ]

            start_time = time.time()
            result = subprocess.run(curl_cmd, capture_output=True, text=True)

            if result.returncode == 0 and result.stdout.strip():
                # curl returns speed in bytes per second
                speed_bps = float(result.stdout.strip())
                speed_mbps = speed_bps * 8 / 1_000_000  # Convert to Mbps

                self.results['download'] = speed_mbps
                print(f"Download: {speed_mbps:.2f} Mbps")
                return speed_mbps
            else:
                raise Exception(f"curl failed with code {result.returncode}: {result.stderr}")

        except Exception as e:
            print(f"Download test failed: {str(e)}")
            print("Trying alternate method...")

            try:
                # Try wget as an alternative
                wget_cmd = [
                    "wget", "-O", "/dev/null",
                    "--timeout=5", "--tries=1",
                    url
                ]

                start_time = time.time()
                result = subprocess.run(wget_cmd, capture_output=True, text=True)
                end_time = time.time()

                # Parse the output to find download speed
                if result.returncode == 0:
                    # Extract file size and time from wget output
                    match = re.search(r"(\d+) ([KMG])B/s", result.stderr)
                    if match:
                        value = float(match.group(1))
                        unit = match.group(2)

                        # Convert to Mbps
                        if unit == 'K':
                            speed_mbps = value * 8 / 1000
                        elif unit == 'M':
                            speed_mbps = value * 8
                        elif unit == 'G':
                            speed_mbps = value * 8 * 1000

                        self.results['download'] = speed_mbps
                        print(f"Download: {speed_mbps:.2f} Mbps")
                        return speed_mbps

            except Exception as inner_e:
                print(f"Alternate download test failed: {str(inner_e)}")

            return None

    def test_upload(self, url, size_mb=10, timeout=60):
        """Test upload speed by sending data to a server"""
        print(f"Testing upload speed ({size_mb} MB)...")

        try:
            # Create a temporary file of the specified size for upload testing
            temp_file = "/tmp/speedtest_upload.tmp"

            # Generate the file if it doesn't exist or is wrong size
            if not os.path.exists(temp_file) or os.path.getsize(temp_file) != size_mb * 1024 * 1024:
                with open(temp_file, 'wb') as f:
                    f.write(b'0' * (size_mb * 1024 * 1024))

            # Use curl to upload the file and measure the speed
            curl_cmd = [
                "curl", "-L", "-s", "-X", "POST",
                "-o", "/dev/null",
                "-w", "%{speed_upload}",
                "--connect-timeout", "5",
                "--max-time", str(timeout),
                "-F", f"file=@{temp_file}",
                url
            ]

            start_time = time.time()
            result = subprocess.run(curl_cmd, capture_output=True, text=True)

            # Clean up the temporary file
            try:
                os.unlink(temp_file)
            except:
                pass

            if result.returncode == 0 and result.stdout.strip():
                # curl returns speed in bytes per second
                speed_bps = float(result.stdout.strip())
                speed_mbps = speed_bps * 8 / 1_000_000  # Convert to Mbps

                self.results['upload'] = speed_mbps
                print(f"Upload: {speed_mbps:.2f} Mbps")
                return speed_mbps
            else:
                print(f"Upload test failed: {result.stderr}")
                return None

        except Exception as e:
            print(f"Upload test failed: {str(e)}")
            return None

    def run_test(self):
        """Run all tests and display results"""
        print("\n=== Running Custom Speed Test ===\n")

        # List of test servers to try
        test_servers = [
            {
                'name': 'Cloudflare',
                'ping_host': '1.1.1.1',
                'download_url': 'https://speed.cloudflare.com/__down?bytes=100000000',  # 100MB file
                'upload_url': 'https://speed.cloudflare.com/__up'
            },
            {
                'name': 'Google',
                'ping_host': '8.8.8.8',
                'download_url': 'https://speed.measurementlab.net/static/100MB.zip',
                'upload_url': None  # No upload test for this server
            },
            {
                'name': 'Fast.com (Netflix)',
                'ping_host': 'fast.com',
                'download_url': 'https://speed.fast.com/garbage.png?x=' + ''.join(random.choices(string.ascii_letters, k=8)),
                'upload_url': None
            }
        ]

        # Try each server until one works
        for server in test_servers:
            print(f"\nTesting with {server['name']}...\n")
            self.results['server'] = server['name']

            # Test ping
            ping_result = self.test_ping(server['ping_host'])

            # If ping fails, try the next server
            if ping_result is None:
                print(f"Cannot connect to {server['name']}, trying next server...\n")
                continue

            # Test download
            if server['download_url']:
                download_result = self.test_download(server['download_url'])
                if download_result is None:
                    print(f"Download test failed with {server['name']}, trying next server...\n")
                    continue

            # Test upload
            if server['upload_url']:
                upload_result = self.test_upload(server['upload_url'])
                # Upload might fail but we still consider the test successful if download worked

            # If we got here, at least ping and download worked, so we can display results
            break
        else:
            print("\nAll servers failed. Check your internet connection.\n")
            return False

        # Print summary of results
        print("\n=== Speed Test Results ===")
        print(f"Server: {self.results['server']}")
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Ping: {self.results['ping']:.2f} ms")
        print(f"Download: {self.results['download']:.2f} Mbps")

        if self.results['upload'] > 0:
            print(f"Upload: {self.results['upload']:.2f} Mbps")
        else:
            print("Upload: Not tested")

        # Save results to log file
        self.save_results()

        return True

    def save_results(self):
        """Save test results to a log file"""
        new_file = not os.path.exists(self.log_file)

        with open(self.log_file, 'a') as f:
            if new_file:
                f.write("Timestamp,Server,Ping (ms),Download (Mbps),Upload (Mbps)\n")

            f.write(f"{self.results['timestamp']},{self.results['server']}," +
                    f"{self.results['ping']:.2f},{self.results['download']:.2f}," +
                    f"{self.results['upload']:.2f}\n")

        print(f"\nResults saved to {self.log_file}")

    def show_stats(self):
        """Show statistics from previous test results"""
        if not os.path.exists(self.log_file):
            print(f"No log file found at {self.log_file}")
            return

        # Read the log file
        with open(self.log_file, 'r') as f:
            lines = f.readlines()

        if len(lines) <= 1:  # Only header or empty file
            print("No test results found in log file")
            return

        # Parse the log file
        ping_values = []
        download_values = []
        upload_values = []

        for line in lines[1:]:  # Skip header
            try:
                parts = line.strip().split(',')
                if len(parts) >= 5:
                    ping_values.append(float(parts[2]))
                    download_values.append(float(parts[3]))
                    upload_values.append(float(parts[4]))
            except (ValueError, IndexError):
                continue

        if not ping_values:
            print("No valid test results found in log file")
            return

        # Calculate statistics
        print("\n=== Speed Test Statistics ===")

        print("\nPing (ms):")
        print(f"  Last: {ping_values[-1]:.2f}")
        print(f"  Min: {min(ping_values):.2f}")
        print(f"  Max: {max(ping_values):.2f}")
        print(f"  Avg: {sum(ping_values) / len(ping_values):.2f}")

        print("\nDownload (Mbps):")
        print(f"  Last: {download_values[-1]:.2f}")
        print(f"  Min: {min(download_values):.2f}")
        print(f"  Max: {max(download_values):.2f}")
        print(f"  Avg: {sum(download_values) / len(download_values):.2f}")

        if any(v > 0 for v in upload_values):
            print("\nUpload (Mbps):")
            print(f"  Last: {upload_values[-1]:.2f}")
            print(f"  Min: {min(v for v in upload_values if v > 0):.2f}")
            print(f"  Max: {max(upload_values):.2f}")
            print(f"  Avg: {sum(upload_values) / len(upload_values):.2f}")

        print(f"\nTotal tests: {len(ping_values)}")
        print(f"First test: {lines[1].split(',')[0]}")
        print(f"Last test: {lines[-1].split(',')[0]}")

def main():
    parser = argparse.ArgumentParser(description='Custom Speed Test Tool for Restricted Networks')
    parser.add_argument('--stats', action='store_true', help='Show statistics from previous tests')
    parser.add_argument('--log', type=str, help='Specify a custom log file location')
    args = parser.parse_args()

    speedtest = CustomSpeedTest()

    if args.log:
        speedtest.log_file = args.log

    if args.stats:
        speedtest.show_stats()
    else:
        speedtest.run_test()

if __name__ == "__main__":
    main()
