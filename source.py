import os
import winreg
import win32api
import win32con
import win32service
import subprocess
import psutil
from datetime import datetime, timedelta
import ctypes
import sys
import string
import csv
import glob
import time
import tempfile

class Colors:
    RED = '\033[38;5;196m'
    GREEN = '\033[38;5;46m'
    YELLOW = '\033[38;5;226m'
    ORANGE = '\033[38;5;208m'
    BLUE = '\033[38;5;39m'
    CYAN = '\033[38;5;51m'
    MAGENTA = '\033[38;5;201m'
    PURPLE = '\033[38;5;129m'
    GRAY = '\033[38;5;245m'
    WHITE = '\033[38;5;255m'
    RESET = '\033[0m'

def print_ascii_art():
    os.system('cls')
    print(f"""{Colors.RED}
   _____ _                  _             _____       _            _   _             
  / ____| |                (_)           |  __ \     | |          | | (_)            
 | |    | | ___  __ _ _ __  _ _ __   __ _| |  | | ___| |_ ___  ___| |_ _  ___  _ __  
 | |    | |/ _ \/ _` | '_ \| | '_ \ / _` | |  | |/ _ \ __/ _ \/ __| __| |/ _ \| '_ \ 
 | |____| |  __/ (_| | | | | | | | | (_| | |__| |  __/ ||  __/ (__| |_| | (_) | | | |
  \_____|_|\___|\__,_|_| |_|_|_| |_|\__, |_____/ \___|\__\___|\___|\__|_|\___/|_| |_|
                                     __/ |                                           
                                    |___/                                            
{Colors.RESET}""")

def print_section_header(title):
    print(f"{Colors.CYAN}════════════════════════════════════════════════════════════════════════")
    print(f"  {Colors.WHITE}{title}{Colors.CYAN}")
    print(f"════════════════════════════════════════════════════════════════════════{Colors.RESET}")

def print_status(label, value, status="OK", indent=0):
    indent_str = "  " * indent
    label = indent_str + label
    
    if status == "ERROR":
        status_mark = f"{Colors.RED}[!]{Colors.RESET}"
        color = Colors.RED
    elif status == "WARNING":
        status_mark = f"{Colors.ORANGE}[!]{Colors.RESET}"
        color = Colors.ORANGE
    elif status == "INFO":
        status_mark = f"{Colors.BLUE}[i]{Colors.RESET}"
        color = Colors.BLUE
    else:
        status_mark = f"{Colors.GREEN}[+]{Colors.RESET}"
        color = Colors.GREEN
    
    print(f"  {status_mark} {label:<36} {color}{value}{Colors.RESET}")

def print_menu():
    print_ascii_art()
    print(f"{Colors.GRAY}════════════════════════════════════════════════════════════════════════")
    print(f"        Developer: avarice | Discord Project: https://discord.gg/ResidenceScreenShare")
    print(f"════════════════════════════════════════════════════════════════════════{Colors.RESET}")
    print()
    
    print(f"{Colors.CYAN}┌────────────────────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.CYAN}│{Colors.RESET}                         {Colors.WHITE}MAIN MENU{Colors.RESET}                                   {Colors.CYAN}│{Colors.RESET}")
    print(f"{Colors.CYAN}├────────────────────────────────────────────────────────────────────────┤{Colors.RESET}")
    print(f"{Colors.CYAN}│{Colors.RESET}  {Colors.GREEN}1{Colors.RESET}. Проверка очистки                             {Colors.CYAN}│{Colors.RESET}")
    print(f"{Colors.CYAN}│{Colors.RESET}  {Colors.GREEN}2{Colors.RESET}. Проверка скриптов                                {Colors.CYAN}│{Colors.RESET}")
    print(f"{Colors.CYAN}│{Colors.RESET}  {Colors.GREEN}3{Colors.RESET}. Выход                                                      {Colors.CYAN}│{Colors.RESET}")
    print(f"{Colors.CYAN}└────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
    print()
    
    return input(f"  {Colors.YELLOW}[?] Select option (1-3): {Colors.RESET}")

def get_system_info():
    print_section_header("SYSTEM INFORMATION")
    
    try:
        uptime_seconds = time.time() - psutil.boot_time()
        boot_dt = datetime.fromtimestamp(psutil.boot_time())
        uptime = timedelta(seconds=uptime_seconds)
        
        print_status("System Boot Time", boot_dt.strftime("%Y-%m-%d %H:%M:%S"))
        print_status("System Uptime", f"{uptime.days} days, {uptime.seconds//3600:02d}:{(uptime.seconds%3600)//60:02d}:{uptime.seconds%60:02d}")
        
        drives = []
        for partition in psutil.disk_partitions():
            if partition.fstype:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    drives.append(f"{partition.device} ({partition.fstype}) {usage.percent}%")
                except:
                    drives.append(f"{partition.device} ({partition.fstype})")
        
        if drives:
            print_status("Connected Drives", ", ".join(drives))
    except Exception as e:
        print_status("System Info Error", str(e)[:30], "ERROR")

def check_event_logs():
    print_section_header("EVENT LOG ANALYSIS")
    
    try:
        print(f"  {Colors.BLUE}[i] Checking event logs...{Colors.RESET}")
        ps_script = '''
        $ErrorActionPreference = 'SilentlyContinue'
        
        function Get-LastEvent {
            param($LogName, $EventID)
            try {
                $event = Get-WinEvent -FilterHashtable @{LogName=$LogName; ID=$EventID} -MaxEvents 1 -ErrorAction Stop
                if ($event) {
                    $time = $event.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")
                    Write-Output "$LogName-$EventID=$time"
                } else {
                    Write-Output "$LogName-$EventID=NOT_FOUND"
                }
            } catch {
                Write-Output "$LogName-$EventID=NOT_FOUND"
            }
        }
        
        # Check required events
        Get-LastEvent -LogName "Application" -EventID 3079
        Get-LastEvent -LogName "Security" -EventID 1102
        Get-LastEvent -LogName "Security" -EventID 104
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8') as f:
            f.write(ps_script)
            temp_file = f.name
        try:
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", temp_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, shell=True)
            results = {}
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        results[key] = value
            if "Application-3079" in results:
                if results["Application-3079"] != "NOT_FOUND":
                    print_status("[!] Event 3079 (USN Journal)", f"{results['Application-3079']}", "WARNING")
                else:
                    print_status("[+] Event 3079 (USN Journal)", "Not found")
            else:
                print_status("[+] Event 3079 (USN Journal)", "Not found")
            
            if "Security-1102" in results:
                if results["Security-1102"] != "NOT_FOUND":
                    print_status("[!] Event 1102 (Log Clear)", f"{results['Security-1102']}", "WARNING")
                else:
                    print_status("[+] Event 1102 (Log Clear)", "Not found")
            else:
                print_status("[+] Event 1102 (Log Clear)", "Not found")
            
            if "Security-104" in results:
                if results["Security-104"] != "NOT_FOUND":
                    print_status("[!] Event 104 (Audit Disabled)", f"{results['Security-104']}", "WARNING")
                else:
                    print_status("[+] Event 104 (Audit Disabled)", "Not found")
            else:
                print_status("[+] Event 104 (Audit Disabled)", "Not found")
                
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass
                
    except subprocess.TimeoutExpired:
        print_status("[!] Event Check", "Timeout", "ERROR")
    except Exception as e:
        print_status("[!] Analysis Error", f"{str(e)[:35]}...", "ERROR")

def check_prefetch_artifacts():
    print_section_header("PREFETCH FILES ANALYSIS")
    
    prefetch_path = r"C:\Windows\Prefetch"
    suspicious_tools = ["FSUTIL", "WEVTUTIL", "REG", "CLEANER", "CCLEANER", "PRIVACY", "DISKCLEAN", "WIPER", "CMD", "POWERSHELL", "CODE", "PYTHON", "VSCODE"]
    
    if os.path.exists(prefetch_path):
        try:
            pf_files = [f for f in os.listdir(prefetch_path) if f.endswith('.pf')]
            total_pf_count = len(pf_files)
            
            print_status("[i] Total .pf files", str(total_pf_count))
            
            if total_pf_count < 30:
                print_status("[!] Cleared .pf files", f"Cleanup detected: {total_pf_count} files", "WARNING")
            elif total_pf_count < 100:
                print_status("[!] Low .pf count", f"Possible cleanup: {total_pf_count} files", "WARNING")
            else:
                print_status("[+] .pf files count", "Normal amount")
            
            found_tools = []
            for pf_file in pf_files:
                file_upper = pf_file.upper()
                for tool in suspicious_tools:
                    if tool in file_upper:
                        file_path = os.path.join(prefetch_path, pf_file)
                        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        found_tools.append((pf_file, tool, mtime))
                        break
            
            if found_tools:
                for file_name, tool, mtime in found_tools:
                    print_status(f"[!] {tool}", f"{file_name} - {mtime.strftime('%Y-%m-%d %H:%M:%S')}", "WARNING")
            else:
                print_status("[+] Cleaning tools", "Not found")
            
            readonly_files = []
            hidden_files = []
            for pf_file in pf_files:
                file_path = os.path.join(prefetch_path, pf_file)
                try:
                    attrs = os.stat(file_path).st_file_attributes
                    if attrs & 1:
                        readonly_files.append(pf_file)
                    if attrs & 2:
                        hidden_files.append(pf_file)
                except:
                    pass
            
            if readonly_files:
                print_status("[!] Read-only files", f"Found: {len(readonly_files)}", "WARNING")
                for file_name in readonly_files[:3]:
                    print_status(f"  [i] Read-only", file_name, "WARNING", 1)
            
            if hidden_files:
                print_status("[!] Hidden files", f"Found: {len(hidden_files)}", "WARNING")
                for file_name in hidden_files[:3]:
                    print_status(f"  [i] Hidden", file_name, "WARNING", 1)
            
            if pf_files:
                try:
                    times = []
                    for file in pf_files:
                        file_path = os.path.join(prefetch_path, file)
                        mtime = os.path.getmtime(file_path)
                        times.append(mtime)
                    
                    if times:
                        oldest = datetime.fromtimestamp(min(times))
                        newest = datetime.fromtimestamp(max(times))
                        time_diff = newest - oldest
                        
                        if time_diff.days < 2:
                            print_status("[!] Time range", f"Too narrow: {time_diff.days} days", "WARNING")
                        else:
                            print_status("[+] Time range", f"{time_diff.days} days")
                except:
                    pass
                
        except Exception as e:
            print_status("[!] Prefetch Analysis Error", str(e)[:35], "ERROR")
    else:
        print_status("[!] Prefetch Folder", "Not found", "ERROR")

def check_services():
    print_section_header("SERVICE STATUS")
    
    services = [
        ("SysMain", "SysMain"),
        ("DiagTrack", "DiagTrack"),
        ("PcaSvc", "PcaSvc"),
        ("Appinfo", "Appinfo"),
        ("Bam", "Bam"),
        ("Power", "Power"),
        ("WSearch", "WSearch"),
        ("DPS", "DPS"),
        ("EventLog", "EventLog"),
        ("CDPSvc", "CDPSvc")
    ]
    
    for service_name, display_name in services:
        try:
            scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ENUMERATE_SERVICE)
            try:
                service = win32service.OpenService(scm, service_name, win32service.SERVICE_QUERY_STATUS)
                status = win32service.QueryServiceStatus(service)
                if status[1] == win32service.SERVICE_RUNNING:
                    print_status(f"[+] {display_name:<25}", "Running")
                else:
                    print_status(f"[!] {display_name:<25}", "Stopped", "WARNING")
                win32service.CloseServiceHandle(service)
            except:
                print_status(f"[!] {display_name:<25}", "Not found", "ERROR")
            win32service.CloseServiceHandle(scm)
                
        except Exception:
            print_status(f"[!] {display_name:<25}", "Check error", "ERROR")

def get_logical_drives():
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives

def check_recycle_bin():
    print_section_header("RECYCLE BIN ANALYSIS")
    
    try:
        found_dates = []
        recycle_found = False
        
        for drive in get_logical_drives():
            recycle_path = os.path.join(drive, "$Recycle.Bin")
            
            if os.path.exists(recycle_path):
                recycle_found = True
                print_status(f"[+] Recycle Bin found", f"Drive {drive}")
                
                try:
                    items = os.listdir(recycle_path)
                    if items:
                        for item in items:
                            item_path = os.path.join(recycle_path, item)
                            if os.path.isdir(item_path):
                                if ("S-1-5-21" in item or "S-1-5-" in item or item.endswith("1001") or item.endswith("1000")):
                                    try:
                                        mtime = os.path.getmtime(item_path)
                                        clean_date = datetime.fromtimestamp(mtime)
                                        found_dates.append(clean_date)
                                        print_status(f"  [i] User folder", f"{item} - {clean_date.strftime('%Y-%m-%d %H:%M:%S')}", "INFO", 1)
                                    except:
                                        pass
                    else:
                        print_status(f"  [!] Empty recycle bin", f"Drive {drive}", "WARNING", 1)
                except PermissionError:
                    print_status(f"  [!] No access", f"Drive {drive}", "ERROR", 1)
                except Exception as e:
                    print_status(f"  [!] Read error", f"{str(e)[:20]}", "ERROR", 1)
        
        if not recycle_found:
            print_status("[!] Recycle Bin", "Not found on any drive", "ERROR")
        
        if found_dates:
            if len(found_dates) > 0:
                latest_clean = max(found_dates)
                oldest_clean = min(found_dates)
                print_status("[!] Last cleanup", latest_clean.strftime("%Y-%m-%d %H:%M:%S"), "WARNING")
                print_status("[i] Earliest record", oldest_clean.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            if recycle_found:
                print_status("[i] Recycle Bin", "Empty or no user records")
            
    except Exception as e:
        print_status("[!] Analysis Error", str(e)[:35], "ERROR")

def check_recent_folder():
    print_section_header("RECENT FOLDER ANALYSIS")
    
    try:
        recent_path = os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Recent')
        
        if os.path.exists(recent_path):
            items = []
            try:
                items = os.listdir(recent_path)
                items = [item for item in items if not item.lower().endswith(('.lnk', '.tmp', '.dat'))]
            except:
                pass
            
            if items:
                print_status("[!] Status", f"Not empty ({len(items)} items)", "WARNING")
                try:
                    mtime = os.path.getmtime(recent_path)
                    mod_time = datetime.fromtimestamp(mtime)
                    print_status("[i] Last modified", mod_time.strftime("%Y-%m-%d %H:%M:%S"))
                except:
                    pass
            else:
                print_status("[+] Status", "Empty")
        else:
            print_status("[!] Recent Folder", "Not found", "ERROR")
            
    except Exception as e:
        print_status("[!] Analysis Error", str(e)[:35], "ERROR")

def check_activities_cache():
    print_section_header("ACTIVITIESCACHE.DB REGISTRATION")
    
    try:
        found_cache = False
        already_found = set()
        
        print(f"  {Colors.BLUE}[i] Searching for ActivitiesCache.db...{Colors.RESET}")
        
        search_paths = [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'ConnectedDevicesPlatform'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'ActivityHistory'),
            "C:\\ProgramData\\Microsoft\\Windows\\ActivityHistory",
            "C:\\Users\\All Users\\Microsoft\\Windows\\ActivityHistory",
        ]
        
        base_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'ConnectedDevicesPlatform')
        if os.path.exists(base_path):
            for item in os.listdir(base_path):
                if item.startswith('L.'):
                    search_paths.append(os.path.join(base_path, item))
        
        for search_path in search_paths:
            if os.path.exists(search_path):
                try:
                    for root, dirs, files in os.walk(search_path):
                        for file in files:
                            if file.lower() == 'activitiescache.db':
                                file_path = os.path.join(root, file)
                                
                                if file_path in already_found:
                                    continue
                                    
                                already_found.add(file_path)
                                
                                try:
                                    size = os.path.getsize(file_path)
                                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                                    ctime = datetime.fromtimestamp(os.path.getctime(file_path))
                                    
                                    print_status("[+] File found", file_path)
                                    print_status("  [i] File size", f"{size / 1024:.1f} KB", "INFO", 1)
                                    print_status("  [i] Last modified", mtime.strftime("%Y-%m-%d %H:%M:%S"), "INFO", 1)
                                    print_status("  [i] Creation date", ctime.strftime("%Y-%m-%d %H:%M:%S"), "INFO", 1)
                                    
                                    if size < 1024:
                                        print_status("  [!] Suspiciously small", f"{size} bytes", "WARNING", 1)
                                    if (datetime.now() - ctime).days < 1:
                                        print_status("  [!] Recently created", f"{(datetime.now() - ctime).seconds//3600} hours ago", "WARNING", 1)
                                    
                                    found_cache = True
                                except Exception as e:
                                    print_status("[i] File found", f"{file_path} (read error: {str(e)[:20]})", "INFO")
                                    found_cache = True
                except Exception:
                    continue
        
        if not found_cache:
            print_status("[!] ActivitiesCache.db", "Not found", "WARNING")
            
    except Exception as e:
        print_status("[!] Analysis Error", str(e)[:35], "ERROR")

def check_shellbag_cleaner():
    print_section_header("SHELLBAGS CLEANER")
    
    filename = "shellbag_analyzer_cleaner.ini"
    search_paths = [
        os.path.expanduser("~"),
        "C:\\Users\\Public",
        "C:\\Windows",
        "C:\\",
    ]
    
    found = False
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            try:
                for root, dirs, files in os.walk(search_path, topdown=True):
                    if filename in files:
                        file_path = os.path.join(root, filename)
                        try:
                            ctime = datetime.fromtimestamp(os.path.getctime(file_path))
                            mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                            
                            print_status("[!] File found", file_path, "WARNING")
                            print_status("  [i] Creation date", ctime.strftime("%Y-%m-%d %H:%M:%S"), "WARNING", 1)
                            print_status("  [i] Modification date", mtime.strftime("%Y-%m-%d %H:%M:%S"), "WARNING", 1)
                            
                            found = True
                            return
                        except:
                            print_status("[!] File found", f"{file_path} (read error)", "WARNING")
                            found = True
                            return
            except Exception:
                continue
    
    if not found:
        print_status("[+] File", f"{filename} not found")

def check_console_history():
    print_section_header("POWERSHELL HISTORY")
    
    try:
        history_path = os.path.join(os.environ.get('APPDATA', ''), 
                                   'Microsoft', 
                                   'Windows', 
                                   'PowerShell', 
                                   'PSReadLine', 
                                   'ConsoleHost_history.txt')
        
        if os.path.exists(history_path):
            try:
                mtime = os.path.getmtime(history_path)
                mod_time = datetime.fromtimestamp(mtime)
                file_size = os.path.getsize(history_path)
                
                print_status("[i] History file", "Found")
                print_status("[i] Last modified", mod_time.strftime("%Y-%m-%d %H:%M:%S"))
                print_status("[i] File size", f"{file_size / 1024:.1f} KB")
                
                if file_size == 0:
                    print_status("[!] History file", "Empty (suspicious)", "WARNING")
                elif file_size < 100:
                    print_status("[!] History file", "Very small", "WARNING")
                    
            except Exception as e:
                print_status("[!] Read error", str(e)[:25], "ERROR")
        else:
            print_status("[i] History file", "Not found")
            
    except Exception as e:
        print_status("[!] Analysis Error", str(e)[:35], "ERROR")

def check_java_processes():
    print_section_header("ACTIVE JAVA PROCESSES")
    
    try:
        java_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'create_time', 'exe']):
            try:
                process_info = proc.info
                process_name = process_info['name'].lower()
                
                if 'java' in process_name or 'javaw' in process_name or 'javaws' in process_name:
                    create_time = datetime.fromtimestamp(process_info['create_time'])
                    
                    java_processes.append({
                        'pid': process_info['pid'],
                        'name': process_info['name'],
                        'started': create_time,
                        'exe': process_info.get('exe', 'N/A')
                    })
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if java_processes:
            print_status(f"[!] Java processes found", f"{len(java_processes)}", "WARNING")
            
            for proc in java_processes:
                print_status(f"  [i] {proc['name']} (PID: {proc['pid']})", 
                           f"Started: {proc['started'].strftime('%H:%M:%S')}", 
                           "WARNING", 1)
        else:
            print_status("[+] Java processes", "Not found")
            
    except Exception as e:
        print_status("[!] Check Error", str(e)[:35], "ERROR")

def check_system_access():
    print_section_header("SYSTEM UTILITIES ACCESS")
    
    try:
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            try:
                value, _ = winreg.QueryValueEx(key, "DisableTaskMgr")
                if value == 1:
                    print_status("[!] Task Manager", "Blocked via registry", "WARNING")
                else:
                    print_status("[+] Task Manager", "Available")
            except FileNotFoundError:
                print_status("[+] Task Manager", "Available")
            winreg.CloseKey(key)
        except FileNotFoundError:
            print_status("[+] Task Manager", "Available")
        except Exception:
            print_status("[+] Task Manager", "Available")
        try:
            gpedit_path = r"C:\Windows\System32\gpedit.msc"
            if os.path.exists(gpedit_path):
                print_status("[+] Group Policy Editor", "Available")
            else:
                print_status("[!] Group Policy Editor", "Not found (possibly Windows Home)", "WARNING")
        except:
            print_status("[+] Group Policy Editor", "Available")
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            try:
                value, _ = winreg.QueryValueEx(key, "DisableRegistryTools")
                if value == 1:
                    print_status("[!] Registry Editor", "Blocked via registry", "WARNING")
                else:
                    print_status("[+] Registry Editor", "Available")
            except FileNotFoundError:
                print_status("[+] Registry Editor", "Available")
            winreg.CloseKey(key)
        except FileNotFoundError:
            print_status("[+] Registry Editor", "Available")
        except Exception:
            print_status("[+] Registry Editor", "Available")
        try:
            key_path = r"Software\Policies\Microsoft\Windows\System"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            try:
                value, _ = winreg.QueryValueEx(key, "DisableCMD")
                if value == 1:
                    print_status("[!] Command Prompt", "Blocked via registry", "WARNING")
                else:
                    print_status("[+] Command Prompt", "Available")
            except FileNotFoundError:
                print_status("[+] Command Prompt", "Available")
            winreg.CloseKey(key)
        except FileNotFoundError:
            print_status("[+] Command Prompt", "Available")
        except Exception:
            print_status("[+] Command Prompt", "Available")
            
    except Exception as e:
        print_status("[!] Access Check Error", str(e)[:35], "ERROR")

def check_prefetch_settings():
    print_section_header("PREFETCH SETTINGS")
    
    reg_path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters"
    
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
        
        try:
            value, reg_type = winreg.QueryValueEx(key, "EnablePrefetcher")
            if value == 0:
                print_status("[!] EnablePrefetcher", "Disabled (0)", "WARNING")
            else:
                print_status("[+] EnablePrefetcher", f"Enabled ({value})")
        except FileNotFoundError:
            print_status("[i] EnablePrefetcher", "Default (3)")
        
        try:
            value, reg_type = winreg.QueryValueEx(key, "EnableSuperfetch")
            if value == 0:
                print_status("[!] EnableSuperfetch", "Disabled (0)", "WARNING")
            else:
                print_status("[+] EnableSuperfetch", f"Enabled ({value})")
        except FileNotFoundError:
            print_status("[i] EnableSuperfetch", "Default")
        
        winreg.CloseKey(key)
        
    except Exception as e:
        print_status("[!] Registry Access", str(e)[:35], "ERROR")

def check_prefetch_integrity():
    print_section_header("PREFETCH INTEGRITY")
    
    prefetch_path = r"C:\Windows\Prefetch"
    
    if os.path.exists(prefetch_path):
        try:
            files = [f for f in os.listdir(prefetch_path) if f.endswith('.pf')]
            
            if not files:
                print_status("[!] Prefetch files", "None found (suspicious)", "ERROR")
                return
            
            print_status("[i] Total files", str(len(files)))
            
            try:
                times = []
                for file in files:
                    file_path = os.path.join(prefetch_path, file)
                    mtime = os.path.getmtime(file_path)
                    times.append(mtime)
                
                if times:
                    oldest = datetime.fromtimestamp(min(times))
                    newest = datetime.fromtimestamp(max(times))
                    
                    print_status("[i] Oldest file", oldest.strftime("%Y-%m-%d %H:%M:%S"))
                    print_status("[i] Newest file", newest.strftime("%Y-%m-%d %H:%M:%S"))
            except:
                pass
                
        except Exception as e:
            print_status("[!] Check Error", str(e)[:35], "ERROR")
    else:
        print_status("[!] Prefetch Folder", "Not found", "ERROR")

def check_registry_settings():
    print_section_header("REGISTRY SETTINGS")
    
    settings = [
        {
            "name": "CMD Access",
            "path": r"Software\Policies\Microsoft\Windows\System",
            "key": "DisableCMD",
            "hive": winreg.HKEY_CURRENT_USER,
            "danger_value": 1,
            "enabled": False
        },
        {
            "name": "PowerShell Logging",
            "path": r"SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging",
            "key": "EnableScriptBlockLogging",
            "hive": winreg.HKEY_LOCAL_MACHINE,
            "danger_value": 0,
            "enabled": True
        },
        {
            "name": "Activities Cache",
            "path": r"SOFTWARE\Policies\Microsoft\Windows\System",
            "key": "EnableActivityFeed",
            "hive": winreg.HKEY_LOCAL_MACHINE,
            "danger_value": 0,
            "enabled": True
        },
        {
            "name": "Prefetch Enabled",
            "path": r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters",
            "key": "EnablePrefetcher",
            "hive": winreg.HKEY_LOCAL_MACHINE,
            "danger_value": 0,
            "enabled": True
        }
    ]
    
    for setting in settings:
        try:
            key = winreg.OpenKey(setting["hive"], setting["path"])
            value, reg_type = winreg.QueryValueEx(key, setting["key"])
            winreg.CloseKey(key)
            
            if setting["enabled"]:
                if value == setting["danger_value"]:
                    print_status(f"[!] {setting['name']}", f"Disabled ({value})", "WARNING")
                else:
                    print_status(f"[+] {setting['name']}", f"Enabled ({value})")
            else:
                if value == setting["danger_value"]:
                    print_status(f"[!] {setting['name']}", f"Enabled ({value})", "WARNING")
                else:
                    print_status(f"[+] {setting['name']}", f"Disabled ({value})")
                
        except FileNotFoundError:
            print_status(f"[i] {setting['name']}", "Default")
        except Exception as e:
            print_status(f"[!] {setting['name']}", str(e)[:25], "ERROR")

def check_running_scripts():
    print_section_header("RUNNING BAT/PY SCRIPTS DETECTION")
    
    try:
        bat_processes = []
        py_processes = []
        
        print(f"  {Colors.BLUE}[i] Scanning for running BAT and PY scripts...{Colors.RESET}")
        
        for proc in psutil.process_iter(['pid', 'name', 'create_time', 'exe', 'cmdline']):
            try:
                process_info = proc.info
                cmdline = process_info.get('cmdline')
                
                if cmdline:
                    for arg in cmdline:
                        if isinstance(arg, str) and arg.lower().endswith('.bat'):
                            create_time = datetime.fromtimestamp(process_info['create_time'])
                            bat_processes.append({
                                'pid': process_info['pid'],
                                'name': process_info['name'],
                                'started': create_time,
                                'cmdline': ' '.join(cmdline),
                                'path': arg
                            })
                            break
                    for arg in cmdline:
                        if isinstance(arg, str) and arg.lower().endswith('.py'):
                            create_time = datetime.fromtimestamp(process_info['create_time'])
                            py_processes.append({
                                'pid': process_info['pid'],
                                'name': process_info['name'],
                                'started': create_time,
                                'cmdline': ' '.join(cmdline),
                                'path': arg
                            })
                            break
                    process_name = process_info['name'].lower()
                    if 'python' in process_name or 'python3' in process_name or 'python.exe' in process_name:
                        for arg in cmdline:
                            if isinstance(arg, str) and (arg.lower().endswith('.py') or not arg.endswith('.exe')):
                                if not arg.lower().endswith('.exe'):
                                    create_time = datetime.fromtimestamp(process_info['create_time'])
                                    py_processes.append({
                                        'pid': process_info['pid'],
                                        'name': process_info['name'],
                                        'started': create_time,
                                        'cmdline': ' '.join(cmdline),
                                        'path': arg if arg.lower().endswith('.py') else 'Unknown Python script'
                                    })
                                    break
                                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            except Exception:
                continue
        if bat_processes:
            print_status(f"[!] BAT scripts running", f"{len(bat_processes)} found", "WARNING")
            
            for proc in bat_processes:
                print_status(f"  [i] BAT: {os.path.basename(proc['path'])} (PID: {proc['pid']})", 
                           f"Started: {proc['started'].strftime('%H:%M:%S')}", 
                           "WARNING", 1)
                print_status(f"       Path", f"{proc['path']}", "WARNING", 2)
                if len(proc['cmdline']) > 100:
                    print_status(f"       Command", f"{proc['cmdline'][:100]}...", "WARNING", 2)
                else:
                    print_status(f"       Command", f"{proc['cmdline']}", "WARNING", 2)
        else:
            print_status("[+] BAT scripts", "No running BAT scripts found")
        if py_processes:
            print_status(f"[!] Python scripts running", f"{len(py_processes)} found", "WARNING")
            
            for proc in py_processes:
                print_status(f"  [i] PY: {os.path.basename(proc['path'])} (PID: {proc['pid']})", 
                           f"Started: {proc['started'].strftime('%H:%M:%S')}", 
                           "WARNING", 1)
                print_status(f"       Path", f"{proc['path']}", "WARNING", 2)
                if len(proc['cmdline']) > 100:
                    print_status(f"       Command", f"{proc['cmdline'][:100]}...", "WARNING", 2)
                else:
                    print_status(f"       Command", f"{proc['cmdline']}", "WARNING", 2)
        else:
            print_status("[+] Python scripts", "No running Python scripts found")
        suspicious_paths = [
            r"C:\Windows\Temp",
            r"C:\Windows\System32",
            r"C:\ProgramData",
            r"C:\Users\Public",
            os.path.expanduser("~\\AppData\\Local\\Temp"),
            os.path.expanduser("~\\AppData\\Roaming"),
            os.path.expanduser("~\\Downloads")
        ]
        
        suspicious_bat = []
        suspicious_py = []
        
        for proc in bat_processes:
            for sus_path in suspicious_paths:
                if sus_path.lower() in proc['path'].lower():
                    suspicious_bat.append(proc)
                    break
        
        for proc in py_processes:
            for sus_path in suspicious_paths:
                if sus_path.lower() in proc['path'].lower():
                    suspicious_py.append(proc)
                    break
        
        if suspicious_bat:
            print_status(f"[!] Suspicious BAT locations", f"{len(suspicious_bat)} in temp/system folders", "ERROR")
            for proc in suspicious_bat:
                print_status(f"  [!] {os.path.basename(proc['path'])}", f"Location: {proc['path']}", "ERROR", 1)
        
        if suspicious_py:
            print_status(f"[!] Suspicious PY locations", f"{len(suspicious_py)} in temp/system folders", "ERROR")
            for proc in suspicious_py:
                print_status(f"  [!] {os.path.basename(proc['path'])}", f"Location: {proc['path']}", "ERROR", 1)
        
        cmd_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'create_time']):
            try:
                if proc.info['name'].lower() == 'cmd.exe':
                    create_time = datetime.fromtimestamp(proc.info['create_time'])
                    cmd_processes.append({
                        'pid': proc.info['pid'],
                        'started': create_time
                    })
            except:
                continue
        
        if cmd_processes:
            print_status(f"[i] CMD.exe processes", f"{len(cmd_processes)} running", "INFO")
            for proc in cmd_processes[:3]:  
                print_status(f"  [i] CMD.exe (PID: {proc['pid']})", f"Started: {proc['started'].strftime('%H:%M:%S')}", "INFO", 1)
            
    except Exception as e:
        print_status("[!] Script Detection Error", str(e)[:35], "ERROR")

def cleaning_detection():
    os.system('cls')
    print_ascii_art()
    
    print(f"{Colors.GRAY}════════════════════════════════════════════════════════════════════════")
    print(f"        Developer: avarice | Discord Project: https://discord.gg/ResidenceScreenShare")
    print(f"════════════════════════════════════════════════════════════════════════{Colors.RESET}")
    print()
    
    try:
        get_system_info()
        print()
        check_event_logs()
        print()
        check_prefetch_artifacts()
        print()
        check_services()
        print()
        check_recycle_bin()
        print()
        check_recent_folder()
        print()
        check_activities_cache()
        print()
        check_shellbag_cleaner()
        print()
        check_console_history()
        print()
        check_java_processes()
        print()
        check_system_access()
        print()
        check_prefetch_settings()
        print()
        check_prefetch_integrity()
        print()
        check_registry_settings()
        
        print()
        print_section_header("ANALYSIS COMPLETED")
        print(f"  {Colors.GREEN}[+] All checks completed successfully{Colors.RESET}")
        
    except KeyboardInterrupt:
        print(f"\n  {Colors.YELLOW}[!] Analysis interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n  {Colors.RED}[!] Critical error: {str(e)[:35]}...{Colors.RESET}")
    
    input(f"\n  {Colors.YELLOW}[?] Press Enter to return to main menu...{Colors.RESET}")

def main():
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print(f"{Colors.RED}[!] Please run as administrator!{Colors.RESET}")
            input("Press Enter to exit...")
            sys.exit(1)
        
        while True:
            choice = print_menu()
            
            if choice == '1':
                cleaning_detection()
            elif choice == '2':
                os.system('cls')
                print_ascii_art()
                print(f"{Colors.GRAY}════════════════════════════════════════════════════════════════════════")
                print(f"        Developer: avarice | Discord Project: https://discord.gg/ResidenceScreenShare")
                print(f"════════════════════════════════════════════════════════════════════════{Colors.RESET}")
                print()
                check_running_scripts()
                input(f"\n  {Colors.YELLOW}[?] Press Enter to return to main menu...{Colors.RESET}")
            elif choice == '3':
                print(f"\n  {Colors.GREEN}[+] Exiting... Goodbye!{Colors.RESET}")
                break
            else:
                print(f"\n  {Colors.RED}[!] Invalid option. Please try again.{Colors.RESET}")
                time.sleep(1)
                
    except KeyboardInterrupt:
        print(f"\n  {Colors.YELLOW}[!] Program interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n  {Colors.RED}[!] Fatal error: {str(e)}{Colors.RESET}")
    
    input(f"\n  {Colors.YELLOW}[?] Press Enter to exit...{Colors.RESET}")

if __name__ == "__main__":
    main()

