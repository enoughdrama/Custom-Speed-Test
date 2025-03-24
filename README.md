# 🚀 Custom Speed Test 🚀

## 🌐 Overview

A lightweight network speed testing tool designed to work in restricted network environments. This tool measures download speed, upload speed, and ping latency using multiple fallback methods and servers.

## ✨ Features

- ⚡ Test download and upload speeds
- ⏱️ Measure ping latency
- 🔄 Automatic fallback to alternative methods and servers
- 📊 View statistics from previous tests
- 💾 Log results for historical tracking
- 🖥️ Simple command-line interface

## 📋 Requirements

- Python 3.6+
- Standard library dependencies only
- Basic network connectivity

## 🚀 Usage

### Basic Speed Test

```bash
python speedtest.py
```

### View Statistics

```bash
python speedtest.py --stats
```

### Custom Log Location

```bash
python speedtest.py --log /path/to/custom/logfile.log
```

## 📈 Example Output

```
=== Running Custom Speed Test ===

Testing with Cloudflare...

Testing ping to 1.1.1.1...
Ping: 24.35 ms
Testing download speed (10 MB)...
Download: 95.42 Mbps
Testing upload speed (10 MB)...
Upload: 18.78 Mbps

=== Speed Test Results ===
Server: Cloudflare
Timestamp: 2025-03-24 15:30:22
Ping: 24.35 ms
Download: 95.42 Mbps
Upload: 18.78 Mbps

Results saved to ~/speedtest_results.log
```

## 📊 Statistics

View your historical speed test data:

```bash
python speedtest.py --stats
```

## 🔍 How It Works

The tool attempts to measure network performance using multiple servers:
1. 🌐 Cloudflare (1.1.1.1)
2. 🌐 Google (8.8.8.8)
3. 🌐 Fast.com (Netflix)

It uses command-line tools like ping, curl, and wget with fallback mechanisms to ensure tests work even in restricted environments.

## 📝 License

MIT License

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.
