import logging
import os
import re
import shutil
import subprocess
from itertools import product
from typing import Any, Dict, List, Union

import rapidfuzz.fuzz as fuzz
from bs4 import BeautifulSoup, Tag
import json

from desktop_env.evaluators.metrics.utils import are_lists_equal, compare_urls

logger = logging.getLogger("desktopenv.metrics.chrome")


def is_expected_active_tab(active_tab_info: Dict[str, str], rule: Dict[str, Any]) -> float:
    """
    Checks if the expected active tab is open in Chrome.
    """
    if not active_tab_info:
        return 0.

    match_type = rule['type']
    if match_type == "url":
        expected_url = rule['url']
        if isinstance(active_tab_info, Dict):
            actual_url = active_tab_info.get('url', None)
        else:
            actual_url = active_tab_info
        print("expected_url: {}".format(expected_url))
        print("actual_url: {}".format(actual_url))
        return 1 if compare_urls(expected_url, actual_url) else 0
    else:
        logger.error(f"Unknown type: {match_type}")
        return 0


# rules[expected] is a string-formatted regex
def is_expected_url_pattern_match(result, rules) -> float:
    """
    This function is used to search the expected pattern in the url using regex.
    result is the return value of function "activte_tab_info" or return value of function "get_active_url_from_accessTree"   
    """
    if not result:
        return 0.

    if type(result) == dict:
        result_url = result["url"]
        print("result url: {}".format(result_url))
    else:
        result_url = result
    # expect_regex = re.compile(rules["expected"])
    patterns = rules["expected"]
    print("expected_regex: {}".format(patterns))
    for pattern in patterns:
        match = re.search(pattern, result_url)
        print(match)
        if not match:
            return 0.
    return 1.


def is_expected_installed_extensions(installed_extensions, expected) -> float:
    print("installed_extensions: ")
    print(installed_extensions)
    expected_extensions = expected["expected"]
    match_type = expected.get("match", "exact")

    if match_type == "substring":
        installed_extensions = [extension.lower() for extension in installed_extensions]
        expected_extensions = [extension.lower() for extension in expected_extensions]
        return 1. if all(
            any(expected_extension in installed_extension for installed_extension in installed_extensions)
            for expected_extension in expected_extensions
        ) else 0.

    # whether the expected extensions are installed
    set_expected_extensions = set(expected_extensions)
    set_installed_extensions = set(installed_extensions)

    if set_expected_extensions.issubset(set_installed_extensions):
        return 1.
    else:
        return 0.


def is_expected_tabs(open_tabs: List[Dict[str, str]], rule: Dict[str, Any]) -> float:
    """
    Checks if the expected tabs are open in Chrome.
    """

    match_type = rule['type']

    if match_type == "url":
        expected_urls = rule['urls']
        actual_urls = [tab['url'] for tab in open_tabs]
        return 1 if are_lists_equal(expected_urls, actual_urls, compare_urls) else 0
    else:
        logger.error(f"Unknown type: {match_type}")
        return 0


def is_expected_bookmarks(bookmarks: List[str], rule: Dict[str, Any]) -> float:
    """
    Checks if the expected bookmarks are in Chrome.
    """
    if not bookmarks:
        return 0.
    elif rule['type'] == "bookmark_bar_folders_names":
        bookmark_bar_folders_names = [bookmark['name'] for bookmark in bookmarks['bookmark_bar']['children'] if
                                      bookmark['type'] == 'folder']
        if set(rule['names']).issubset(set(bookmark_bar_folders_names)):
            return 1.
        else:
            return 0.
        # return 1. if set(bookmark_bar_folders_names) == set(rule['names']) else 0.
    elif rule['type'] == "bookmark_bar_websites_urls":
        bookmark_bar_websites_urls = [bookmark['url'] for bookmark in bookmarks['bookmark_bar']['children'] if
                                      bookmark['type'] == 'url']
        print(bookmark_bar_websites_urls)
        
        if set(rule['urls']).issubset(set(bookmark_bar_websites_urls)):
            return 1.
        else:
            return 0.
        # return 1. if set(bookmark_bar_websites_urls) == set(rule['urls']) else 0.
    elif rule['type'] == "liked_authors_websites_urls":
        # Check if "liked authors" folder exists
        liked_authors_folder = next((bookmark for bookmark in bookmarks['bookmark_bar']['children'] if
                                     bookmark['type'] == 'folder' and bookmark['name'] == 'Liked Authors'), None)
        if liked_authors_folder:
            # Check if it contains the specified URLs
            liked_authors_urls = [bookmark['url'] for bookmark in liked_authors_folder['children'] if
                                  bookmark['type'] == 'url']

            urls = rule['urls']

            for idx, url in enumerate(urls):
                if isinstance(url, str):
                    urls[idx] = [url]

            combinations = product(*urls)

            for combination in combinations:
                if set(combination) == set(liked_authors_urls):
                    return 1.
            return 0.
        else:
            return 0.
    else:
        raise TypeError(f"{rule['type']} not support yet!")




def is_expected_search_query(active_tab_info: Dict[str, str], rules: Dict[str, Any]) -> float:
    expected = rules['expect']
    pattern = expected['pattern']
    matched = re.search(pattern, active_tab_info['url'])
    if matched:
        return 1.
    return 0.


def compare_pdfs(pdf1_path: Union[str, List[str]], pdf2_path: Union[str, List[str]]):
    """
    Compare two PDF files.
    """
    if type(pdf2_path) != list:
        pdf1_path, pdf2_path = [pdf1_path], [pdf2_path]

    def extract_text_from_pdf(pdf_path):
        """Extract text from each page of the PDF."""
        text = ""
        with fitz.open(pdf_path) as pdf:
            for page in pdf:
                text += page.get_text()
        return text.strip()

    score = 0.
    for path1, path2 in zip(pdf1_path, pdf2_path):
        try:
            text1 = extract_text_from_pdf(path1)
            text2 = extract_text_from_pdf(path2)
            score += fuzz.ratio(text1, text2) / 100
        except Exception as e:
            logger.info(f"[ERROR]: unexpected error occurred when comparing PDF files: {e}")
    return score / len(pdf2_path)


import fitz
from PIL import Image
import typing

# borb 3.x imports typing.TypeAlias even on Python 3.9. Keep mounted clients
# usable with the image's Python 3.9; image builds pin a compatible 2.x borb.
if not hasattr(typing, "TypeAlias"):
    typing.TypeAlias = typing.Any

from borb.pdf import Document
from borb.pdf import PDF

from pathlib import Path


def compare_pdf_images(pdf1_path: str, pdf2_path: str, **kwargs) -> float:
    if not pdf1_path or not pdf2_path:
        return 0.

    def extract_images_from_pdf(pdf_path):
        pdf_document = fitz.open(pdf_path)
        images = []

        for page_number in range(pdf_document.page_count):
            page = pdf_document[page_number]
            pixmap = page.get_pixmap()

            img = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)

            images.append(img)

        return images

    def fix_pdf(in_path: Path, out_path: Path) -> None:
        doc: typing.Optional[Document] = None
        with open(in_path, "rb") as fh:
            doc = PDF.loads(fh)
        with open(out_path, "wb") as fh:
            PDF.dumps(fh, doc)

    fix_pdf(Path(pdf1_path), Path(pdf1_path))
    fix_pdf(Path(pdf2_path), Path(pdf2_path))

    images1 = extract_images_from_pdf(pdf1_path)
    images2 = extract_images_from_pdf(pdf2_path)

    if len(images1) != len(images2):
        return 0.

    for img1, img2 in zip(images1, images2):
        if img1.tobytes() != img2.tobytes():
            return 0.

    return 1.


def compare_archive(pred_path: str, gold_path: str, **kwargs) -> float:
    """
    Compare two archives. Note that the files in the archives should be of the same type.
    """
    file_path = kwargs.pop('file_path', '')

    if not pred_path:
        return 0.
    pred_folder = os.path.splitext(pred_path)[0] + '_pred'
    gold_folder = os.path.splitext(gold_path)[0] + '_gold'

    if os.path.exists(pred_folder):  # remove existing folder for new predictions
        shutil.rmtree(pred_folder, ignore_errors=True)
    os.makedirs(pred_folder)
    shutil.unpack_archive(pred_path, pred_folder)

    if not os.path.exists(gold_folder):  # use cache if exists
        os.makedirs(gold_folder)
        shutil.unpack_archive(gold_path, gold_folder)

    pred_files = sorted(os.listdir(os.path.join(pred_folder, file_path)))
    gold_files = sorted(os.listdir(os.path.join(gold_folder, file_path)))

    if pred_files != gold_files:
        return 0.

    def get_compare_function():
        file_type = kwargs.pop('file_type', 'text')
        if file_type == 'text':
            from .vscode import compare_text_file
            return compare_text_file
        elif file_type == 'pdf':
            return compare_pdfs
        elif file_type == 'docx':
            from .docs import compare_docx_files
            return compare_docx_files
        elif file_type == 'ppt':
            from .slides import compare_pptx_files
            return compare_pptx_files
        elif file_type == 'image':
            from .vlc import compare_images
            return compare_images
        elif file_type == 'csv':
            from .table import compare_csv
            return compare_csv
        elif file_type == 'table':
            from .table import compare_table
            return compare_table
        elif file_type == 'audio':
            from .vlc import compare_audios
            return compare_audios
        elif file_type == 'video':
            from .vlc import compare_videos
            return compare_videos
        else:
            raise ValueError('[ERROR]: not support file type: %s' % file_type)

    score = 0
    compare_function = get_compare_function()
    for f1, f2 in zip(pred_files, gold_files):
        fp1 = os.path.join(pred_folder, file_path, f1)
        fp2 = os.path.join(gold_folder, file_path, f2)
        score += compare_function(fp1, fp2, **kwargs)
    return score / len(pred_files)


def compare_htmls(html_path1: str, html_path2: str) -> float:
    """
    Compare two HTML files.
    """
    with open(html_path1, 'r', encoding='utf-8') as inf:
        soup1 = BeautifulSoup(inf, 'lxml')
    with open(html_path2, 'r', encoding='utf-8') as inf:
        soup2 = BeautifulSoup(inf, 'lxml')

    def compare_elements(elem1, elem2):
        if not (isinstance(elem1, Tag) and isinstance(elem2, Tag)):
            return elem1 == elem2
        if elem1.name != elem2.name:
            return False
        if elem1.text.strip() != elem2.text.strip():
            return False
        if elem1.attrs != elem2.attrs:
            return False
        return True

    for elem1, elem2 in zip(soup1.recursiveChildGenerator(), soup2.recursiveChildGenerator()):
        if not compare_elements(elem1, elem2):
            return .0
    return 1.


def is_cookie_deleted(cookie_data, rule):
    """
    Check if the cookie is deleted.
    """

    if rule['type'] == 'domains':
        cookies_domains = [cookie[1] for cookie in cookie_data]
        for domain in rule['domains']:
            for cookies_domain in cookies_domains:
                if compare_urls(domain, cookies_domain):
                    return 0.
        return 1.
    else:
        raise TypeError(f"{rule['type']} not support yet!")


def is_shortcut_on_desktop(shortcuts: Dict[str, str], rule):
    """
    Check if the shortcut is on the desktop.
    """
    # fixme: if the name of the website changed in the future, this will not work; can be replaced with url
    if rule['type'] == 'name':
        for shortcut_path, shortcut_content in shortcuts.items():
            if "Name=" + rule['name'] + "\n" in shortcut_content:
                return 1.
        return 0.
    elif rule['type'] == 'description':
        for shortcut_path, shortcut_content in shortcuts.items():
            try:
                shortcut_description = json.loads(shortcut_content)['data']['description']
                if rule['description'] in shortcut_description:
                    return 1.
            except:
                pass
        return 0.
    elif rule['type'] == 'url':
        raise TypeError(f"{rule['type']} not support yet!")
    elif rule['type'] == 'id':
        raise TypeError(f"{rule['type']} not support yet!")
    else:
        raise TypeError(f"{rule['type']} not support yet!")


def check_history_deleted(history_data, rule):
    """
    Check if the history is deleted.
    """

    if rule['type'] == 'keywords':
        history_domains = [history[0] for history in history_data]
        for keyword in rule['keywords']:
            for history_domain in history_domains:
                if keyword in history_domain:
                    return 0.
        return 1.
    else:
        raise TypeError(f"{rule['type']} not support yet!")


def check_history_contains(history_data, rule):
    """
    Check whether browser history contains each expected URL pattern.
    """
    if not history_data:
        return 0.

    if rule['type'] != 'url_patterns':
        raise TypeError(f"{rule['type']} not support yet!")

    history_urls = [history[0] for history in history_data if history and history[0]]
    for pattern in rule['patterns']:
        if not any(re.search(pattern, url) for url in history_urls):
            return 0.
    return 1.


def check_enabled_experiments(enabled_experiments, rule):
    """
    Check if the enabled experiments are as expected.
    """
    enabled_experiments_names = [experiment.split("@")[0] for experiment in enabled_experiments]

    if rule['type'] == 'names':
        return 1. if enabled_experiments_names == rule['names'] else 0.
    else:
        raise TypeError(f"{rule['type']} not support yet!")


def check_font_size(font_size, rule):
    """
    Check if the font size is as expected.
    """

    default_font_size = font_size['default_font_size']
    if rule['type'] == 'value':
        return 1. if default_font_size == rule['value'] else 0.
    elif rule['type'] == 'range':
        return 1. if rule['min'] < default_font_size < rule['max'] else 0.
    else:
        raise TypeError(f"{rule['type']} not support yet!")


def is_added_to_steam_cart(active_tab_info, rule):
    """
    Check if the item is added to the Steam cart.
    """
    return is_page_contains_items(active_tab_info, rule)


def is_page_contains_items(active_tab_info, rule):
    """
    Score expected cart items against a page's HTML content.

    The rule's items list is treated as the expected product list. For a single
    expected item, the cart must contain exactly one product and it must match.
    For multiple expected items, score matched expected items divided by the
    larger of expected item count and cart item count.

    The rule may alternatively include item_groups, where each inner list is a
    set of acceptable substitutes for one expected cart item.
    """
    items = rule.get('items', [])
    item_groups = rule.get('item_groups', [])
    content = active_tab_info['content']

    if not items and not item_groups:
        return 0.

    db_score = _score_shopping_cart_db(rule)
    if db_score is not None:
        return db_score

    matched = sum(1 for item in items if item in content)
    matched += sum(
        1 for group in item_groups
        if any(str(item) in content for item in group)
    )
    cart_item_count = content.count('data-cart-item-id=')
    if cart_item_count == 0:
        cart_item_count = content.count('class="item-info"')

    expected_count = len(items) + len(item_groups)

    if expected_count == 1:
        return 1. if matched == 1 and cart_item_count == 1 else 0.

    denominator = max(expected_count, cart_item_count)
    if denominator == 0:
        return 0.

    return matched / denominator


def _score_shopping_cart_db(rule):
    host = rule.get("db_host", "host.docker.internal")
    port = str(rule.get("db_port", 13306))
    database = rule.get("db_name", "magentodb")
    user = rule.get("db_user", "magentouser")
    password = rule.get("db_password", "MyPassword")
    items = rule.get("items", [])
    item_groups = rule.get("item_groups", [])
    sql = (
        "SELECT qi.item_id, qi.product_id, qi.sku, qi.name "
        "FROM quote q JOIN quote_item qi ON qi.quote_id=q.entity_id "
        "WHERE q.items_count > 0 AND q.is_active=1 "
        "ORDER BY q.updated_at DESC, qi.item_id;"
    )
    command = [
        "mysql",
        "--skip-ssl",
        "-h",
        host,
        "-P",
        port,
        "-u",
        user,
        f"-p{password}",
        database,
        "-N",
        "-B",
        "-e",
        sql,
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        logger.warning("Could not inspect shopping cart database: %s", e)
        return None

    cart_items = []
    cart_item_ids = []
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) >= 4:
            cart_item_ids.append(fields[0])
            cart_items.append(" ".join(fields[1:]).lower())

    if not cart_items:
        return 0.

    matched = sum(1 for item in items if any(str(item).lower() in cart_item for cart_item in cart_items))
    matched += sum(
        1 for group in item_groups
        if any(
            str(item).lower() in cart_item
            for item in group
            for cart_item in cart_items
        )
    )
    cart_item_count = len(cart_items)
    if matched and not _shopping_cart_options_match(rule, cart_item_ids):
        return 0.

    expected_count = len(items) + len(item_groups)

    if expected_count == 1:
        return 1. if matched == 1 and cart_item_count == 1 else 0.

    denominator = max(expected_count, cart_item_count)
    return matched / denominator if denominator else 0.


def _shopping_cart_options_match(rule, cart_item_ids):
    expected_options = rule.get("options", {})
    if not expected_options:
        return True

    host = rule.get("db_host", "host.docker.internal")
    port = str(rule.get("db_port", 13306))
    database = rule.get("db_name", "magentodb")
    user = rule.get("db_user", "magentouser")
    password = rule.get("db_password", "MyPassword")
    item_ids = ",".join(cart_item_ids)
    if not item_ids:
        return False

    sql = (
        "SELECT qi.sku, ot.title, ovt.title "
        "FROM quote_item qi "
        "JOIN quote_item_option qio ON qio.item_id=qi.item_id AND qio.code LIKE 'option_%' "
        "JOIN catalog_product_option o ON CONCAT('option_', o.option_id)=qio.code "
        "JOIN catalog_product_option_title ot ON ot.option_id=o.option_id "
        "JOIN catalog_product_option_type_title ovt ON ovt.option_type_id=CAST(qio.value AS UNSIGNED) "
        f"WHERE qi.item_id IN ({item_ids});"
    )
    command = [
        "mysql",
        "--skip-ssl",
        "-h",
        host,
        "-P",
        port,
        "-u",
        user,
        f"-p{password}",
        database,
        "-N",
        "-B",
        "-e",
        sql,
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        logger.warning("Could not inspect shopping cart item options: %s", e)
        return False

    actual_options = {}
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) >= 3:
            sku, option_name, option_value = fields[:3]
            actual_options.setdefault(sku.lower(), {})[option_name.lower()] = option_value.lower()

    for item, options in expected_options.items():
        item_key = str(item).lower()
        item_options = actual_options.get(item_key)
        if item_options is None:
            return False
        for option_name, expected_value in options.items():
            if item_options.get(str(option_name).lower()) != str(expected_value).lower():
                return False

    return True


def check_chrome_weather_bookmark(env, config):

    bookmark_paths = [
        r"C:\Users\Docker\AppData\Local\Google\Chrome\User Data\Default\Bookmarks",
        r"C:\Users\Docker\AppData\Local\Google\Chrome\User Data\Profile 1\Bookmarks"
    ]

    for path in bookmark_paths:

        if not os.path.exists(path):
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                bookmarks = json.load(f)

            stack = [bookmarks]

            while stack:
                node = stack.pop()

                if isinstance(node, dict):

                    url = str(node.get("url", "")).lower()
                    name = str(node.get("name", "")).lower()

                    text = name + " " + url

                    if "sydney" in text and "weather" in text:
                        return 1.0

                    for value in node.values():
                        stack.append(value)

                elif isinstance(node, list):
                    stack.extend(node)

        except Exception:
            continue

    return 0.0


def check_digital_accessibility_page(active_tab_info, rule):
    if not active_tab_info:
        return 0.0

    if isinstance(active_tab_info, dict):
        url = active_tab_info.get("url", "")
    else:
        url = str(active_tab_info)

    print("Checking URL:", url)

    return 1.0 if "digital.gov.au/about/accessibility" in url else 0.0

def is_expected_bookmark_anywhere(bookmarks, rule):
    if not bookmarks:
        return 0.0

    expected_urls = set(rule["urls"])
    actual_urls = set()

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "url":
                actual_urls.add(node["url"])

            for value in node.values():
                walk(value)

        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(bookmarks)

    print("Expected bookmark URLs:", expected_urls)
    print("Actual bookmark URLs:", actual_urls)

    return 1.0 if expected_urls.issubset(actual_urls) else 0.0
    return 1.0 if expected_urls.issubset(actual_urls) else 0.0

def compare_text_content(result, rule):
    expected = rule.get("content", "").strip()
    actual = result.strip()

    print("Expected text:", expected)
    print("Actual text:", actual)

    return 1.0 if actual == expected else 0.0


def check_zoom_access_tree(result, rule):
    """
    Checks for Chrome zoom level text shown in browser UI/accessibility tree.
    """

    print("Checking accessibility tree for zoom")
    expected = rule.get("zoom", "").strip()
    actual = str(result)

    return 1.0 if expected in actual else 0.0

def exact_coupon_code(result, rules):
    expected = rules["expected"]
    return result == expected
