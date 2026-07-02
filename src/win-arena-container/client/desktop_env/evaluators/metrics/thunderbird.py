import email
import datetime
import html
import json
import logging
import mailbox
import re
from zoneinfo import ZoneInfo
from email.header import decode_header, make_header
from email.message import Message
from email import policy
from typing import Iterable, List, Pattern, Dict, Match
from typing import Union, Any, TypeVar, Callable

from .utils import _match_record
from .utils import _match_value_to_rule as _match_pref

logger = logging.getLogger("desktopenv.metric.thunderbird")

V = TypeVar("Value")

_pref_pattern: Pattern[str] = re.compile(r'^user_pref\("(?P<key>(?:[^"]|\\")+)\", (?P<val>.+)\);$');


def check_thunderbird_prefs(result: str, rule: Dict[str, Dict[str, Dict[str, Any]]]):
    """
    Args:
        result (str): path to result file
        rule (Dict[str, Dict[str, Dict[str, Any]]]): dict like
          {
            "expect": {
                str: {
                    "method": str
                    "ref": something
                }
            }
            "unexpect": {
                str: {
                    "method": str
                    "ref": something
                }
            }
          }

    Returns:
        float
    """

    if result is None:
        return 0.

    expect_rules = rule.get("expect", {})
    unexpect_rules = rule.get("unexpect", {})

    expect_metrics = {k: False for k in expect_rules}
    unexpect_metric = True
    with open(result) as f:
        for l in f:
            match_: Match[str] = _pref_pattern.match(l.strip())
            if match_ is None:
                continue

            key: str = match_.group("key")
            # value: str = match_.group("val")
            # if value in {"true", "false"}:
            # value = value.title()
            # value: V = eval(value)
            value = json.loads(match_.group("val"))
            if key in expect_rules:
                logger.debug("K: %s, V: %s", key, repr(value))
                expect_metrics[key] = _match_pref(value, expect_rules[key])
            elif key in unexpect_rules:
                unexpect_metric = unexpect_metric and not _match_pref(value, unexpect_rules[key])

    return float(all(expect_metrics.values()) and unexpect_metric)


_value_processor: Callable[[str], str] = lambda val: val.replace("\\\"", "\"").replace("\\\\", "\\")
# _condition_pattern: Pattern[str] = re.compile(r'(?P<type>AND|OR) \((?P<key>[\w ]+),(?P<rel>[\w ' + '\'' + r']+),(?:"(?P<val2>(?:[^"]|\")+)"|(?P<val1>[^)]+))\)')
_condition_pattern: Pattern[str] = re.compile(
    r'\b(?:AND|OR) \((?:[\w ]+),(?:[\w ' + '\'' + r']+),(?:"(?:(?:[^"]|\")+)"|(?:[^)]+))\)|\bALL\b')


def check_thunderbird_filter(result: str, rules: Dict[str, List[Dict[str, str]]]) -> float:
    """
    Args:
        result (str): path to filter def file
        rules (Dict[str, List[Dict[str, str]]]): dict like
          {
            "expect": [{key: value}]
            "unexpect": [{key: value}]
          }

    Returns:
        float
    """

    if result is None:
        return 0.

    # read filter def file
    # a filter:
    # {
    #   "name": "Name",
    #   "enabled": "yes" | "no",
    #   "type": "17",
    #   "action": "Move to folder" | ...,
    #   "actionValue": ...,
    #   "condition": [...]
    # }
    filters: List[Dict[str, Union[str, List[str]]]] = []
    with open(result) as f:
        for l in f:
            if l.startswith("name="):
                filter_: Dict[str, Union[str, List[str]]] = {}
                filter_["name"] = _value_processor(l[6:-2])
            elif l.startswith("enabled="):
                filter_["enabled"] = _value_processor(l[9:-2])
            elif l.startswith("type="):
                filter_["type"] = _value_processor(l[6:-2])
            elif l.startswith("action="):
                filter_["action"] = _value_processor(l[8:-2])
            elif l.startswith("actionValue="):
                filter_["actionValue"] = _value_processor(l[13:-2])
            elif l.startswith("condition="):
                condition_str: str = _value_processor(l[11:-2])
                logger.debug("FILTER CONDITION: %s", condition_str)

                conditions: List[str] = \
                    _condition_pattern.findall(condition_str)
                logger.debug("FILTER CONDITIONS: %s", repr(conditions))

                filter_["condition"] = conditions
                logger.debug("FILTER %s", repr(filter_))
                filters.append(filter_)

    expect_metrics = [False] * len(rules.get("expect", []))
    unexpect_metric = True
    for flt in filters:
        for i, r in enumerate(rules.get("expect", [])):
            expect_metrics[i] = expect_metrics[i] or _match_record(r, flt)
        unexpect_metric = unexpect_metric and not any(_match_record(r, flt) for r in rules.get("unexpect", []))
    return float(all(expect_metrics) and unexpect_metric)


def check_thunderbird_folder(result: Union[str, List[str]], reference: Union[str, List[str]], **kwargs) -> float:
    """
    Check the file or file_list that each text file contains all messages in a folder in Thunderbird. Each message is started with `FROM - `.
    **kwargs:
        ignore_status (bool): for comparison, ignore the status (X-Mozilla-Status: 0000) of each message. default: False
        ignore_keys (bool): for comparison, ignore the keys (X-Mozilla-Keys: label) of each message. default: False
        remove_deleted (bool): ignore deleted messages which has status code 0008 or 0009. default: True
        remove_duplicate (bool): remove duplicate messages. default: True
    """

    def normalize_msg(msg, options):
        ignore_status = options.get('ignore_status', False)
        ignore_keys = options.get('ignore_keys', False)
        if ignore_status:
            msg = re.sub(r'X-Mozilla-Status\d?:[\s\d]+', '', msg)
        if ignore_keys:
            msg = re.sub(r'(X-Mozilla-Keys:[^\n]*?)\n(MIME-Version)', r'\2', msg)
        return msg.strip()

    def read_thunderbird_folder_file(path: str) -> str:
        with open(path, 'r') as inf:
            data = inf.read().strip()
            messages = []
            for mail in data.split('FROM - '):
                if mail.strip(): continue
                if kwargs.get('remove_deleted', True) and re.search(r'X-Mozilla-Status: 000[89]', mail): continue
                messages.append('FROM - ' + normalize_msg(mail, kwargs))
            if kwargs.get('remove_duplicate', True):
                messages = set(messages)
        return '\n'.join(sorted(messages))

    if type(reference) != list:
        result, reference = [result], [reference]
    for pred, gold in zip(result, reference):
        if pred is None: return .0
        mail1 = read_thunderbird_folder_file(pred)
        mail2 = read_thunderbird_folder_file(gold)
        if mail1 != mail2: return .0
    return 1.0


def _normalize_email_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[^A-Za-z0-9@.$]+", " ", value)
    return " ".join(value.split())


def _decode_header_value(value: Any) -> str:
    if value is None:
        return ""
    try:
        return str(make_header(decode_header(str(value))))
    except Exception:
        return str(value)


def _message_body(message: Message) -> str:
    body_parts: List[str] = []

    if message.is_multipart():
        parts = message.walk()
    else:
        parts = [message]

    for part in parts:
        if part.is_multipart():
            continue
        content_type = part.get_content_type()
        if content_type not in {"text/plain", "text/html"}:
            continue
        try:
            payload = part.get_payload(decode=True)
            charset = part.get_content_charset() or "utf-8"
            if payload is None:
                text = str(part.get_payload())
            else:
                text = payload.decode(charset, errors="replace")
        except Exception:
            text = str(part.get_payload())
        body_parts.append(text)

    return "\n".join(body_parts)


def _iter_messages(path: str) -> Iterable[Message]:
    try:
        for message in mailbox.mbox(path, factory=None):
            yield message
        return
    except Exception:
        pass

    with open(path, "rb") as f:
        raw = f.read()

    for chunk in raw.split(b"\nFrom "):
        chunk = chunk.strip()
        if not chunk:
            continue
        if not chunk.startswith(b"From "):
            chunk = b"From " + chunk
        try:
            yield email.message_from_bytes(chunk, policy=policy.default)
        except Exception:
            continue


def _message_score(message: Message, rules: Dict[str, Any]) -> float:
    expected_to = _normalize_email_text(rules.get("to", ""))
    expected_subject = _normalize_email_text(rules.get("subject", ""))
    actual_to = _normalize_email_text(_decode_header_value(message.get("to")))
    actual_subject = _normalize_email_text(_decode_header_value(message.get("subject")))

    if expected_to not in actual_to or actual_subject != expected_subject:
        return 0.

    body = _normalize_email_text(_message_body(message)).lower()
    body_points: List[List[str]] = rules.get("body_points", [])
    if not body_points:
        return 1.

    matched = 0
    for variants in body_points:
        if any(_normalize_email_text(variant).lower() in body for variant in variants):
            matched += 1

    return matched / len(body_points)


def check_thunderbird_email_composition(result: Union[str, List[str]], rules: Dict[str, Any]) -> float:
    """
    Score a Thunderbird composed/saved email from one or more mbox files.
    Required headers (`to`, `subject`) must match before body points score.
    Each body point is a list of acceptable variants and contributes equally.
    """

    if result is None:
        return 0.

    paths = result if isinstance(result, list) else [result]
    best_score = 0.
    for path in paths:
        if path is None:
            continue
        try:
            for message in _iter_messages(path):
                best_score = max(best_score, _message_score(message, rules))
        except Exception as exc:
            logger.warning("Failed to score Thunderbird composition %s: %s", path, exc)

    return best_score


def _calendar_timestamp_to_datetime(value: Any, timezone_name: str = "") -> Union[datetime.datetime, None]:
    if value is None or value == "":
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return datetime.datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            try:
                value = int(text)
            except Exception:
                return None
    try:
        number = int(value)
    except Exception:
        return None

    timezone = None
    if timezone_name:
        try:
            timezone = ZoneInfo(timezone_name)
        except Exception:
            timezone = None

    candidates = []
    for divisor in (1000000, 1000, 1):
        try:
            timestamp = number / divisor
            if timezone:
                candidates.append(
                    datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
                    .astimezone(timezone)
                    .replace(tzinfo=None)
                )
            candidates.append(datetime.datetime.fromtimestamp(timestamp))
        except Exception:
            pass
    for candidate in candidates:
        if 2000 <= candidate.year <= 2100:
            return candidate
    return None


def _calendar_event_text(event: Dict[str, Any]) -> str:
    parts = []
    values = list(event.items())
    for related in event.get("related", []):
        if isinstance(related, dict):
            values.extend(related.items())
    for key, value in values:
        if value is None:
            continue
        if isinstance(value, str):
            parts.append(value)
    return _normalize_email_text(" ".join(parts)).lower()


def _calendar_event_description_text(event: Dict[str, Any]) -> str:
    parts = []
    for key, value in event.items():
        key_lower = key.lower()
        if isinstance(value, str) and any(token in key_lower for token in ["description", "descr", "notes"]):
            parts.append(value)
    for related in event.get("related", []):
        if not isinstance(related, dict):
            continue
        related_text = " ".join(str(value) for value in related.values() if isinstance(value, str))
        related_key_text = " ".join(str(key).lower() for key in related.keys())
        if any(token in related_key_text or token in related_text.lower() for token in ["description", "descr", "notes"]):
            parts.append(related_text)
    return _normalize_email_text(" ".join(parts)).lower()


def _calendar_event_datetime(event: Dict[str, Any], preferred_keys: List[str], fallback_name: str) -> Union[datetime.datetime, None]:
    timezone_name = ""
    for key in event:
        key_lower = key.lower()
        if "tz" in key_lower and fallback_name in key_lower and event.get(key):
            timezone_name = str(event.get(key))
            break
    for key in preferred_keys:
        if key in event:
            parsed = _calendar_timestamp_to_datetime(event.get(key), timezone_name)
            if parsed:
                return parsed
    for key, value in event.items():
        if fallback_name in key.lower():
            parsed = _calendar_timestamp_to_datetime(value, timezone_name)
            if parsed:
                return parsed
    return None


def _calendar_event_start(event: Dict[str, Any]) -> Union[datetime.datetime, None]:
    return _calendar_event_datetime(event, [
        "event_start",
        "start_time",
        "start",
        "dtstart",
        "startDate",
    ], "start")


def _calendar_event_end(event: Dict[str, Any]) -> Union[datetime.datetime, None]:
    return _calendar_event_datetime(event, [
        "event_end",
        "end_time",
        "end",
        "dtend",
        "endDate",
    ], "end")


def check_thunderbird_calendar_event(result: Dict[str, Any], rules: Dict[str, Any]) -> float:
    """
    Score a Thunderbird calendar event.

    Rules:
      - days_from_today: integer offset for expected event date
      - hour: expected local start hour
      - minute: expected local start minute, default 0
      - duration_minutes: expected event duration
      - title: expected title phrase
      - body_points: list of acceptable phrase variants, like email scoring
    """
    if not result:
        return 0.

    try:
        today = datetime.date.fromisoformat(result["today"])
    except Exception:
        today = datetime.date.today()
    expected_date = today + datetime.timedelta(days=int(rules.get("days_from_today", 1)))
    expected_hour = int(rules.get("hour", 9))
    expected_minute = int(rules.get("minute", 0))
    expected_duration = rules.get("duration_minutes")
    expected_title = rules.get("title", "")
    body_points: List[List[str]] = rules.get("body_points", [])

    best_score = 0.
    for event in result.get("events", []):
        if not isinstance(event, dict):
            continue
        start = _calendar_event_start(event)
        if not start:
            continue
        if start.date() != expected_date or start.hour != expected_hour or start.minute != expected_minute:
            continue
        if expected_duration is not None:
            end = _calendar_event_end(event)
            if not end:
                continue
            duration_minutes = int((end - start).total_seconds() / 60)
            if duration_minutes != int(expected_duration):
                continue

        event_text = _calendar_event_text(event)
        if expected_title and _normalize_email_text(expected_title).lower() not in event_text:
            continue

        if not body_points:
            return 1.

        text = _calendar_event_description_text(event)
        matched = 0
        for variants in body_points:
            if any(_normalize_email_text(variant).lower() in text for variant in variants):
                matched += 1
        best_score = max(best_score, matched / len(body_points))

    return best_score
