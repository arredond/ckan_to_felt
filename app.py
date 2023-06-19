import streamlit as st
import pandas as pd

from st_aggrid import GridOptionsBuilder, AgGrid

from ckan_api import (
    create_open_in_felt_link,
    get_package,
    get_package_url,
    search_packages,
)

st.set_page_config(page_title="CKAN -> Felt", page_icon="📊")

st.title("CKAN API -> Felt")

st.subheader("1. Choose a CKAN API")
st.text('Input a CKAN API URL (ending in "/api/3/")')
st.text("Example: https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/")
# st.text('Input a CKAN API URL (ending in ""/api/3/") or choose from the dropdown')
ckan_base_url = st.text_input("CKAN Base URL")
# selected = st.selectbox("City Open Data Portals", KNOWN_CKAN_API_URLS, None)

st.subheader("2. Fine tune your search")
search = st.text_input("Search terms (optional)")
formats = st.text_input("Format (SHP, GeoJSON, etc)")

if ckan_base_url:
    search_df = search_packages(ckan_base_url, formats=formats, search=search)
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
                    <img src="https://file.notion.so/f/s/8c128438-9541-4062-b3c0-a80541f26578/Untitled.png?id=23a63381-04b8-4ae2-b32e-cccb9852d2fb&table=block&spaceId=4b86b6ac-47f4-4ed5-af9b-aee09bd38256&expirationTimestamp=1687260275047&signature=EaQwJwfoZne1UmHdPmvRjp9eV-2vkIyzNjwAWMo8OuE&downloadName=Untitled.png" />
                </a>""",
                unsafe_allow_html=True,
            )
    else:
        st.text("No results found")
