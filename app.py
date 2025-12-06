import streamlit as st
import pandas as pd
import os

# --- Configuration (MUST be the first Streamlit command) ---
st.set_page_config(
    page_title="Voter List Search",
    # This setting maximizes the available screen width for the content area.
    layout="wide" 
)

# --- Define the list of all CSV files and their location mapped to Polling Station Name ---
# This mapping provides the Polling Station name to be added to each voter's record.
CSV_MAPPING = {
    "voter_lists/1_Pappad.csv": "1 - Pappad Anganvadi",
    "voter_lists/2_Manchampara_Marathakam.csv": "2 - Manchampara LPS Marathakam",
    "voter_lists/3_Manchampara_Manikyam.csv": "3 - Manchampara LPS Manikyam",
    "voter_lists/4_Communityhall_Rightside.csv": "4 - Community Hall Rightside",
    "voter_lists/5_Communityhall_Leftside.csv": "5 - Community Hall Leftside",
    "voter_lists/6_CPT.csv": "6 - CPT",
    "voter_lists/7_Depaul.csv": "7 - Depaul",
}

# --- Data Loading and Cleaning ---

@st.cache_data
def load_and_clean_data():
    """Loads, combines, and cleans all voter data from CSV files, adding the polling station name."""
    all_data = []
    
    # Define the expected 7 core column names
    EXPECTED_COLUMNS = [
        'Serial No.', 'Name', "Guardian's Name", 'OldWard No/ House No.', 
        'House Name', 'Gender / Age', 'New SEC ID No.'
    ]

    # Check for the data directory
    if not os.path.exists("voter_lists"):
        st.error("Error: The 'voter_lists' directory was not found. Please ensure the folder exists and is pushed to GitHub.")
        return pd.DataFrame()

    # Iterate through the mapping
    for file_path, polling_station_name in CSV_MAPPING.items():
        try:
            # FIX: Use 'latin-1' encoding to handle special character errors (e.g., byte 0xa0)
            df = pd.read_csv(file_path, encoding='latin-1') 
            
            # Drop all-NaN columns/rows from the raw data
            df.dropna(axis=1, how='all', inplace=True) 

            # FIX: Trim to the expected number of data columns (7) to handle column mismatch error
            if df.shape[1] < 7:
                st.warning(f"File {file_path} has too few columns ({df.shape[1]}). Skipping.")
                continue

            df = df.iloc[:, :7] 
            
            # Rename columns to standard names
            df.columns = EXPECTED_COLUMNS
            
            # ADD POLLING STATION COLUMN
            df['Polling Station'] = polling_station_name
            
            all_data.append(df)
        except FileNotFoundError:
            st.warning(f"File not found: {file_path}. Skipping this list.")
        except Exception as e:
            st.error(f"Error loading {file_path}: {e}")

    if not all_data:
        st.error("No voter data could be loaded.")
        return pd.DataFrame()

    # Combine all individual dataframes
    voter_data = pd.concat(all_data, ignore_index=True)

    # Split the 'Gender / Age' column
    voter_data[['Gender', 'Age']] = voter_data['Gender / Age'].astype(str).str.split(' / ', expand=True)
    voter_data['Age'] = pd.to_numeric(voter_data['Age'], errors='coerce')
    voter_data.drop(columns=['Gender / Age'], inplace=True)
    
    # Define the final desired column order, with Polling Station first
    final_columns = [
        'Polling Station', 
        'Serial No.', 
        'Name', 
        'Gender', 
        'Age', 
        "Guardian's Name", 
        'House Name', 
        'OldWard No/ House No.', 
        'New SEC ID No.'
    ]
    
    present_columns = [col for col in final_columns if col in voter_data.columns]
    
    return voter_data[present_columns]

# --- Main Streamlit App Logic ---

st.title("Voter List Search Application 🔎")
st.markdown("Search for a voter by **Name** in the compiled list.")

df = load_and_clean_data()

if not df.empty:
    st.sidebar.success(f"✅ Total Voters Loaded: {len(df):,}")
    
    # Create a selectbox in the sidebar for filtering by Polling Station (optional but useful)
    all_stations = sorted(df['Polling Station'].unique())
    selected_station = st.sidebar.selectbox("Filter by Polling Station", ["All Polling Stations"] + all_stations)
    
    if selected_station != "All Polling Stations":
        df = df[df['Polling Station'] == selected_station]
        st.sidebar.info(f"Showing **{len(df):,}** voters in {selected_station}.")
    
    search_term = st.text_input("Enter Voter's Name to Search (case-insensitive):").strip()
    
    if search_term:
        # Filter for rows where 'Name' contains the search term
        filtered_df = df[
            df['Name'].astype(str).str.contains(search_term, case=False, na=False)
        ]
        
        st.subheader(f"Results for '{search_term}'")
        st.info(f"Found **{len(filtered_df)}** result(s).")
        
        if not filtered_df.empty:
            # Displays the DataFrame using the requested fixed width
            st.dataframe(filtered_df.reset_index(drop=True), width=1200) 
        else:
            st.warning("No matching voters found. Try a broader search term.")
            
    else:
        st.subheader("Voter List Overview (Sample Data)")
        # Displays the DataFrame using the requested fixed width
        st.dataframe(df.head(20), width=1200) 
        st.caption(f"Showing a sample of the first 20 records out of {len(df):,} total.")

else:
    st.error("The application failed to load data.")