import re
import json


def extract_data_from_routing_js(content):
    # Remove comments
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)  # block comments
    content = re.sub(r"//.*?\n", "", content)  # single-line comments

    # Extract dictionary after integrimarkRoutes
    routes_pattern = r"var integrimarkRoutes = (.*?);"
    routes_match = re.search(routes_pattern, content, re.DOTALL)
    if not routes_match:
        raise ValueError("integrimarkRoutes not found in the content.")
    routes_dict_str = routes_match.group(1)
    routes_dict = json.loads(
        routes_dict_str.replace("'", '"')
    )  # Convert single quotes to double quotes for JSON parsing

    # Extract integrimarkBaseURL
    base_url_pattern = r"var\s+integrimarkBaseURL\s*=\s*('.*?'\|\".*?\");"
    base_url_match = re.search(base_url_pattern, content, re.DOTALL)
    if not base_url_match:
        raise ValueError("integrimarkBaseURL not found in the content: " + content)
    base_url = base_url_match.group(1)

    return routes_dict, base_url
