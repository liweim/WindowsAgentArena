import logging
from typing import Dict
import requests
import os

logger = logging.getLogger("desktopenv.getters.general")


def get_vm_command_line(env, config: Dict[str, str]):
    vm_ip = env.vm_ip
    port = 5000

    command = config["command"]
    shell = config.get("shell", False)
    # shell = True

    logger.info(f"COMMAND: {command}")
    logger.info(f"SHELL: {shell}")
    response = requests.post(f"http://{vm_ip}:{port}/execute", json={"command": command, "shell": shell})
    # response = requests.post("/execute", json={"command": command, "shell": shell})
    if response.status_code == 200:
        result = response.json()
        logger.info("VM CMD LINE: %s", result)
        return result["output"]
        # logger.info(f"CMD and SHELL: {command, shell}")
        # logger.info(f"RESPONSE succ: {response}")
        # return response.json()
    else:
        logger.error("Failed to get vm command line. Status code: %d", response.status_code)
        return None

def get_vm_command_error(env, config: Dict[str, str]):
    vm_ip = env.vm_ip
    port = 5000
    command = config["command"]
    shell = config.get("shell", False)

    response = requests.post(f"http://{vm_ip}:{port}/execute", json={"command": command, "shell": shell})

    print(response.json())

    if response.status_code == 200:
        return response.json()["error"]
    else:
        logger.error("Failed to get vm command line error. Status code: %d", response.status_code)
        return None


def get_vm_terminal_output(env, config: Dict[str, str]):
    return env.controller.get_terminal_output()


def get_sticky_notes_content(env, config: Dict[str, str]):
    command = [
        "python",
        "-c",
        (
            "import glob, os, sqlite3; "
            "base=os.path.join(os.environ['LOCALAPPDATA'], 'Packages', "
            "'Microsoft.MicrosoftStickyNotes_8wekyb3d8bbwe', 'LocalState'); "
            "paths=glob.glob(os.path.join(base, 'plum.sqlite')); out=[]\n"
            "for path in paths:\n"
            "    try:\n"
            "        con=sqlite3.connect(path); cur=con.cursor();\n"
            "        for table in ('Note', 'LegacyNote'):\n"
            "            try:\n"
            "                cols=[r[1] for r in cur.execute('PRAGMA table_info(%s)' % table)];\n"
            "                for col in ('Text', 'Body', 'Content'):\n"
            "                    if col in cols:\n"
            "                        out.extend(str(r[0] or '') for r in cur.execute('SELECT %s FROM %s' % (col, table)))\n"
            "            except Exception:\n"
            "                pass\n"
            "        con.close()\n"
            "    except Exception:\n"
            "        pass\n"
            "print('\\n'.join(out))"
        )
    ]
    return get_vm_command_line(env, {"command": command, "shell": config.get("shell", False)})
