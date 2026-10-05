import logging
from typing import Dict
import requests
import os
import subprocess

logger = logging.getLogger("desktopenv.getters.general")


def get_magento_product_match(env, config):
    """Return `1` when a Magento admin product matches all requested fields."""
    base_url = config.get("base_url", "http://host.docker.internal:7780")
    try:
        token_response = requests.post(
            f"{base_url}/rest/V1/integration/admin/token",
            json={
                "username": config.get("username", "admin"),
                "password": config.get("password", "admin1234"),
            },
            timeout=20,
        )
        token_response.raise_for_status()
        token = token_response.json()
        product_response = requests.get(
            f"{base_url}/rest/V1/products/{requests.utils.quote(config['sku'], safe='')}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )
        if product_response.status_code == 404:
            return "0"
        product_response.raise_for_status()
        product = product_response.json()
        stock = product.get("extension_attributes", {}).get("stock_item", {})
        requested_stock_fields = {"qty", "is_in_stock"}.intersection(config)
        if requested_stock_fields.difference(stock):
            stock_response = requests.get(
                f"{base_url}/rest/V1/stockItems/{requests.utils.quote(config['sku'], safe='')}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=20,
            )
            stock_response.raise_for_status()
            stock = stock_response.json()

        checks = {
            "sku": product.get("sku") == config["sku"],
            "name": product.get("name") == config.get("name", product.get("name")),
            "type_id": product.get("type_id") == config.get("type_id", product.get("type_id")),
            "status": int(product.get("status", 0)) == int(config.get("status", product.get("status", 0))),
            "price": abs(float(product.get("price", 0)) - float(config.get("price", product.get("price", 0)))) < 1e-6,
            "qty": abs(float(stock.get("qty", 0)) - float(config.get("qty", stock.get("qty", 0)))) < 1e-6,
            "is_in_stock": bool(stock.get("is_in_stock")) == bool(config.get("is_in_stock", stock.get("is_in_stock"))),
        }
        if not all(checks.values()):
            logger.warning(
                "Magento product mismatch for %s: failed=%s product=%s stock=%s",
                config.get("sku"),
                [field for field, matched in checks.items() if not matched],
                {field: product.get(field) for field in ("sku", "name", "type_id", "status", "price")},
                {field: stock.get(field) for field in ("qty", "is_in_stock")},
            )
        return "1" if all(checks.values()) else "0"
    except (requests.RequestException, TypeError, ValueError, KeyError) as e:
        logger.error("Failed to validate Magento product through REST: %s", e)
        return "0"


def get_magento_cms_page_match(env, config):
    """Return `1` when CMS page existence and optional fields match the rule."""
    base_url = config.get("base_url", "http://host.docker.internal:7780")
    try:
        token_response = requests.post(
            f"{base_url}/rest/V1/integration/admin/token",
            json={
                "username": config.get("username", "admin"),
                "password": config.get("password", "admin1234"),
            },
            timeout=20,
        )
        token_response.raise_for_status()
        response = requests.get(
            f"{base_url}/rest/V1/cmsPage/search",
            headers={"Authorization": f"Bearer {token_response.json()}"},
            params={
                "searchCriteria[filter_groups][0][filters][0][field]": "identifier",
                "searchCriteria[filter_groups][0][filters][0][value]": config["identifier"],
                "searchCriteria[filter_groups][0][filters][0][condition_type]": "eq",
            },
            timeout=20,
        )
        response.raise_for_status()
        items = response.json().get("items", [])
        expected_exists = config.get("exists", True)
        if not expected_exists:
            return "1" if not items else "0"
        for page in items:
            content = str(page.get("content", ""))
            ordered = config.get("content_contains_in_order", [])
            positions = [content.find(value) for value in ordered]
            ordered_match = all(position >= 0 for position in positions) and positions == sorted(positions)
            excludes_match = all(value not in content for value in config.get("content_excludes", []))
            if (all(page.get(field) == value for field, value in config.get("fields", {}).items())
                    and ordered_match and excludes_match):
                return "1"
        return "0"
    except (requests.RequestException, TypeError, ValueError, KeyError) as e:
        logger.error("Failed to validate Magento CMS page through REST: %s", e)
        return "0"


def get_mysql_query(env, config: Dict[str, str]):
    """Run a read-only query against the local Magento database for evaluation."""
    sql = config["sql"].strip()
    if not sql.lower().startswith(("select ", "show ", "describe ", "with ")):
        raise ValueError("mysql_query only accepts read-only SQL")
    command = [
        "mysql", "--skip-ssl",
        "-h", config.get("host", "host.docker.internal"),
        "-P", str(config.get("port", 13306)),
        "-u", config.get("user", "magentouser"),
        f"-p{config.get('password', 'MyPassword')}",
        config.get("database", "magentodb"),
        "-N", "-B", "-e", sql,
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        logger.error("Failed to query Magento database: %s", e)
        return None


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
