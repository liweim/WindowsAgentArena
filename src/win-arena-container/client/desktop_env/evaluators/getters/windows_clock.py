import logging
import re
import xml.etree.ElementTree as ET

logger = logging.getLogger("desktopenv.metric.windows_clock")


def _format_timer_duration_candidates(hours: int, minutes: int, seconds: int) -> list[str]:
    def unit(value, singular, plural):
        return singular if value == 1 else plural

    hour_part = f"{hours} {unit(hours, 'hour', 'hours')}"
    minute_part = f"{minutes} {unit(minutes, 'minute', 'minutes')}"
    second_part = f"{seconds} {unit(seconds, 'second', 'seconds')}"

    candidates = [f"{hour_part} {minute_part} {second_part}"]
    if hours:
        candidates.append(f"{hour_part} {minute_part}")
        candidates.append(hour_part)
    if minutes:
        candidates.append(f"{minute_part} {second_part}")
        candidates.append(minute_part)
    if seconds:
        candidates.append(second_part)

    return list(dict.fromkeys(candidates))


def _element_has_running_pause(element: ET.Element) -> bool:
    return any(child.attrib.get("name") == "Timer running, Pause" for child in element.iter())


def _timer_started_in_accessibility_tree(accessibility_tree: str, hours: int, minutes: int, seconds: int) -> bool:
    candidates = _format_timer_duration_candidates(hours, minutes, seconds)
    try:
        root = ET.fromstring(accessibility_tree)
    except ET.ParseError:
        logger.exception("Failed to parse accessibility tree for Clock timer fallback")
        return False

    for element in root.iter():
        name = element.attrib.get("name", "")
        if any(re.search(rf"\b{re.escape(candidate)}\b", name) for candidate in candidates):
            if _element_has_running_pause(element):
                logger.info("Clock timer matched running timer: %s", name)
                return True

    logger.info("Clock timer found no running timer for candidates: %s", candidates)
    return False


def get_check_if_timer_started(env, config: dict) -> str:
    hours = int(config["hours"])
    minutes = int(config["minutes"])
    seconds = int(config["seconds"])

    accessibility_tree = env.controller.get_accessibility_tree(backend="uia")
    if accessibility_tree and _timer_started_in_accessibility_tree(
        accessibility_tree,
        hours,
        minutes,
        seconds,
    ):
        return "True"

    return "False"

def get_check_if_world_clock_exists(env, config: dict) -> str:
    return env.controller.get_vm_check_if_world_clock_exists(config["city"], config["country"])
