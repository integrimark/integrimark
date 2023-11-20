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
    base_url_pattern = r"var\s+integrimarkBaseURL\s*=\s*'([^']+?)';"
    base_url_match = re.search(base_url_pattern, content)
    if not base_url_match:
        raise ValueError("integrimarkBaseURL not found in the content.")
    base_url = base_url_match.group(1)

    return routes_dict, base_url


# Example usage:
content = """
var integrimarkRoutes = {
  "EXAM1-SOLUTIONS": "_266f48d5d164ef7b50095f37e9a0238e.enc.pdf",
  "HW2-SOLUTIONS": "_584b8e2a64c6999c46b6ebf40fd2db6a.enc.pdf",
  // This is a comment
  "HW3-SOLUTIONS": "_9b8638292a13aac15f090cdffdcf49db.enc.pdf",
  "HW4-SOLUTIONS": "_fc0a90e636a4b5ccdd046f6b826b4258.enc.pdf",
  "HW5-SOLUTIONS": "_a6024a44d566030763e4f5469e82ab77.enc.pdf",
  "HW6-SOLUTIONS": "_b412342376a0f309b383d76df11b1674.enc.pdf"
};

/* Another comment */
var integrimarkBaseURL = 'https://jlumbroso.github.io/integrimark-prototype/';
"""

routes, base_url = extract_data_from_routing_js(content)
print(routes)
print(base_url)
