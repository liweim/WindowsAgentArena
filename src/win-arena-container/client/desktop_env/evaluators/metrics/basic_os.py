def check_gnome_favorite_apps(apps_str: str, rule):
    # parse the string like "['thunderbird.desktop', 'vim.desktop', 'google-chrome.desktop']"
    # to a list of strings
    apps = eval(apps_str)

    expected_apps = rule["expected"]

    if len(apps) != len(expected_apps):
        return 0

    if set(apps) == set(expected_apps):
        return 1
    else:
        return 0


def is_utc_0(timedatectl_output):
    """
    Format as:
    Local time: Thu 2024-01-25 12:56:06 WET
           Universal time: Thu 2024-01-25 12:56:06 UTC
                 RTC time: Thu 2024-01-25 12:56:05
                Time zone: Atlantic/Faroe (WET, +0000)
System clock synchronized: yes
              NTP service: inactive
          RTC in local TZ: no
    """

    utc_line = timedatectl_output.split("\n")[3]

    if utc_line.endswith("+0000)"):
        return 1
    else:
        return 0


def check_text_enlarged(scaling_factor_str):
    scaling_factor = float(scaling_factor_str)
    if scaling_factor > 1.0:
        return 1
    else:
        return 0


def check_moved_jpgs(directory_list, rule):
    expected_jpgs = rule["expected"]
    moved_jpgs = [node['name'] for node in directory_list['children']]

    if len(moved_jpgs) != len(expected_jpgs):
        return 0

    if set(moved_jpgs) == set(expected_jpgs):
        return 1
    else:
        return 0


def is_in_vm_clickboard(config, terminal_output):
    print("terminal_output: ")
    print(terminal_output)
    print("config: ")
    print(config)
    expected_results = config["expected"]
    # check if terminal_output has expected results
    if not isinstance(expected_results, list):
        return 1 if expected_results in terminal_output else 0
    else:
        return 1 if all(result in terminal_output for result in expected_results) else 0


def check_magnifier_ui_open(result, rule):
    """
    Check that Windows Magnifier is running.

    Magnifier does not reliably expose a node in the accessibility tree when
    it is minimized, in full-screen mode, or when another window has focus.
    Requiring such a node therefore turns a valid background/full-screen
    Magnifier session into a false negative.  Tasks that specifically require
    a visible Magnifier control window can opt into the stricter tree check.
    """
    if not isinstance(result, (list, tuple)) or len(result) != 2:
        return 0.

    process, tree = result
    print("process: ", str(process))
    print("tree: ", str(tree))

    process_running = "magnify.exe" in str(process).lower()
    if rule.get("require_ui_tree", False):
        return float(process_running and "magnifier" in str(tree).lower())
    return float(process_running)


def check_narrator_enabled(result, rule):
    """
    Checks whether Narrator is enabled.
    """
    return "narrator.exe" in str(result).lower()
