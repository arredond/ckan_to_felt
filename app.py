import streamlit as st
import pandas as pd

from st_aggrid import GridOptionsBuilder, AgGrid

from ckan_api import (
    create_open_in_felt_link,
    get_package,
    get_package_url,
    list_res_formats,
    search_packages,
    KNOWN_CKAN_API_URLS,
)

st.set_page_config(page_title="CKAN -> Felt", page_icon="📊")

st.title("CKAN API -> Felt")

st.subheader("1. Choose a CKAN API")
st.markdown(
    """_Input a CKAN API URL (ending in "/api/3/") or choose from the dropdown_"""
)
ckan_base_url = st.text_input("CKAN Base URL")

api_urls = {v: k for k, v in KNOWN_CKAN_API_URLS.items()}
selected = st.selectbox(
    "Example Open Data Portals",
    api_urls.keys(),
    format_func=lambda x: api_urls[x],
    index=0,
)
if selected:
    ckan_base_url = selected

st.subheader("2. Fine tune your search")
search = st.text_input("Search terms (optional)") or None
max_results = st.slider("Max. results", min_value=10, max_value=1000, value=50, step=10)

if ckan_base_url:
    # List resource formats and offer selection
    res_formats = list_res_formats(ckan_base_url)
    formats_with_counts = {k: f"{k} ({v})" for k, v in res_formats.items()}
    format_options = [None] + list(formats_with_counts.keys())
    res_format = st.selectbox(
        "Filter by format",
        format_options,
        format_func=lambda x: formats_with_counts[x] if x else None,
        index=0,
    )
    # Search packages
    search_df = search_packages(
        ckan_base_url, rows=max_results, search=search, res_format=res_format
    )
    if search_df is not None:
        gb = GridOptionsBuilder.from_dataframe(search_df)
        gb.configure_pagination(paginationAutoPageSize=True)  # Add pagination
        gb.configure_selection(
            "multiple",
            use_checkbox=True,
            groupSelectsChildren="Group checkbox select children",  # Enable multi-row selection
        )
        gridOptions = gb.build()
        grid_response = AgGrid(
            search_df,
            gridOptions=gridOptions,
            data_return_mode="AS_INPUT",
            update_mode="MODEL_CHANGED",
            fit_columns_on_grid_load=False,
            width="100%",
        )
        data = grid_response["data"]
        selected = grid_response["selected_rows"]
        if selected:
            st.title("Selected Rows")
            selected_df = pd.DataFrame(selected)
            selected_df = selected_df.drop(columns=["_selectedRowNodeInfo"])
            AgGrid(selected_df)

            package_urls = []
            for _, row in selected_df.iterrows():
                package = get_package(ckan_base_url, row["id"])
                package_urls.append(get_package_url(package))

            title = st.text_input("(Optional) Map Title")
            if title == "":
                title = None
            link = create_open_in_felt_link(package_urls, title)
            st.markdown(
                f"""
                <a href="{link}">
                    <img src="https://feltmaps.notion.site/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F8c128438-9541-4062-b3c0-a80541f26578%2FUntitled.png?id=23a63381-04b8-4ae2-b32e-cccb9852d2fb&table=block&spaceId=4b86b6ac-47f4-4ed5-af9b-aee09bd38256&width=540&userId=&cache=v2" />
                </a>""",
                unsafe_allow_html=True,
            )
    else:
        st.text("No results found")
