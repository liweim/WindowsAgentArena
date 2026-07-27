import fnmatch
from typing import Dict, List

import lxml.cssselect
import lxml.etree
from lxml.etree import _Element as Element

from .general import check_text_points

_libconf_namespaces = [("oor", "http://openoffice.org/2001/registry")]
_libconf_ns_mapping = dict(_libconf_namespaces)
_setup_locale_selector = lxml.cssselect.CSSSelector('item[oor|path$=L10N]>prop[oor|name=ooSetupSystemLocale]>value',
                                                    namespaces=_libconf_ns_mapping)
_locale_selector = lxml.cssselect.CSSSelector('item[oor|path$=L10N]>prop[oor|name=ooLocale]>value',
                                              namespaces=_libconf_ns_mapping)


def check_libre_locale(config_file: str, rules: Dict[str, List[str]]) -> float:
    config: Element = lxml.etree.parse(config_file).getroot()
    setup_locale_setting: List[Element] = _setup_locale_selector(config)
    locale_setting: List[Element] = _locale_selector(config)

    setup_locale_setting: str = setup_locale_setting[0].text \
        if len(setup_locale_setting) > 0 \
        else locale_setting[0].text

    return float(any(fnmatch.fnmatchcase(setup_locale_setting, ptn) \
                     for ptn in rules["locale_set"]
                     )
                 )


import zipfile
import re


def check_docx_image_alt_text(result, rule):
    """
    Check DOCX image alternative text.

    DOCX stores image descriptions in:
    word/document.xml

    Example:
        <wp:docPr descr="A dog playing in a park"/>
    """

    keywords = rule.get("keywords", [])

    try:
        with zipfile.ZipFile(result, "r") as docx:

            document_xml = (
                docx
                .read("word/document.xml")
                .decode("utf-8")
            )

        # Extract image descriptions
        descriptions = re.findall(
            r'descr="([^"]*)"',
            document_xml
        )

        print("Found descriptions:", descriptions)

        if not descriptions:
            return 0.0

        alt_text = " ".join(descriptions).lower()
        return check_text_points(alt_text, rule)

    except Exception as e:
        print("Evaluator error:", e)
        return 0.0