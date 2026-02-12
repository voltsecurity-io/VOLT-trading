"""
VOLT Trading Control Script
Master control script for the trading system
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path


class VOLTController:
    """Master controller for VOLT Trading system"""

    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.processes = {}

    def start(self):
        """Start the VOLT trading system"""
        print("🚀 Starting VOLT Trading System...")

        # Check if already running
        if self.is_running():
            print("⚠️ VOLT Trading is already running")
            return False

        try:
            # Start main trading process
            main_process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.processes["main"] = main_process

            # Start dashboard if enabled
            dashboard_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    "dashboard/app.py",
                    "--server.port",
                    "8501",
                ],
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.processes["dashboard"] = dashboard_process

            print("✅ VOLT Trading System started successfully")
            print("📊 Dashboard available at: http://localhost:8501")

            return True

        except Exception as e:
            print(f"❌ Failed to start VOLT Trading: {e}")
            self.stop()
            return False

    def stop(self):
        """Stop the VOLT trading system"""
        print("🛑 Stopping VOLT Trading System...")

        for name, process in self.processes.items():
            try:
                if process.poll() is None:  # Process is still running
                    print(f"  🔄 Stopping {name}...")
                    process.terminate()

                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                        print(f"  ✅ {name} stopped")
                    except subprocess.TimeoutExpired:
                        print(f"  ⚠️ Force killing {name}...")
                        process.kill()
                        process.wait()

            except Exception as e:
                print(f"  ❌ Error stopping {name}: {e}")

        self.processes.clear()
        print("👋 VOLT Trading System stopped")

    def status(self):
        """Check system status"""
        print("📊 VOLT Trading System Status")
        print("=" * 40)

        if self.is_running():
            print("🟢 Status: RUNNING")

            # Check individual processes
            for name in ["main", "dashboard"]:
                try:
                    result = subprocess.run(
                        ["pgrep", "-f", name], capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        print(f"  ✅ {name.title()}: Active")
                    else:
                        print(f"  ❌ {name.title()}: Inactive")
                except:
                    print(f"  ❓ {name.title()}: Unknown")

            # Check dashboard
            try:
                import requests

                response = requests.get("http://localhost:8501", timeout=2)
                if response.status_code == 200:
                    print("  🌐 Dashboard: Accessible")
                else:
                    print("  🌐 Dashboard: Error")
            except:
                print("  🌐 Dashboard: Not accessible")

        else:
            print("🔴 Status: STOPPED")

    def restart(self):
        """Restart the trading system"""
        print("🔄 Restarting VOLT Trading System...")
        self.stop()
        time.sleep(2)
        return self.start()

    def logs(self, component="main"):
        """Show logs for a component"""
        log_file = self.project_dir / "logs" / f"{component}.log"

        if log_file.exists():
            print(f"📄 Showing logs for {component}:")
            print("=" * 50)
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    # Show last 50 lines
                    for line in lines[-50:]:
                        print(line.rstrip())
            except Exception as e:
                print(f"❌ Error reading logs: {e}")
        else:
            print(f"❌ No log file found for {component}")

    def is_running(self):
        """Check if VOLT Trading is running"""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "python.*main.py"], capture_output=True, text=True
            )
            return result.returncode == 0
        except:
            return False

    def backup(self):
        """Create a backup of the system"""
        print("💾 Creating system backup...")

        backup_name = f"volt_backup_{int(time.time())}"
        backup_path = Path.home() / "volt_backups" / backup_name

        try:
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)

            # Copy important files
            import shutil

            files_to_backup = [
                "main.py",
                "README.md",
                "requirements.txt",
                "src/",
                "config/",
                "logs/",
            ]

            for item in files_to_backup:
                src = self.project_dir / item
                if src.exists():
                    if src.is_dir():
                        shutil.copytree(src, backup_path / item)
                    else:
                        shutil.copy2(src, backup_path / item)

            print(f"✅ Backup created: {backup_path}")

        except Exception as e:
            print(f"❌ Backup failed: {e}")


def main():
    """Main control function"""
    controller = VOLTController()

    if len(sys.argv) < 2:
        print("VOLT Trading Controller")
        print("Usage: python control.py [command]")
        print("Commands:")
        print("  start     - Start the trading system")
        print("  stop      - Stop the trading system")
        print("  restart   - Restart the trading system")
        print("  status    - Show system status")
        print("  logs      - Show logs (optional: main, dashboard)")
        print("  backup    - Create system backup")
        return

    command = sys.argv[1].lower()

    if command == "start":
        controller.start()
    elif command == "stop":
        controller.stop()
    elif command == "restart":
        controller.restart()
    elif command == "status":
        controller.status()
    elif command == "logs":
        component = sys.argv[2] if len(sys.argv) > 2 else "main"
        controller.logs(component)
    elif command == "backup":
        controller.backup()
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()
