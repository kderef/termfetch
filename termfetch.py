from platform import architecture
from threading import Thread
from os import getenv, system

def install(package_name: str):
    system("python -m pip install "+package_name)

try:
    from py_cui import PyCUI
except ImportError:
    install("py-cui")
    from py_cui import PyCUI
try:
    from speedtest import Speedtest
except ImportError:
    install("speedtest-cli")
    from speedtest import Speedtest
try:
    from requests import get
except ImportError:
    install("requests")
    from requests import get
try:
    from subprocess import Popen, CalledProcessError, PIPE, STDOUT
except ImportError:
    install("subprocess")
    from subprocess import Popen, CalledProcessError, PIPE, STDOUT

root = PyCUI(5, 5)

# constants
VERSION = "1.0.1"
AUTHOR  = "Kian Heitkamp"
IP4_URL = "https://api.ipify.org"
IP6_URL = "https://api6.ipify.org"
STATUS_BAR_MESSAGE = "press Q to exit | escape to dismiss popups | developer : {} | version : {}".format(AUTHOR, VERSION)

class Disk:
    def capacity() -> float:
        '''
        get total disk capacity in GB
        method: wmic
        if fails, returns 0
        '''
        try:
            ch = Popen(
                [
                    "wmic", "logicaldisk", "get", "size"
                ],
                stdout=PIPE,
                stderr=STDOUT
            )
        except CalledProcessError:
            root.show_error_popup("error occurred", "failed to get disk capacity.")
            return 0
        else:
            return int(ch.stdout.readlines()[1].decode()) / 1024 ** 3
    
    def free() -> float:
        '''
        get free disk space
        method: wmic
        if fails, returns 0
        '''
        try:
            ch = Popen(
                [
                    "wmic", "logicaldisk", "get", "freespace"
                ],
                stdout=PIPE,
                stderr=STDOUT
            )
        except CalledProcessError:
            root.show_error_popup("error occurred", "failed to get disk free space.")
            return 0
        else:
            return int(ch.stdout.readlines()[1].decode()) / 1024 ** 3
    
    def used() -> float:
        '''
        get used disk space
        method: capacity - free = used
        if fails, returns 0
        TODO find a more efficient method
        '''
        cap = Disk.capacity()
        free = Disk.free()

        if cap == 0 and free == 0:
            root.show_error_popup("error occurred", "failed to get disk used space.")
            return 0
        
        return cap - free


class Hardware:
    def cpu() -> str:
        '''
        get the cpu name using WMIC
        if fails, returns "unknown"
        '''
        try:
            ch = Popen(["wmic", "cpu", "get", "name"], stdout=PIPE, stderr=STDOUT)
        except CalledProcessError:
            root.show_error_popup("error occurred", "failed to get cpu name.")
            return "unknown"
        else:
            return ch.stdout.readlines()[1].decode().strip()

    def ram() -> int:
        '''
        get the system ram using powershell (in GB)
        if fails, returns 0
        '''
        try:
            ch = Popen(
                [
                    "powershell.exe",
                    "-command",
                    "[Math]::Round((Get-WmiObject -Class Win32_ComputerSystem).TotalPhysicalMemory/1GB)"
                ],
                stdout=PIPE,
                stderr=STDOUT
            )
        except CalledProcessError:
            root.show_error_popup("error occurred", "failed to get ram amount.")
            return 0
        else:
            return int(ch.stdout.read().decode().strip())
    
    def cpu_cores() -> int:
        '''
        get the number of cpu cores.
        method: get environment variable "NUMBER_OF_PROCESSORS" and divide by 2
        '''
        return round(int(getenv("NUMBER_OF_PROCESSORS"))/2)


class OS:
    '''container class for functions to get system information'''
    def name() -> str:
        '''
        get the name of the windows version (eg. Microsoft Windows 11 home)
        if fails, returns "unknown"
        '''
        try:
            ch = Popen(
            [
                "powershell.exe",
                "-command",
                "(Get-WmiObject -class Win32_OperatingSystem).Caption",
            ],
            stdout=PIPE,
            stderr=STDOUT
            )
        except CalledProcessError:
            return "unknown"
        else:
            return ch.stdout.read().decode().strip()

    def username() -> str:
        '''
        gets the name of the user
        method: get from environment variable
        '''
        return getenv("USERNAME")

    def hostname() -> str:
        '''
        gets the hostname of the computer
        method: get from environment variable
        '''
        return getenv("COMPUTERNAME")


class Private:
    '''container class for ip4 and ip6 functions'''
    def ip4() -> tuple:
        '''
        function to get internal/private IPv4 address
        method: powershell (Test-Connection)
        if fails, returns "not detectable"
        '''
        try:
            ch = Popen(
                [
                    "powershell.exe",
                    "-command",
                    "(Test-Connection -ComputerName (hostname) -Count 1).IPV4Address.IPAddressToString"
                ],
                stdout=PIPE,
                stderr=STDOUT
            )
        except CalledProcessError:
            root.show_error_popup("error occurred", "failed to get internal IPv4.")
            return "not detectable"
        else:
            ip4 = ch.stdout.read().decode().strip()
            return (
                ip4,
                getsubnetmask(ip4)
            )

    def ip6() -> str:
        '''
        function to get internal/private IPv6 address
        method: powershell (Test-Connection)
        if fails, returns "not detectable"
        '''
        try:
            ch = Popen(
                [
                    "powershell.exe",
                    "-command",
                    "(Test-Connection -ComputerName (hostname) -Count 1).IPV6Address.IPAddressToString"
                ],
                stdout=PIPE,
                stderr=STDOUT
            )
        except CalledProcessError:
            root.show_error_popup("error occurred", "failed to get internal IPv6.")
            return "not detectable"
        else:
            return ch.stdout.read().decode().strip()


class Public:
    '''container class for ip4 and ip6 functions'''
    def ip4() -> str:
        '''get the public/external IPv4 address with a GET request'''
        try:
           ip4 = get(IP4_URL).text
        except:
            try:
                ip4 = get(IP4_URL, verify=False).text
            except Exception as e:
                root.show_error_popup("error occurred", f"could not get external ip4 due to error: \"{e}\"")
                ip4 = "not detectable"
        finally:
            return ip4

    def ip6() -> str:
        '''get the public/external IPv6 address with a GET request'''
        try:
           ip6 = get(IP6_URL).text
        except:
            try:
                ip6 = get(IP6_URL, verify=False).text
            except Exception as e:
                root.show_error_popup("error occurred", f"could not get external ip6 due to error: \"{e}\"")
                ip6 = "not detectable"
        finally:
            return ip6


def getsubnetmask(ip4) -> str:
    '''
    function to get the subnet mask (eg. 255.255.255.0) from the IPv4
    '''
    ip = int(ip4.split(".")[0])
    if ip <= 223 and ip >= 192:
        return "255.255.255.0"
    if ip <= 191 and ip >= 128:
        return "255.255.0.0"
    if ip <= 127:
        return "255.0.0.0"


def ip4_show_int():
    '''
    function to show internal IPv4 address using PyCUI.show_message_popup()
    NOTE: _show() runs in a thread
    '''
    def _show():
        ipv4 = Private.ip4()
        root.stop_loading_popup()
        root.show_message_popup("internal IPv4 address", ipv4[0]+'/'+ipv4[1])

    root.show_loading_icon_popup("please wait", "fetching internal ipv4 address")
    t = Thread(target=_show)
    t.start()

def ip6_show_int():
    '''
    function to show internal IPv6 address using PyCUI.show_message_popup()
    NOTE: _show() runs in a thread
    '''
    def _show():
        ipv6 = Private.ip6()
        root.stop_loading_popup()
        root.show_message_popup("internal IPv6 address", ipv6)
    root.show_loading_icon_popup("please wait", "fetching internal ipv6 address")
    t = Thread(target=_show)
    t.start()
def ip4_show_ext():
    '''
    function to show external IPv4 address using PyCUI.show_message_popup()
    NOTE: _show() runs in a thread
    '''
    def _show():
        ipv4 = Public.ip4()
        root.stop_loading_popup()
        root.show_message_popup("external IPv4 address", ipv4)
    root.show_loading_icon_popup("please wait", "fetching external ipv4 address")
    t = Thread(target=_show)
    t.start()
def ip6_show_ext():
    '''
    function to show external IPv6 address using PyCUI.show_message_popup()
    NOTE: _show() runs in a thread
    '''
    def _show():
        ipv6 = Public.ip6()
        root.stop_loading_popup()
        root.show_message_popup("external IPv6 address", ipv6)
    root.show_loading_icon_popup("please wait", "fetching external ipv6 address")
    t = Thread(target=_show)
    t.start()

def show_hardware_info():
    '''
    NOTE: this function starts a thread to fetch_info()
    '''
    def fetch_info():
        '''
        fetch hardware info from functions
        NOTE: this functions runs in a thread
        '''
        cpu = Hardware.cpu()

        cores = Hardware.cpu_cores()

        ram = Hardware.ram()

        username = OS.username()

        hostname = OS.hostname()

        arc = architecture("cmd.exe")[0]

        os = OS.name()

        disk_cap = round(Disk.capacity())

        disk_free = round(Disk.free(), 2)

        disk_used = round(Disk.used(), 2)
        text = root.add_text_block(
            "Hardware Info", 3, 0, column_span=3, row_span=2,
            initial_text="os\t\t--> {}\ncpu\t\t--> {}\ncpu cores\t--> {}\nram\t\t--> {}GB\nusername\t--> {}\nhostname\t--> {}\nplatform\t--> {}".format(
            os, cpu, cores, ram, username, hostname, arc
            )
        )
        text.set_selectable(False)
        disk_info = root.add_text_block(
            "Disk Space", 3, 3, column_span=2, row_span=2,
            initial_text="capacity:\t{}GB\nfree space:\t{}GB\nused space:\t{}GB".format(
                disk_cap, disk_free, disk_used
                )
            )
        disk_info.set_selectable(False)
        root.stop_loading_popup()
    
    root.show_loading_icon_popup("please wait", "loading hardware info")
    t = Thread(target=fetch_info)
    t.start()

def run_speedtest():
    '''
    NOTE: this functions starts a thread to _run()
    '''
    def _run():
        '''
        NOTE: this function runs in a thread
        '''
        sp = Speedtest()
        download = round(sp.download() / 1000000, 2)
        upload = round(sp.upload() / 1000000, 2)
        root.stop_loading_popup()
        root.show_message_popup(f"download: {download}mb/s", f"upload: {upload}mb/s")
    root.show_loading_icon_popup("please wait", "running speedtest")
    t = Thread(target=_run)
    t.start()



def main():
    '''
    main function, Widgets are created here
    '''
    root.toggle_unicode_borders()
    system("title TermFetch")
    root.set_status_bar_text(
        STATUS_BAR_MESSAGE
    )
    root.set_title("TermFetch")

    _l1 = root.add_label("Internal", 1, 0, column_span=1)
    _l1.set_selectable(False)

    _l2 = root.add_label("External", 2, 0, column_span=1)
    _l2.set_selectable(False)

    btn_ip4_int = root.add_button("IPv4", 1, 1, command=ip4_show_int, column_span=2)
    btn_ip4_int.set_color(4)

    btn_ip6_int = root.add_button("IPv6", 1, 3, command=ip6_show_int, column_span=2)
    btn_ip6_int.set_color(4)

    btn_ip4_ext = root.add_button("IPv4", 2, 1, command=ip4_show_ext, column_span=2)
    btn_ip4_ext.set_color(4)

    btn_ip6_ext = root.add_button("IPv6", 2, 3, command=ip6_show_ext, column_span=2)
    btn_ip6_ext.set_color(4)

    btn_hardware = root.add_button(
        "get hardware info", 0, 1, column_span=4, command=show_hardware_info
    )
    btn_hardware.set_color(2)

    btn_speedtest = root.add_button(
        "speedtest", 0, 0, column_span=1, command=run_speedtest
    )
    btn_speedtest.set_color(2)

    root.start() #NOTE DO NOT REMOVE


if __name__ == "__main__":
    main()
