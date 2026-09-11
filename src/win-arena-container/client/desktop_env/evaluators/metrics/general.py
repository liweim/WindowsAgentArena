import csv
import datetime
import difflib
import functools
import json
import logging
import operator
import os
import re
import sqlite3
import zipfile
from numbers import Number
from typing import Callable, Any, Union
from typing import Dict, List, Pattern

import lxml.etree
import openpyxl
import pdfplumber
import yaml
from docx import Document
from lxml.cssselect import CSSSelector
from lxml.etree import _Element
from rapidfuzz import fuzz

from desktop_env.evaluators.metrics.utils import _match_record, _match_value_to_rule

logger = logging.getLogger("desktopenv.metric.general")


def check_include_exclude(result: str, rules: Dict[str, List[str]]) -> float:
    if result is None:
        return 0.

    print(result, rules)
    include = rules.get("include", [])
    exclude = rules.get("exclude", [])
    if all(r in result for r in include) and all(r not in result for r in exclude):
        return 1.
    else:
        return 0.


def exact_match(result, rules) -> float:
    expect = rules["expected"]
    print(result, expect)

    if result == expect:
        return 1.
    else:
        return 0.


def literal_match(result: Any, expected: Any, **options) -> float:
    literal_type = options.get('type', 'str')
    if literal_type == 'str':
        ignore_case = options.get('ignore_case', False)
        score = str(result) == str(expected) if not ignore_case else str(result).lower() == str(expected).lower()
        return float(score)
    elif literal_type == 'list':
        if type(result) not in [list, tuple] or type(expected) not in [list, tuple] or len(result) != len(expected):
            return .0
        ignore_case = options.get('ignore_case', False)
        result = [str(s) for s in result] if not ignore_case else [str(s).lower() for s in result]
        expected = [str(s) for s in expected] if not ignore_case else [str(s).lower() for s in expected]
        return float(result == expected)
    else:
        raise NotImplementedError(f"Type {type} not supported")


def compare_xlsx_items(result: str, rules: Dict[str, Any]) -> float:
    if result is None or not os.path.exists(result):
        return 0.

    expected_items = rules.get("expected", [])
    if not expected_items:
        return 0.

    header_row = rules.get("header_row", 1)
    column_name = rules.get("column_name", "Item")

    def normalize_text(value: Any) -> str:
        return " ".join(str(value or "").lower().strip().split())

    def contains_match(expected: str, actual: str) -> bool:
        return normalize_text(expected) in normalize_text(actual)

    try:
        workbook = openpyxl.load_workbook(result, data_only=True)
    except Exception:
        return 0.

    worksheet_name = rules.get("sheet_name")
    if worksheet_name and worksheet_name in workbook.sheetnames:
        worksheet = workbook[worksheet_name]
    else:
        worksheet = workbook[workbook.sheetnames[0]]

    target_column = 1
    for cell in worksheet[header_row]:
        if normalize_text(cell.value) == normalize_text(column_name):
            target_column = cell.column
            break

    actual_items: List[str] = []
    seen_normalized: set[str] = set()
    for row in range(header_row + 1, worksheet.max_row + 1):
        value = worksheet.cell(row=row, column=target_column).value
        normalized = normalize_text(value)
        if not normalized or normalized in seen_normalized:
            continue
        seen_normalized.add(normalized)
        actual_items.append(normalized)

    if not actual_items:
        return 0.

    return sum(
        any(contains_match(expected_item, actual_item) for actual_item in actual_items)
        for expected_item in expected_items
    ) / len(expected_items)


def compare_emergency_kit_items_xlsx(result: str, rules: Dict[str, Any]) -> float:
    return compare_xlsx_items(result, rules)


def check_text_points(result: str, rules: Dict[str, Any]) -> float:
    """Score free-form text by atomic semantic facts.

    Point syntax is backward compatible:
      * ["A", "B"] or "A": any listed surface form may match.
      * {"any_of": ["A", "B"]}: explicit aliases / paraphrases.
      * {"all_of": [["A", "A-alt"], ["B"]]}: every component of one fact
        must be present; each component can itself have aliases.
      * {"regex": [r"..."]}: normalized-text regular-expression variants.
      * {"none_of": ["forbidden"]}: reject the point when a forbidden phrase
        is present.

    Rule flags:
      * ordered: points must occur in configured order.
      * line_based: each point must match a distinct non-empty line. Combined
        with ordered this is suitable for "one item per line, in this order".

    Text normalization intentionally handles presentation differences (Unicode
    compatibility, curly quotes, dash variants, case, repeated whitespace) but
    does not remove semantic tokens. Numeric-only aliases are matched with digit
    boundaries so e.g. `20` does not accidentally match `2026`.
    """
    if result is None:
        return 0.

    points = rules.get("points", [])
    if not points:
        return 0.

    ignore_case = rules.get("ignore_case", True)
    ordered = rules.get("ordered", False)
    line_based = rules.get("line_based", False)

    import unicodedata

    def normalize_text(value: Any) -> str:
        text = unicodedata.normalize("NFKC", str(value or ""))
        text = (text.replace("\u2018", "'").replace("\u2019", "'")
                    .replace("\u201c", '"').replace("\u201d", '"')
                    .replace("\u2013", "-").replace("\u2014", "-")
                    .replace("\u2212", "-"))
        text = " ".join(text.split())
        return text.casefold() if ignore_case else text

    def literal_span(actual: str, variant: Any):
        needle = normalize_text(variant)
        if not needle:
            return None
        if re.fullmatch(r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)", needle):
            m = re.search(rf"(?<![\d.]){re.escape(needle)}(?![\d.])", actual)
            return (m.start(), m.end()) if m else None
        pos = actual.find(needle)
        return (pos, pos + len(needle)) if pos >= 0 else None

    def regex_span(actual: str, patterns: Any):
        if isinstance(patterns, str):
            patterns = [patterns]
        best = None
        for pattern in patterns or []:
            try:
                m = re.search(pattern, actual)
            except re.error:
                continue
            if m and (best is None or m.start() < best[0]):
                best = (m.start(), m.end())
        return best

    def variants_span(actual: str, variants: Any):
        if isinstance(variants, str):
            variants = [variants]
        best = None
        for variant in variants or []:
            if isinstance(variant, dict):
                span = requirement_span(actual, variant)
            else:
                span = literal_span(actual, variant)
            if span is not None and (best is None or span[0] < best[0]):
                best = span
        return best

    def requirement_span(actual: str, requirement: Any):
        if isinstance(requirement, (str, list, tuple)):
            return variants_span(actual, requirement)
        if not isinstance(requirement, dict):
            return None

        spans = []
        if "any_of" in requirement:
            span = variants_span(actual, requirement["any_of"])
            if span is None:
                return None
            spans.append(span)
        if "regex" in requirement:
            span = regex_span(actual, requirement["regex"])
            if span is None:
                return None
            spans.append(span)
        for component in requirement.get("all_of", []):
            span = requirement_span(actual, component)
            if span is None:
                return None
            spans.append(span)
        for forbidden in requirement.get("none_of", []):
            if requirement_span(actual, forbidden) is not None:
                return None
        if not spans:
            return None
        return min(x[0] for x in spans), max(x[1] for x in spans)

    if line_based:
        lines = [normalize_text(line) for line in str(result).splitlines() if normalize_text(line)]
        matched = 0
        next_line = 0
        used = set()
        for point in points:
            candidates = range(next_line, len(lines)) if ordered else range(len(lines))
            found = None
            for idx in candidates:
                if idx in used:
                    continue
                if requirement_span(lines[idx], point) is not None:
                    found = idx
                    break
            if found is not None:
                matched += 1
                used.add(found)
                if ordered:
                    next_line = found + 1
        return matched / len(points)

    actual = normalize_text(result)
    matched = 0
    previous_end = 0
    for point in points:
        span = requirement_span(actual, point)
        if span is not None and (not ordered or span[0] >= previous_end):
            matched += 1
            if ordered:
                previous_end = span[1]
    return matched / len(points)


def is_in_list(result, rules) -> float:
    expect = rules["expected"]
    if expect in result:
        return 1.
    else:
        return 0.


def diff_text_file(result: str, expect: str) -> float:
    if result is None:
        return 0.

    with open(result) as f:
        result_lines: List[str] = f.read().splitlines()
    with open(expect) as f:
        expected_lines: List[str] = f.read().splitlines()
    return difflib.SequenceMatcher(a=result_lines, b=expected_lines).ratio()


def fuzzy_match(result, rules) -> float:
    expect = rules["expected"]

    return fuzz.ratio(result, expect) / 100.


def fuzzy_place_math(result_file_path, rules) -> float:
    if result_file_path is None:
        return 0.
    expect = rules["expected"]  # a list of possible answers
    # read list.docx, and get all texts out, overlook blank lines, remove blanks before and after each line
    doc = Document(result_file_path)
    words_list = []
    for para in doc.paragraphs:
        words_list.extend(para.text.split())
    fuzzy_score_list = []
    for word in words_list:
        max_score = 0
        for ans in expect:
            score = fuzz.ratio(word, ans) / 100
            max_score = max(max_score, score)
        fuzzy_score_list.append(max_score)
    if len(fuzzy_score_list) != 3:
        return 0.
    return sum(fuzzy_score_list) / 3



def check_ods_cell_values(result: str, rules: Dict[str, Any]) -> float:
    """Check cell values (and optional formula presence) in an ODS spreadsheet."""
    if result is None or not os.path.exists(result):
        return 0.

    expected_cells = rules.get("cells", {})
    expected_formulas = rules.get("formulas", {})
    if not expected_cells and not expected_formulas:
        return 0.

    sheet_name = rules.get("sheet")
    tolerance = float(rules.get("tolerance", 1e-6))
    ns = {
        "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
        "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
        "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    }

    def col_to_index(address: str) -> int:
        match = re.fullmatch(r"([A-Za-z]+)([1-9][0-9]*)", address)
        if not match:
            raise ValueError(f"Invalid ODS cell address: {address}")
        value = 0
        for char in match.group(1).upper():
            value = value * 26 + ord(char) - ord("A") + 1
        return value

    targets = set(expected_cells) | set(expected_formulas)
    try:
        target_positions = {
            address: (int(re.search(r"[0-9]+$", address).group()), col_to_index(address))
            for address in targets
        }
    except Exception:
        return 0.

    max_row = max((row for row, _ in target_positions.values()), default=0)
    max_col = max((col for _, col in target_positions.values()), default=0)

    try:
        with zipfile.ZipFile(result) as archive:
            content_xml = archive.read("content.xml")
        root = lxml.etree.fromstring(content_xml)
    except Exception as exc:
        logger.warning("Failed to parse ODS %s: %s", result, exc)
        return 0.

    tables = root.xpath("//table:table", namespaces=ns)
    if sheet_name:
        tables = [
            table for table in tables
            if table.get(f"{{{ns['table']}}}name") == sheet_name
        ]
    if not tables:
        return 0.
    table = tables[0]

    actual = {}
    row_index = 1
    for row in table.xpath("./table:table-row", namespaces=ns):
        row_repeat = int(row.get(f"{{{ns['table']}}}number-rows-repeated", "1"))
        if row_index > max_row:
            break
        row_end = min(row_index + row_repeat - 1, max_row)
        relevant_rows = range(row_index, row_end + 1)

        col_index = 1
        cells = row.xpath("./table:table-cell | ./table:covered-table-cell", namespaces=ns)
        for cell in cells:
            col_repeat = int(cell.get(f"{{{ns['table']}}}number-columns-repeated", "1"))
            if col_index > max_col:
                break
            col_end = min(col_index + col_repeat - 1, max_col)
            relevant_cols = range(col_index, col_end + 1)

            value_type = cell.get(f"{{{ns['office']}}}value-type", "")
            office_value = cell.get(f"{{{ns['office']}}}value")
            date_value = cell.get(f"{{{ns['office']}}}date-value")
            formula = cell.get(f"{{{ns['table']}}}formula")
            display = " ".join(
                "".join(paragraph.itertext()).strip()
                for paragraph in cell.xpath(".//text:p", namespaces=ns)
                if "".join(paragraph.itertext()).strip()
            ).strip()

            if value_type in {"float", "currency", "percentage"} and office_value is not None:
                try:
                    value = float(office_value)
                except ValueError:
                    value = display
            elif value_type == "date":
                value = display or date_value or ""
            elif value_type == "boolean":
                value = cell.get(f"{{{ns['office']}}}boolean-value", display)
            else:
                value = display

            for r in relevant_rows:
                for c in relevant_cols:
                    for address, position in target_positions.items():
                        if position == (r, c):
                            actual[address] = {"value": value, "formula": formula}
            col_index += col_repeat
        row_index += row_repeat

    def values_match(actual_value: Any, expected_value: Any) -> bool:
        if isinstance(expected_value, Number) and not isinstance(expected_value, bool):
            try:
                return abs(float(actual_value) - float(expected_value)) <= tolerance
            except (TypeError, ValueError):
                return False
        return str(actual_value).strip() == str(expected_value).strip()

    for address, expected_value in expected_cells.items():
        if address not in actual or not values_match(actual[address]["value"], expected_value):
            return 0.

    for address, should_have_formula in expected_formulas.items():
        if address not in actual:
            return 0.
        has_formula = bool(actual[address].get("formula"))
        if has_formula != bool(should_have_formula):
            return 0.

    return 1.

def check_csv(result: str, rules: Dict[str, List[Dict[str, str]]]) -> float:
    """
    Args:
        result (str): path to csv file
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

    expect_metrics = [False] * len(rules.get("expect", []))
    unexpect_metric = True
    with open(result) as f:
        reader = csv.DictReader(f)

        for rcd in reader:
            for i, r in enumerate(rules.get("expect", [])):
                expect_metrics[i] = expect_metrics[i] or _match_record(r, rcd)
            unexpect_metric = unexpect_metric and not any(_match_record(r, rcd) for r in rules.get("unexpect", []))
    return float(all(expect_metrics) and unexpect_metric)


def check_list(result: str, rules: Dict[str, List[str]]) -> float:
    """
    Args:
        result (str): path to list file
        rules (Dict[str, List[str]]): dict like
          {
            "expect": list of str as regexes
            "unexpect": list of str as regexes
          }

    Returns:
        float
    """

    if result is None:
        return 0.

    expect_patterns: List[Pattern[str]] = [re.compile(ptt) for ptt in rules.get("expect", [])]
    unexpect_patterns: List[Pattern[str]] = [re.compile(ptt) for ptt in rules.get("unexpect", [])]

    expect_metrics = [False] * len(expect_patterns)
    unexpect_metric = True
    with open(result) as f:
        for l in f:
            for i, r in enumerate(expect_patterns):
                expect_metrics[i] = expect_metrics[i] or (r.search(l) is not None)
            unexpect_metric = unexpect_metric and all(r.search(l) is None for r in unexpect_patterns)
    return float(all(expect_metrics) and unexpect_metric)


_accessibility_ns_map = {"st": "uri:deskat:state.at-spi.gnome.org"
    , "attr": "uri:deskat:attributes.at-spi.gnome.org"
    , "cp": "uri:deskat:component.at-spi.gnome.org"
    , "doc": "uri:deskat:document.at-spi.gnome.org"
    , "docattr": "uri:deskat:attributes.document.at-spi.gnome.org"
    , "txt": "uri:deskat:text.at-spi.gnome.org"
    , "val": "uri:deskat:value.at-spi.gnome.org"
    , "act": "uri:deskat:action.at-spi.gnome.org"
                         }


def check_accessibility_tree(result: str, rules: List[Dict[str, Any]]) -> float:
    """
    Args:
        result (str): XML of GNOME Accessibility Tree
        rules (List[Dict[str, Any]]): list of dict like
          {
            "selectors": list of str as CSS selectors, will be connected by ", "
              to form a composite selector. Only one from `selectors` and
              `xpath` is needed. If both are present, `xpath` takes the
              priority.
            "xpath": str as xpath. Only one from `selectors` and `xpath` is
              needed. If both are present, `xpath` takes the priority.
            "text": str as the expected text content of the selected element.
            "exact": bool specifying whether exact match or fuzzy match should
              be performed. defaults to True.
          }

    Returns:
        float
    """

    at: _Element = lxml.etree.fromstring(result)
    total_match_score = 1.
    for r in rules:
        if "xpath" in r:
            elements: List[_Element] = at.xpath(r["xpath"], namespaces=_accessibility_ns_map)
        elif "selectors" in r:
            selector = CSSSelector(", ".join(r["selectors"]), namespaces=_accessibility_ns_map)
            elements: List[_Element] = selector(at)
        else:
            raise ValueError("At least one of xpath and selectors is required")

        if len(elements) == 0:
            logger.info("No elements: %s", r["xpath"] if "xpath" in r else r["selectors"])
            return 0.

        if "text" in r:
            match_func: Callable[[str], Number] = functools.partial(operator.eq if r["exact"] \
                                                                        else (lambda a, b: fuzz.ratio(a, b) / 100.)
                                                                    , r["text"]
                                                                    )
            match_score: Number = 0
            for elm in elements:
                match_score = max(match_score, match_func(elm.text or None))
        else:
            match_score = 1.
        total_match_score *= match_score

    return float(total_match_score)


# def check_existence(result: str, *args) -> float:
# return 1. - (result is None)

def run_sqlite3(result: str, rules: Dict[str, Any]) -> float:
    connection: sqlite3.Connection = sqlite3.connect(result)
    cursor: sqlite3.Cursor = connection.execute(rules["sql"])
    return float(cursor.fetchone()[0] or 0)


def check_json(result: str, rules: Dict[str, List[Dict[str, Union[List[str], str]]]], is_yaml: bool = False) -> float:
    """
    Args:
        result (str): path to json file
        rules (Dict[str, List[Dict[str, Union[List[str], str]]]]): dict like
          {
            "expect": [
                {
                    "key": list of str
                    "method": str
                    "ref": something
                }
            ],
            "unexpect": <the same as `expect`
          }
        is_yaml (bool): yaml rather than json

    Returns:
        float
    """

    if result is None:
        return 0.
    with open(result) as f:
        if is_yaml:
            result: Dict[str, Any] = yaml.load(f, Loader=yaml.Loader)
        else:
            result: Dict[str, Any] = json.load(f)

    expect_rules = rules.get("expect", {})
    unexpect_rules = rules.get("unexpect", {})

    metric = True
    for r in expect_rules:
        value = result
        for k in r["key"]:
            try:
                value = value[k]
            except KeyError:
                return 0.
        metric = metric and _match_value_to_rule(value, r)
    for r in unexpect_rules:
        value = result
        for k in r["key"]:
            try:
                value = value[k]
            except KeyError:
                value = None
                break
        metric = metric and not _match_value_to_rule(value, r)
    return float(metric)


def check_direct_json_object(result, rules) -> float:
    """
    One of the most commonly used function to evalute.
    Compare two json objects directly.
    """
    if isinstance(result, str):
        # remove blanks before and after result
        result = result.strip()
        # replace all ' with "
        result = result.replace("'", '"')
        # load json object
        result = json.loads(result)
    if result is None:
        return 0.
    try:
        expect_in_result = rules.get("expect_in_result", False)
        if not expect_in_result:
            expected_json = rules["expected"]
            for key in expected_json.keys():
                expected_value = expected_json.get(key)
                if expected_value != result.get(key):
                    return 0.
            return 1.0
        else:
            expected_json = rules["expected"]

            for key in expected_json.keys():
                if isinstance(expected_json.get(key), list):
                    flag = 0
                    expected_value_list = expected_json.get(key)
                    for each_expected_value in expected_value_list:
                        if isinstance(result.get(key), list) and each_expected_value in result.get(key):
                            flag = 1
                            break
                    if flag == 0:
                        return 0.
                elif isinstance(expected_json.get(key), str):
                    if expected_json.get(key) not in result.get(key):
                        return 0.
                else:
                    logger.debug("check_direct_json_object: expected value type not supported")
                    return 0.
            return 1.0
    except:
        logger.debug("check_direct_json_object: result is not a valid json object")
        return 0.


def compare_time_in_speedtest_results(speedtest_result_path, time_diff):
    if not speedtest_result_path:
        return 0

    # open the speedtest results file(csv)
    date_col = None
    try:
        with open(speedtest_result_path, 'r') as f:
            for i, line in enumerate(f):
                if i == 1:
                    date = line.split(',')[1]
                    break
            now_date_time = datetime.datetime.now().strftime('%H:%M')
            date_time = date[-5:]
            # compare the date time with the current date time, if time diff less than time_diff para, then return true
            if not abs((datetime.datetime.strptime(date_time, '%H:%M') - datetime.datetime.strptime(now_date_time,
                                                                                                    '%H:%M')).total_seconds()) / 60 < int(
                time_diff):
                return 0
        return 1
    except:
        logger.debug("compare_time_in_speedtest_results: file not found or not readable")
        return 0


def is_included_all_json_objects(gold_file_path, result_file_path):
    if not gold_file_path or not result_file_path:
        return 0

    print("gold_file_path: ")
    print(gold_file_path)
    print("result_file_path: ")
    print(result_file_path)
    # two json file, check if all the key-value pair in gold_file_path is included in result_file_path
    with open(gold_file_path, 'r') as f:
        gold_json = json.load(f)
    with open(result_file_path, 'r') as fr:
        result_json = json.load(fr)
    for key in gold_json.keys():
        if key not in result_json.keys() or gold_json[key] != result_json[key]:
            return 0
    return 1


def is_gold_text_included_in_pdf(pdf_file_path, gold_text_path):
    if not gold_text_path or not pdf_file_path:
        return 0

    print("gold_text_path: ")
    print(gold_text_path)
    print("pdf_file_path: ")
    print(pdf_file_path)
    # gold file is a json file, we need to check all the value in json are included in pdf file.
    with open(gold_text_path, 'r') as f:
        gold_json = json.load(f)
    with pdfplumber.open(pdf_file_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
    false_list = []
    for key in gold_json.keys():
        if gold_json[key] not in text:
            false_list.append(key)
    if len(false_list) > 0:
        print("false_list: ")
        print(false_list)
        return 0
    else:
        return 1


def file_contains(file_path, config):
    # file_path ends with .txt
    if not file_path:
        return 0.
    try:
        with open(file_path, 'r') as f:
            file_text = f.read()
        for text in config["expected"]:
            if text not in file_text:
                logger.debug(f"file_contains: {text} not found in {file_path}")
                return 0.
    except:
        logger.debug("file_contains: file not found or not readable")
        return 0.
    return 1.


def check_line_number(file_path, line_number):
    # check if file_path exists
    if file_path is None or not os.path.isfile(file_path):
        return 0.
    timeRegex = "([01]\d|2[0-3]):[0-5]\d:[0-5]\d"
    # check if the string that matches the timeRegex in this txt file equals to line_number["expected"]
    try:
        with open(file_path, 'r') as f:
            line_count = 0
            for line in f:
                if re.search(timeRegex, line):
                    line_count += 1
        # if line_count equals to line_number["expected"], return 1, else return 0
        return 1 if line_count == int(line_number["expected"]) else 0
    except:
        logger.debug("check_line_number: file not found or not readable")
        return 0.


def compare_terminal_and_txt(txt_file_path, terminal_output):
    if not txt_file_path or not terminal_output:
        return 0

    # read txt file content
    with open(txt_file_path, 'r') as f:
        txt_file_content = f.read()
    # compare terminal output with txt file content
    return 1 if terminal_output == txt_file_content else 0


def compare_python_pure_text(py_file_path, gold_file_path):
    if not py_file_path or not gold_file_path:
        return 0

    # first, change the suffix of gold_file from .txt to .py
    print("py_file_path: ")
    print(py_file_path)
    print("gold_file_path: ")
    print(gold_file_path)

    # gold_file_path = gold_file_path.replace('.txt', '.py')
    def remove_whitespace(text):
        return ''.join(text.split())

    with open(py_file_path, 'r') as file1:
        content1 = file1.read()
    with open(gold_file_path, 'r') as file2:
        content2 = file2.read()
    content1_no_whitespace = remove_whitespace(content1)
    content2_no_whitespace = remove_whitespace(content2)
    if content1_no_whitespace == content2_no_whitespace:
        return 1
    else:
        return 0

if __name__ == '__main__':
    print(check_direct_json_object([], rules={
                "relativeTime": {
                  "from": "5th next month"
                },
                "expected": {
                    "start": "SEA",
                    "end": "NYC",
                    "time": "{DoW}, {Month} {DayD}, {Year}",
                    "category": "Miles"
                }}))
