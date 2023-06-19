from urllib.parse import urljoin, urlencode

import requests
import pandas as pd


KNOWN_CKAN_API_URLS = {
    "City Of Toronto": "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/",
    "Switzerland Open Data": "https://opendata.swiss/api/3/",
}


def search_packages(ckan_api_base, rows=50, start=0, formats=None, search=None):
    """Search packages from a CKAN API"""
    selected_cols = ["title", "author", "id", "formats", "excerpt"]
    params = {
        "rows": rows,
        "start": start,
    }
    if formats:
        params["formats[]"] = formats
    if search:
        params["search"] = search
    search_url = urljoin(ckan_api_base, "action/search_packages")
    r = requests.get(search_url, params)
    if not r.ok:
        raise ValueError()
    r_json = r.json()
    if not r_json["success"]:
        raise ValueError()
    search_df = pd.DataFrame(r_json["result"]["results"])
    if search_df.empty:
        return None
    return search_df[selected_cols]


def list_packages(ckan_api_base):
    """List all packages. Returns a list of package IDs"""
    search_url = urljoin(ckan_api_base, "action/search_packages")
    r = requests.get(search_url)
    r_json = r.json()
    if not r_json["success"]:
        raise ValueError()
    return r_json["result"]


def get_package(ckan_api_base, package_id):
    params = {"id": package_id}
    package_url = urljoin(ckan_api_base, "action/package_show")
    dataset_r = requests.get(package_url, params=params)
    return dataset_r.json()["result"]


def get_package_url(package, format_sort=["GPKG", "SHP", "GeoJSON", "CSV"]):
    """Fetch the best available resource URL for a package"""
    package_resources = package["resources"]
    format_urls = {res["format"]: res["url"] for res in package_resources}
    for preferred_format in format_sort:
        for res_format, res_url in format_urls.items():
            if preferred_format.lower() == res_format.lower():
                return res_url
    # None of the selected formats found, fallback to last URL
    return package_resources[-1]["url"]


def create_open_in_felt_link(layer_urls, title=None, **kwargs):
    """Create an Open In Felt link for some layer URLs"""
    params = {"layer_urls[]": layer_urls, **kwargs}
    if title:
        params["title"] = title
    return f"https://felt.com/map/new?{urlencode(params, True)}"
