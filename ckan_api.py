from urllib.parse import urljoin, urlencode

import requests
import pandas as pd


KNOWN_CKAN_API_URLS = {
    "None": None,
    "City Of Toronto": "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/",
    "Data.gov": "http://catalog.data.gov/api/3/",
    "Humanitarian Data Exchange": "https://data.humdata.org/api/3/",
    "Data.gov.uk": "https://data.gov.uk/api/",
    "Canada Open Data": "https://open.canada.ca/data/en/api/3/",
    "Australia Open Data": "https://data.gov.au/data/api/3/",
    "Switzerland Open Data": "https://opendata.swiss/api/3/",
}


def search_packages_generic(ckan_api_base, params):
    """Generic function to query the package_search endpoint

    Used both to search actual packages and facets (filters)
    """
    search_url = urljoin(ckan_api_base, "action/package_search")
    r = requests.get(search_url, params)
    if not r.ok or not r.json()["success"]:
        raise ValueError(f'Invalid request to "{search_url}" with params "{params}"')
    return r.json()


def list_facet(ckan_api_base, facet, limit=20):
    """List values for a specific facet (filter)"""
    params = {
        "facet.field": f'["{facet}"]',
        "facet.limit": f"{limit}",
        "rows": 0,
    }
    r_dict = search_packages_generic(ckan_api_base, params)
    facet_counts = r_dict["result"]["facets"][facet]
    return facet_counts
    # return pd.DataFrame.from_dict(facet_counts, orient='index', columns=['count'])


def list_res_formats(ckan_api_base):
    """List resource formats for a CKAN API"""
    return list_facet(ckan_api_base, "res_format")


def extract_formats(resources):
    """Extract comma-separated string of formats from CKAN resources list"""
    return ",".join({res["format"] for res in resources})


def search_packages(ckan_api_base, rows=50, start=0, search=None, res_format=None):
    """Search packages from a CKAN API and return a Pandas DataFrame"""
    selected_cols = ["title", "formats", "excerpt", "author", "notes", "id"]
    params = {
        "rows": rows,
        "start": start,
    }
    if search:
        params["q"] = search
    if res_format:
        params["fq"] = f"res_format:{res_format}"
    r_json = search_packages_generic(ckan_api_base, params)
    search_df = pd.DataFrame(r_json["result"]["results"])
    search_df["formats"] = search_df["resources"].map(extract_formats)
    ordered_cols = [c for c in selected_cols if c in search_df.columns] + [
        c for c in search_df.columns if c not in selected_cols
    ]
    # cols = [c for c in search_df.columns if c in selected_cols]
    if search_df.empty:
        return None
    return search_df[ordered_cols]
    # return search_df[cols]


def list_packages(ckan_api_base):
    """List all packages. Returns a list of package IDs"""
    search_url = urljoin(ckan_api_base, "action/package_list")
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
