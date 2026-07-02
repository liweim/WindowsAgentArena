import json
import logging
import os
import os.path
import shutil
import sqlite3
import tempfile
import time
import traceback
import uuid
from datetime import datetime, timedelta
from typing import Any, Union, Optional
from typing import Dict, List

import requests
from playwright.sync_api import sync_playwright, TimeoutError
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive, GoogleDriveFile, GoogleDriveFileList
from requests_toolbelt.multipart.encoder import MultipartEncoder

from desktop_env.controllers.python import PythonController
from desktop_env.evaluators.metrics.utils import compare_urls

logger = logging.getLogger("desktopenv.setup")

FILE_PATH = os.path.dirname(os.path.abspath(__file__))


class SetupController:
    def __init__(self, vm_ip: str, cache_dir: str):
        self.vm_ip: str = vm_ip
        self.http_server: str = f"http://{vm_ip}:5000"
        self.http_server_setup_root: str = f"http://{vm_ip}:5000/setup"
        self.cache_dir: str = cache_dir
        self.task_config_dir: Optional[str] = None

    def reset_cache_dir(self, cache_dir: str):
        self.cache_dir = cache_dir

    def set_task_config_dir(self, task_config_dir: Optional[str]):
        self.task_config_dir = task_config_dir

    def _resolve_local_path(self, local_path: str) -> str:
        if os.path.isabs(local_path):
            return local_path
        if self.task_config_dir:
            candidate = os.path.normpath(os.path.join(self.task_config_dir, local_path))
            if os.path.exists(candidate):
                return candidate
        return local_path

    def setup(self, config: List[Dict[str, Any]]):
        """
        Args:
            config (List[Dict[str, Any]]): list of dict like {str: Any}. each
              config dict has the structure like
                {
                    "type": str, corresponding to the `_{:}_setup` methods of
                      this class
                    "parameters": dict like {str, Any} providing the keyword
                      parameters
                }
        """

        for cfg in config:
            config_type: str = cfg["type"]
            parameters: Dict[str, Any] = cfg["parameters"]

            # Assumes all the setup the functions should follow this name
            # protocol
            setup_function: str = "_{:}_setup".format(config_type)
            assert hasattr(self, setup_function), f'Setup controller cannot find init function {setup_function}'
            getattr(self, setup_function)(**parameters)

            logger.info("SETUP: %s(%s)", setup_function, str(parameters))
    
    def _set_default_browser_setup(self, browser: str):
        # Comment: this function doesn't work. It does set the registry key correctly, but looks like there's some security mechanism that prevents the key by itself from setting the default browser
        key_path = r"HKCU:Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice"  
        setting_path = r"ProgId"  
        
        browser_prog_ids = {  
            "chrome": "ChromeHTML",  
            "edge": "MSEdgeHTM",  
        }  
    
        try:  
            browser_prog_id = browser_prog_ids[browser.lower()]  
        except KeyError:  
            return f"Invalid browser: {browser}. Choose from 'chrome', 'edge', 'firefox', 'ie'."  
    
        try:  
            controller = PythonController(self.vm_ip)
            controller.set_registry_key(key_path, setting_path, browser_prog_id)  
        except Exception as e:  
            return str(e)  
    
        return f"Default browser set to {browser}" 

    def _download_setup(self, files: List[Dict[str, str]]):
        """
        Args:
            files (List[Dict[str, str]]): files to download. lisf of dict like
              {
                "url": str, the url to download
                "path": str, the path on the VM to store the downloaded file
              }
        """

        # if not config:
        # return
        # if not 'download' in config:
        # return
        # for url, path in config['download']:
        for f in files:
            url: str = f["url"]
            path: str = f["path"]
            cache_path: str = os.path.join(self.cache_dir, "{:}_{:}".format(
                uuid.uuid5(uuid.NAMESPACE_URL, url),
                os.path.basename(path)))
            if not url or not path:
                raise Exception(f"Setup Download - Invalid URL ({url}) or path ({path}).")

            if not os.path.exists(cache_path):
                max_retries = 3
                downloaded = False
                e = None
                for i in range(max_retries):
                    try:
                        response = requests.get(url, stream=True)
                        response.raise_for_status()

                        with open(cache_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        logger.info("File downloaded successfully")
                        downloaded = True
                        break

                    except requests.RequestException as e:
                        logger.error(
                            f"Failed to download {url} caused by {e}. Retrying... ({max_retries - i - 1} attempts left)")
                if not downloaded:
                    raise requests.RequestException(f"Failed to download {url}. No retries left. Error: {e}")

            form = MultipartEncoder({
                "file_path": path,
                "file_data": (os.path.basename(path), open(cache_path, "rb"))
            })
            headers = {"Content-Type": form.content_type}
            logger.debug(form.content_type)

            # send request to server to upload file
            try:
                logger.debug("REQUEST ADDRESS: %s", self.http_server + "/setup" + "/upload")
                response = requests.post(self.http_server + "/setup" + "/upload", headers=headers, data=form)
                if response.status_code == 200:
                    logger.info("Command executed successfully: %s", response.text)
                else:
                    logger.error("Failed to upload file. Status code: %s", response.text)
            except requests.exceptions.RequestException as e:
                logger.error("An error occurred while trying to send the request: %s", e)

    def _upload_file_setup(self, files: List[Dict[str, str]]):
        """
        Args:
            files (List[Dict[str, str]]): files to download. lisf of dict like
              {
                "local_path": str, the local path to the file to upload
                "path": str, the path on the VM to store the downloaded file
              }
        """
        for f in files:
            local_path: str = self._resolve_local_path(f["local_path"])
            path: str = f["path"]

            if not os.path.exists(local_path):
                logger.error(f"Setup Upload - Invalid local path ({local_path}).")
                return

            form = MultipartEncoder({
                "file_path": path,
                "file_data": (os.path.basename(path), open(local_path, "rb"))
            })
            headers = {"Content-Type": form.content_type}
            logger.debug(form.content_type)

            # send request to server to upload file
            try:
                logger.debug("REQUEST ADDRESS: %s", self.http_server + "/setup" + "/upload")
                response = requests.post(self.http_server + "/setup" + "/upload", headers=headers, data=form)
                if response.status_code == 200:
                    logger.info("Command executed successfully: %s", response.text)
                else:
                    logger.error("Failed to upload file. Status code: %s", response.text)
            except requests.exceptions.RequestException as e:
                logger.error("An error occurred while trying to send the request: %s", e)

    def _change_wallpaper_setup(self, path: str):
        # if not config:
        # return
        # if not 'wallpaper' in config:
        # return

        # path = config['wallpaper']
        if not path:
            raise Exception(f"Setup Wallpaper - Invalid path ({path}).")

        payload = json.dumps({"path": path})
        headers = {
            'Content-Type': 'application/json'
        }

        # send request to server to change wallpaper
        try:
            response = requests.post(self.http_server + "/setup" + "/change_wallpaper", headers=headers, data=payload)
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
            else:
                logger.error("Failed to change wallpaper. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)

    def _tidy_desktop_setup(self, **config):
        raise NotImplementedError()

    def _open_setup(self, path: str):
        # if not config:
        # return
        # if not 'open' in config:
        # return
        # for path in config['open']:
        if not path:
            raise Exception(f"Setup Open - Invalid path ({path}).")

        lower_path = path.lower()
        if lower_path.endswith((".xlsx", ".xls", ".ods")):
            self._execute_setup(
                r'taskkill /IM soffice.bin /F 2>NUL & taskkill /IM soffice.exe /F 2>NUL & taskkill /IM scalc.exe /F 2>NUL & '
                r'rmdir /S /Q "C:\Temp\winarena-libreoffice-profile" 2>NUL & mkdir "C:\Temp\winarena-libreoffice-profile"',
                shell=True,
            )
            self._launch_setup([
                r"C:\Program Files\LibreOffice\program\scalc.exe",
                "--norestore",
                "--nolockcheck",
                "-env:UserInstallation=file:///C:/Temp/winarena-libreoffice-profile",
                path,
            ])
            time.sleep(2)
            return
        if lower_path.endswith((".docx", ".doc", ".odt")):
            self._execute_setup(
                r'taskkill /IM soffice.bin /F 2>NUL & taskkill /IM soffice.exe /F 2>NUL & taskkill /IM swriter.exe /F 2>NUL & '
                r'rmdir /S /Q "C:\Temp\winarena-libreoffice-profile" 2>NUL & mkdir "C:\Temp\winarena-libreoffice-profile"',
                shell=True,
            )
            self._launch_setup([
                r"C:\Program Files\LibreOffice\program\swriter.exe",
                "--norestore",
                "--nolockcheck",
                "-env:UserInstallation=file:///C:/Temp/winarena-libreoffice-profile",
                path,
            ])
            time.sleep(2)
            return

        payload = json.dumps({"path": path})
        headers = {
            'Content-Type': 'application/json'
        }

        # send request to server to open file
        try:
            response = requests.post(self.http_server + "/setup" + "/open_file", headers=headers, data=payload)
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
                time.sleep(2)
            else:
                logger.error("Failed to open file. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)

    def _launch_setup(self, command: Union[str, List[str]], shell: bool = False):
        if not command:
            raise Exception("Empty command to launch.")

        if not shell and isinstance(command, str) and len(command.split()) > 1:
            logger.warning("Command should be a list of strings. Now it is a string. Will split it by space.")
            command = command.split()

        if isinstance(command, list) and any(arg in ("google-chrome", "chrome") for arg in command):
            has_remote_debugging = any(str(arg).startswith("--remote-debugging-port=") for arg in command)
            has_user_data_dir = any(str(arg).startswith("--user-data-dir=") for arg in command)
            is_accessibility_chrome = "--force-renderer-accessibility" in command
            if has_remote_debugging and is_accessibility_chrome and not has_user_data_dir:
                command.append(r"--user-data-dir=C:\Temp\winarena-chrome-debug")
            for flag in ("--no-first-run", "--no-default-browser-check"):
                if has_remote_debugging and is_accessibility_chrome and flag not in command:
                    command.append(flag)

        payload = json.dumps({"command": command, "shell": shell})
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(self.http_server + "/setup" + "/launch", headers=headers, data=payload)
            logger.info(f"launch_setup(), response: {payload}")
            logger.info(f"launch_setup(), response: {response}")
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
            else:
                logger.error("Failed to launch application. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)

    def _execute_setup(
            self,
            command: List[str],
            stdout: str = "",
            stderr: str = "",
            shell: bool = False,
            until: Optional[Dict[str, Any]] = None
    ):
        if not command:
            raise Exception("Empty command to launch.")

        until: Dict[str, Any] = until or {}
        terminates: bool = False
        nb_failings = 0

        payload = json.dumps({"command": command, "shell": shell})
        headers = {"Content-Type": "application/json"}

        while not terminates:
            try:
                response = requests.post(self.http_server + "/setup" + "/execute", headers=headers, data=payload)
                if response.status_code == 200:
                    results: Dict[str, str] = response.json()
                    if stdout:
                        with open(os.path.join(self.cache_dir, stdout), "w") as f:
                            f.write(results["output"])
                    if stderr:
                        with open(os.path.join(self.cache_dir, stderr), "w") as f:
                            f.write(results["error"])
                    logger.info("Command executed successfully: %s -> %s"
                                , " ".join(command) if isinstance(command, list) else command
                                , response.text
                                )
                else:
                    logger.error("Failed to launch application. Status code: %s", response.text)
                    results = None
                    nb_failings += 1
            except requests.exceptions.RequestException as e:
                logger.error("An error occurred while trying to send the request: %s", e)
                traceback.print_exc()

                results = None
                nb_failings += 1

            if len(until) == 0:
                terminates = True
            elif results is not None:
                terminates = "returncode" in until and results["returncode"] == until["returncode"] \
                             or "stdout" in until and until["stdout"] in results["output"] \
                             or "stderr" in until and until["stderr"] in results["error"]
            terminates = terminates or nb_failings >= 5
            if not terminates:
                time.sleep(0.3)

    def _prepare_thunderbird_profile_setup(
            self,
            archive_path: str = r"C:\Users\Docker\Downloads\thunderbird-profile.tar.gz",
            profile_name: str = "t5q2a5hp.default-release",
    ):
        command = (
            "$ErrorActionPreference = 'Stop'; "
            "Stop-Process -Name thunderbird -Force -ErrorAction SilentlyContinue; "
            "$profileRoot = 'C:\\Users\\Docker\\AppData\\Roaming'; "
            "$legacyRoot = Join-Path $profileRoot '.thunderbird'; "
            "if (Test-Path $legacyRoot) { Remove-Item $legacyRoot -Recurse -Force }; "
            f"tar.exe -xzf '{archive_path}' -C $profileRoot; "
            f"$prefs = 'C:\\Users\\Docker\\AppData\\Roaming\\.thunderbird\\{profile_name}\\prefs.js'; "
            "$content = Get-Content -Path $prefs -Raw; "
            "$content = $content -replace 'user_pref\\(\\\"mail\\.identity\\.id1\\.draft_folder\\\", \\\"[^\\\"]*\\\"\\);', "
            "'user_pref(\"mail.identity.id1.draft_folder\", \"mailbox://nobody@Local%20Folders/Drafts\");'; "
            "$content = $content -replace 'user_pref\\(\\\"mail\\.identity\\.id1\\.drafts_folder_picker_mode\\\", \\\"[^\\\"]*\\\"\\);', "
            "'user_pref(\"mail.identity.id1.drafts_folder_picker_mode\", \"1\");'; "
            "Set-Content -Path $prefs -Value $content -Encoding ASCII; "
            f"New-Item -ItemType File -Path 'C:\\Users\\Docker\\AppData\\Roaming\\.thunderbird\\{profile_name}\\Mail\\Local Folders\\Drafts' -Force | Out-Null"
        )
        self._execute_setup([
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ])

    def _command_setup(self, command: List[str], **kwargs):
        self._execute_setup(command, **kwargs)

    def _sleep_setup(self, seconds: float):
        time.sleep(seconds)

    def _act_setup(self, action_seq: List[Union[Dict[str, Any], str]]):
        # TODO
        raise NotImplementedError()

    def _replay_setup(self, trajectory: str):
        """
        Args:
            trajectory (str): path to the replay trajectory file
        """

        # TODO
        raise NotImplementedError()

    def _activate_window_setup(self, window_name: str, strict: bool = False, by_class: bool = False):
        if not window_name:
            raise Exception(f"Setup Open - Invalid path ({window_name}).")

        payload = json.dumps({"window_name": window_name, "strict": strict, "by_class": by_class})
        headers = {
            'Content-Type': 'application/json'
        }

        # send request to server to open file
        try:
            response = requests.post(self.http_server + "/setup" + "/activate_window", headers=headers, data=payload)
            logger.info(f"activate window setup RESPONSE: {response}, {response.text}")
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
            else:
                logger.error(f"Failed to activate window {window_name}. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)

    def _close_all_setup(self):
        payload = json.dumps({})
        headers = {
            'Content-Type': 'application/json'
        }

        # send request to server to open file
        try:
            response = requests.post(self.http_server + "/setup" + "/close_all", headers=headers, data=payload)
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
            else:
                logger.error(f"Failed to close all windows. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)

    def _clean_up_files(self):
        payload = json.dumps({})
        headers = {
            'Content-Type': 'application/json'
        }

        # send request to server to open file
        try:
            response = requests.post(self.http_server + "/setup" + "/clear_task_files", headers=headers, data=payload)
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
            else:
                logger.error(f"Failed to clear task files. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)


    def _close_window_setup(self, window_name: str, strict: bool = False, by_class: bool = False):
        if not window_name:
            raise Exception(f"Setup Open - Invalid path ({window_name}).")

        payload = json.dumps({"window_name": window_name, "strict": strict, "by_class": by_class})
        headers = {
            'Content-Type': 'application/json'
        }

        # send request to server to open file
        try:
            response = requests.post(self.http_server + "/setup" + "/close_window", headers=headers, data=payload)
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
            else:
                logger.error(f"Failed to close window {window_name}. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)

    # File Explorer setup
    def _create_folder_setup(self, path: str):
        if not path:
            raise Exception(f"Setup Create Folder - Invalid path ({path}).")

        payload = json.dumps({"path": path})
        headers = {
            'Content-Type': 'application/json'
        }

        # send request to server to create folder
        try:
            response = requests.post(self.http_server + "/setup" + "/create_folder", headers=headers, data=payload)
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
            else:
                logger.error("Failed to create folder. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)

    def _create_file_setup(self, path: str, content: str = ""):
        if not path:
            raise Exception(f"Setup Create File - Invalid path ({path}).")

        payload = json.dumps({"path": path, "content": content})
        headers = {
            'Content-Type': 'application/json'
        }

        # send request to server to create text file
        try:
            response = requests.post(self.http_server + "/setup" + "/create_file", headers=headers, data=payload)
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
            else:
                logger.error("Failed to create file. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)


    def _recycle_file_setup(self, path: str):
        if not path:
            raise Exception(f"Setup recycle file - Invalid path ({path}).")

        payload = json.dumps({"path": path})
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(self.http_server + "/setup" + "/recycle", headers=headers, data=payload)
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
            else:
                logger.error("Failed to recycle file. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)

    def _connect_browser_over_cdp(
            self,
            playwright,
            remote_debugging_url: str,
            browser_name: str,
            attempts: int = 15,
            initial_wait_seconds: float = 2,
            retry_wait_seconds: float = 5
    ):
        if initial_wait_seconds:
            time.sleep(initial_wait_seconds)

        for attempt in range(attempts):
            try:
                return playwright.chromium.connect_over_cdp(remote_debugging_url)
            except Exception as e:
                if attempt < attempts - 1:
                    logger.info(
                        "%s DevTools endpoint is not ready yet, retrying (%d/%d): %s",
                        browser_name,
                        attempt + 1,
                        attempts,
                        e
                    )
                    time.sleep(retry_wait_seconds)
                else:
                    logger.error("Failed to connect to %s after multiple attempts: %s", browser_name, e)
                    raise e

    # Chrome setup
    def _chrome_open_tabs_setup(self, urls_to_open: List[str]):

        host = self.vm_ip
        port = 9222  # fixme: this port is hard-coded, need to be changed from config file

        remote_debugging_url = f"http://{host}:{port}"
        logger.info("Connect to Chrome @: %s", remote_debugging_url)
        logger.debug("PLAYWRIGHT ENV: %s", repr(os.environ))
        with sync_playwright() as p:
            browser = self._connect_browser_over_cdp(p, remote_debugging_url, "Chrome")

            if not browser:
                return

            logger.info("Opening %s...", urls_to_open)
            for i, url in enumerate(urls_to_open):
                # Use the first context (which should be the only one if using default profile)
                if i == 0:
                    context = browser.contexts[0]

                if i == 0:
                    startup_pages = [
                        page for page in context.pages
                        if page.url.startswith(("about:", "chrome://"))
                    ]
                    page = startup_pages[0] if startup_pages else context.new_page()
                else:
                    page = context.new_page()
                try:
                    page.goto(url, timeout=60000)
                except:
                    logger.warning("Opening %s exceeds time limit", url)  # only for human test
                logger.info(f"Opened tab {i + 1}: {url}")

            self._close_chrome_startup_tabs(remote_debugging_url, urls_to_open)

            # Do not close the context or browser; they will remain open after script ends
            return browser, context

    def _close_chrome_startup_tabs(self, remote_debugging_url: str, urls_to_keep: List[str]):
        keep_urls = set(urls_to_keep)
        startup_titles = {"New Tab", "Sign in to Chrome", "What's New - Google Chrome"}
        try:
            response = requests.get(f"{remote_debugging_url}/json/list", timeout=3)
            response.raise_for_status()
            targets = response.json()
        except Exception as e:
            logger.warning("Failed to list Chrome startup tabs: %s", e)
            return

        for target in targets:
            target_id = target.get("id")
            target_url = target.get("url")
            target_title = target.get("title")
            target_type = target.get("type")
            is_startup_page = (
                target_url not in keep_urls
                and (
                    str(target_url).startswith(("chrome://", "about:"))
                    or target_title in startup_titles
                )
            )
            if target_type == "page" and target_id and is_startup_page:
                try:
                    requests.get(f"{remote_debugging_url}/json/close/{target_id}", timeout=3)
                    logger.info("Closed Chrome startup tab/window: %s (%s)", target_title, target_url)
                except Exception as e:
                    logger.warning("Failed to close Chrome startup tab/window %s: %s", target_url, e)
            
    def _edge_open_tabs_setup(self, urls_to_open: List[str]):

        host = self.vm_ip
        port = 9222  # fixme: this port is hard-coded, need to be changed from config file

        remote_debugging_url = f"http://{host}:{port}"
        logger.info("Connect to Microsoft Edge @: %s", remote_debugging_url)
        logger.debug("PLAYWRIGHT ENV: %s", repr(os.environ))
        with sync_playwright() as p:
            browser = self._connect_browser_over_cdp(p, remote_debugging_url, "Microsoft Edge")

            if not browser:
                return

            logger.info("Opening %s...", urls_to_open)
            for i, url in enumerate(urls_to_open):
                # Use the first context (which should be the only one if using default profile)
                if i == 0:
                    context = browser.contexts[0]

                page = context.new_page()  # Create a new page (tab) within the existing context
                try:
                    page.goto(url, timeout=60000)
                except:
                    logger.warning("Opening %s exceeds time limit", url)  # only for human test
                logger.info(f"Opened tab {i + 1}: {url}")

                if i == 0:
                    # clear the default tab
                    default_page = context.pages[0]
                    default_page.close()

            # Do not close the context or browser; they will remain open after script ends
            return browser, context

    def _chrome_close_tabs_setup(self, urls_to_close: List[str]):
        time.sleep(5)  # Wait for Chrome to finish launching

        host = self.vm_ip
        port = 9222  # fixme: this port is hard-coded, need to be changed from config file

        remote_debugging_url = f"http://{host}:{port}"
        with sync_playwright() as p:
            browser = self._connect_browser_over_cdp(p, remote_debugging_url, "Chrome")

            if not browser:
                return

            for i, url in enumerate(urls_to_close):
                # Use the first context (which should be the only one if using default profile)
                if i == 0:
                    context = browser.contexts[0]

                for page in context.pages:

                    # if two urls are the same, close the tab
                    if compare_urls(page.url, url):
                        context.pages.pop(context.pages.index(page))
                        page.close()
                        logger.info(f"Closed tab {i + 1}: {url}")
                        break

            # Do not close the context or browser; they will remain open after script ends
            return browser, context

    def _chrome_execute_script_setup(
            self,
            script: str,
            url: Optional[str] = None,
            url_prefix: Optional[str] = None,
            timeout: int = 30000,
            wait_seconds: float = 0
    ):
        if not url and not url_prefix:
            raise ValueError("chrome_execute_script requires either url or url_prefix")

        host = self.vm_ip
        port = 9222  # fixme: this port is hard-coded, need to be changed from config file

        remote_debugging_url = f"http://{host}:{port}"
        target_prefix = url_prefix or url
        with sync_playwright() as p:
            browser = self._connect_browser_over_cdp(p, remote_debugging_url, "Chrome")

            if not browser:
                return

            target_page = None
            target_context = browser.contexts[0]
            for context in browser.contexts:
                for page in context.pages:
                    if page.url.startswith(target_prefix):
                        target_page = page
                        target_context = context
                        break
                if target_page:
                    break

            if not target_page and url:
                startup_pages = [
                    page for page in target_context.pages
                    if page.url.startswith(("about:", "chrome://"))
                ]
                target_page = startup_pages[0] if startup_pages else target_context.new_page()
                try:
                    target_page.goto(url, timeout=60000)
                    logger.info("Opened tab for Chrome script: %s", url)
                except Exception as e:
                    logger.warning("Opening %s exceeds time limit: %s", url, e)
                self._close_chrome_startup_tabs(remote_debugging_url, [url])

            if not target_page:
                logger.warning("No Chrome tab matched URL prefix: %s", target_prefix)
                return

            if wait_seconds:
                time.sleep(wait_seconds)

            try:
                target_page.wait_for_load_state("domcontentloaded", timeout=timeout)
                target_page.evaluate(script)
                logger.info("Executed Chrome script on tab: %s", target_page.url)
            except Exception as e:
                logger.warning("Failed to execute Chrome script on %s: %s", target_page.url, e)

    @staticmethod
    def _build_youtube_live_caption_prep_script(
            pause_video: bool = True,
            disable_youtube_captions: bool = True
    ) -> str:
        script_lines = [
            "async () => {",
            "  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));",
        ]
        if pause_video:
            script_lines.extend([
                "  for (let i = 0; i < 20; i++) {",
                "    const video = document.querySelector('video');",
                "    if (video) {",
                "      video.pause();",
                "      break;",
                "    }",
                "    await sleep(500);",
                "  }",
            ])
        if disable_youtube_captions:
            script_lines.extend([
                "  for (let i = 0; i < 20; i++) {",
                "    const captionsButton = document.querySelector('.ytp-subtitles-button');",
                "    if (captionsButton) {",
                "      const title = (captionsButton.getAttribute('title') || '').toLowerCase();",
                "      const isOn = captionsButton.getAttribute('aria-pressed') === 'true'",
                "        || captionsButton.classList.contains('ytp-button-active')",
                "        || title.includes('turn off');",
                "      if (isOn) captionsButton.click();",
                "      break;",
                "    }",
                "    await sleep(500);",
                "  }",
            ])
        script_lines.append("}")
        return "\n".join(script_lines)

    def _chrome_prepare_youtube_for_live_caption_setup(
            self,
            url: str,
            wait_seconds: float = 1,
            timeout: int = 30000,
            pause_video: bool = True,
            disable_youtube_captions: bool = True
    ):
        self._chrome_execute_script_setup(
            script=self._build_youtube_live_caption_prep_script(
                pause_video=pause_video,
                disable_youtube_captions=disable_youtube_captions,
            ),
            url=url,
            timeout=timeout,
            wait_seconds=wait_seconds,
        )

    def _chrome_pause_video_setup(
            self,
            url: str,
            wait_seconds: float = 1,
            timeout: int = 30000
    ):
        self._chrome_execute_script_setup(
            script="\n".join([
                "async () => {",
                "  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));",
                "  for (let i = 0; i < 20; i++) {",
                "    const video = document.querySelector('video');",
                "    if (video) {",
                "      video.pause();",
                "      break;",
                "    }",
                "    await sleep(500);",
                "  }",
                "}",
            ]),
            url=url,
            timeout=timeout,
            wait_seconds=wait_seconds,
        )

    # google drive setup
    def _googledrive_setup(self, **config):
        """ Clean google drive space (eliminate the impact of previous experiments to reset the environment)
        @args:
            config(Dict[str, Any]): contain keys
                settings_file(str): path to google drive settings file, which will be loaded by pydrive.auth.GoogleAuth()
                operation(List[str]): each operation is chosen from ['delete', 'upload']
                args(List[Dict[str, Any]]): parameters for each operation
            different args dict for different operations:
                for delete:
                    query(str): query pattern string to search files or folder in google drive to delete, please refer to
                        https://developers.google.com/drive/api/guides/search-files?hl=en about how to write query string.
                    trash(bool): whether to delete files permanently or move to trash. By default, trash=false, completely delete it.
                for mkdirs:
                    path(List[str]): the path in the google drive to create folder
                for upload:
                    path(str): remote url to download file
                    dest(List[str]): the path in the google drive to store the downloaded file
        """
        settings_file = config.get('settings_file', 'evaluation_examples/settings/googledrive/settings.yml')
        gauth = GoogleAuth(settings_file=settings_file)
        drive = GoogleDrive(gauth)

        def mkdir_in_googledrive(paths: List[str]):
            paths = [paths] if type(paths) != list else paths
            parent_id = 'root'
            for p in paths:
                q = f'"{parent_id}" in parents and title = "{p}" and mimeType = "application/vnd.google-apps.folder" and trashed = false'
                folder = drive.ListFile({'q': q}).GetList()
                if len(folder) == 0:  # not exists, create it
                    parents = {} if parent_id == 'root' else {'parents': [{'id': parent_id}]}
                    file = drive.CreateFile({'title': p, 'mimeType': 'application/vnd.google-apps.folder', **parents})
                    file.Upload()
                    parent_id = file['id']
                else:
                    parent_id = folder[0]['id']
            return parent_id

        for oid, operation in enumerate(config['operation']):
            if operation == 'delete':  # delete a specific file
                # query pattern string, by default, remove all files/folders not in the trash to the trash
                params = config['args'][oid]
                q = params.get('query', '')
                trash = params.get('trash', False)
                q_file = f"( {q} ) and mimeType != 'application/vnd.google-apps.folder'" if q.strip() else "mimeType != 'application/vnd.google-apps.folder'"
                filelist: GoogleDriveFileList = drive.ListFile({'q': q_file}).GetList()
                q_folder = f"( {q} ) and mimeType = 'application/vnd.google-apps.folder'" if q.strip() else "mimeType = 'application/vnd.google-apps.folder'"
                folderlist: GoogleDriveFileList = drive.ListFile({'q': q_folder}).GetList()
                for file in filelist:  # first delete file, then folder
                    file: GoogleDriveFile
                    if trash:
                        file.Trash()
                    else:
                        file.Delete()
                for folder in folderlist:
                    folder: GoogleDriveFile
                    # note that, if a folder is trashed/deleted, all files and folders in it will be trashed/deleted
                    if trash:
                        folder.Trash()
                    else:
                        folder.Delete()
            elif operation == 'mkdirs':
                params = config['args'][oid]
                mkdir_in_googledrive(params['path'])
            elif operation == 'upload':
                params = config['args'][oid]
                url = params['url']
                with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmpf:
                    response = requests.get(url, stream=True)
                    response.raise_for_status()
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            tmpf.write(chunk)
                    tmpf.close()
                    paths = [params['path']] if params['path'] != list else params['path']
                    parent_id = mkdir_in_googledrive(paths[:-1])
                    parents = {} if parent_id == 'root' else {'parents': [{'id': parent_id}]}
                    file = drive.CreateFile({'title': paths[-1], **parents})
                    file.SetContentFile(tmpf.name)
                    file.Upload()
                return
            else:
                raise ValueError('[ERROR]: not implemented clean type!')

    def _login_setup(self, **config):
        """ Login to a website with account and password information.
        @args:
            config(Dict[str, Any]): contain keys
                settings_file(str): path to the settings file
                platform(str): platform to login, implemented platforms include:
                    googledrive: https://drive.google.com/drive/my-drive

        """
        host = self.vm_ip
        port = 9222  # fixme: this port is hard-coded, need to be changed from config file

        remote_debugging_url = f"http://{host}:{port}"
        with sync_playwright() as p:
            browser = self._connect_browser_over_cdp(p, remote_debugging_url, "Chrome")
            if not browser:
                return

            context = browser.contexts[0]
            platform = config['platform']

            if platform == 'googledrive':
                url = 'https://drive.google.com/drive/my-drive'
                page = context.new_page()  # Create a new page (tab) within the existing context
                try:
                    page.goto(url, timeout=60000)
                except:
                    logger.warning("Opening %s exceeds time limit", url)  # only for human test
                logger.info(f"Opened new page: {url}")
                settings = json.load(open(config['settings_file']))
                email, password = settings['email'], settings['password']

                try:
                    page.wait_for_selector('input[type="email"]', state="visible", timeout=3000)
                    page.fill('input[type="email"]', email)
                    page.click('#identifierNext > div > button')
                    page.wait_for_selector('input[type="password"]', state="visible", timeout=5000)
                    page.fill('input[type="password"]', password)
                    page.click('#passwordNext > div > button')
                    page.wait_for_load_state('load', timeout=5000)
                except TimeoutError:
                    logger.info('[ERROR]: timeout when waiting for google drive login page to load!')
                    return

            else:
                raise NotImplementedError

            return browser, context
            
    def _update_browse_history_edge_setup(self, **config):
        db_path = os.path.join("desktop_env", "assets", "history_empty.sqlite")

        # copy a new history file in the tmp folder
        cache_path = os.path.join(self.cache_dir, "history_new.sqlite")
        shutil.copyfile(db_path, cache_path)
        db_path = cache_path

        history = config['history']

        for history_item in history:
            url = history_item['url']
            title = history_item['title']
            visit_time = datetime.now() - timedelta(seconds=history_item['visit_time_from_now_in_seconds'])

            # Chrome use ms from 1601-01-01 as timestamp
            epoch_start = datetime(1601, 1, 1)
            edge_timestamp  = int((visit_time - epoch_start).total_seconds() * 1000000)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute('''
                   INSERT INTO urls (url, title, visit_count, typed_count, last_visit_time, hidden)
                   VALUES (?, ?, ?, ?, ?, ?)
               ''', (url, title, 1, 0, edge_timestamp , 0))

            url_id = cursor.lastrowid

            cursor.execute('''
                   INSERT INTO visits (url, visit_time, from_visit, transition, segment_id, visit_duration)
                   VALUES (?, ?, ?, ?, ?, ?)
               ''', (url_id, edge_timestamp , 0, 805306368, 0, 0))

            conn.commit()
            conn.close()

        logger.info('Fake browsing history added successfully.')

        controller = PythonController(self.vm_ip)

        # get the path of the history file according to the platform
        os_type = controller.get_vm_platform()

        if os_type == 'Windows':
            edge_history_path = controller.execute_python_command(
                """import os; print(os.path.join(os.getenv('USERPROFILE'), "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "History"))""")[
                'output'].strip()
        elif os_type == 'Darwin':
            edge_history_path = controller.execute_python_command(
                """import os; print(os.path.join(os.getenv('HOME'), "Library", "Application Support", "Microsoft", "Edge", "Default", "History"))""")[
                'output'].strip()
        elif os_type == 'Linux':
            edge_history_path = controller.execute_python_command(
                "import os; print(os.path.join(os.getenv('HOME'), '.config', 'microsoft-edge', 'Default', 'History'))")[
                'output'].strip()
        else:
            raise Exception('Unsupported operating system')

        form = MultipartEncoder({
            "file_path": edge_history_path,
            "file_data": (os.path.basename(edge_history_path), open(db_path, "rb"))
        })
        headers = {"Content-Type": form.content_type}
        logger.debug(form.content_type)

        # send request to server to upload file
        try:
            logger.debug("REQUEST ADDRESS: %s", self.http_server + "/setup" + "/upload")
            response = requests.post(self.http_server + "/setup" + "/upload", headers=headers, data=form)
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
            else:
                logger.error("Failed to upload file. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)
        self._execute_setup(["sudo chown -R user:user /home/user/.config/microsoft-edge/Default/History"], shell=True)

    def _update_browse_history_setup(self, **config):
        db_path = os.path.join("desktop_env", "assets", "history_empty.sqlite")

        # copy a new history file in the tmp folder
        cache_path = os.path.join(self.cache_dir, "history_new.sqlite")
        shutil.copyfile(db_path, cache_path)
        db_path = cache_path

        history = config['history']

        for history_item in history:
            url = history_item['url']
            title = history_item['title']
            visit_time = datetime.now() - timedelta(seconds=history_item['visit_time_from_now_in_seconds'])

            # Chrome use ms from 1601-01-01 as timestamp
            epoch_start = datetime(1601, 1, 1)
            chrome_timestamp = int((visit_time - epoch_start).total_seconds() * 1000000)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute('''
                   INSERT INTO urls (url, title, visit_count, typed_count, last_visit_time, hidden)
                   VALUES (?, ?, ?, ?, ?, ?)
               ''', (url, title, 1, 0, chrome_timestamp, 0))

            url_id = cursor.lastrowid

            cursor.execute('''
                   INSERT INTO visits (url, visit_time, from_visit, transition, segment_id, visit_duration)
                   VALUES (?, ?, ?, ?, ?, ?)
               ''', (url_id, chrome_timestamp, 0, 805306368, 0, 0))

            conn.commit()
            conn.close()

        logger.info('Fake browsing history added successfully.')

        controller = PythonController(self.vm_ip)

        # get the path of the history file according to the platform
        os_type = controller.get_vm_platform()

        if os_type == 'Windows':
            chrome_history_path = controller.execute_python_command(
                """import os; print(os.path.join(os.getenv('USERPROFILE'), "AppData", "Local", "Google", "Chrome", "User Data", "Default", "History"))""")[
                'output'].strip()
        elif os_type == 'Darwin':
            chrome_history_path = controller.execute_python_command(
                """import os; print(os.path.join(os.getenv('HOME'), "Library", "Application Support", "Google", "Chrome", "Default", "History"))""")[
                'output'].strip()
        elif os_type == 'Linux':
            chrome_history_path = controller.execute_python_command(
                "import os; print(os.path.join(os.getenv('HOME'), '.config', 'google-chrome', 'Default', 'History'))")[
                'output'].strip()
        else:
            raise Exception('Unsupported operating system')

        form = MultipartEncoder({
            "file_path": chrome_history_path,
            "file_data": (os.path.basename(chrome_history_path), open(db_path, "rb"))
        })
        headers = {"Content-Type": form.content_type}
        logger.debug(form.content_type)

        # send request to server to upload file
        try:
            logger.debug("REQUEST ADDRESS: %s", self.http_server + "/setup" + "/upload")
            response = requests.post(self.http_server + "/setup" + "/upload", headers=headers, data=form)
            if response.status_code == 200:
                logger.info("Command executed successfully: %s", response.text)
            else:
                logger.error("Failed to upload file. Status code: %s", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while trying to send the request: %s", e)

        self._execute_setup(["sudo chown -R user:user /home/user/.config/google-chrome/Default/History"], shell=True)
