import streamlit as st
import pandas as pd
import os

# --- Configuration (MUST be the first Streamlit command) ---
st.set_page_config(
    page_title="Voter List Search",
    # This setting maximizes the available screen width for the content area.
    layout="wide" 
)

# Define the list of all CSV files and their location
# ASSUMPTION: Files are in a subfolder named 'voter_lists'
CSV_FILES = [
    "voter_lists/1_Pappad.csv",
    "voter_lists/2_Manchampara_Marathakam.csv",
    "voter_lists/3_Manchampara_Manikyam.csv",
    "voter_lists/4_Communityhall_Rightside.csv",
    "voter_lists/5_Communityhall_Leftside.csv",
    "voter_lists/6_CPT.csv",
    "voter_lists/7_Depaul.csv",
]

# --- Data Loading and Cleaning ---

@st.cache_data
def load_and_clean_data():
    """Loads, combines, and cleans all voter data from CSV files."""
    all_data = []

    # Check for the data directory
    if not os.path.exists("voter_lists"):
        st.error("Error: The 'voter_lists' directory was not found.")
        return pd.DataFrame()

    # Load each file
    for file_path in CSV_FILES:
        try:
            # Use 'latin-1' encoding to handle special characters (like Malayalam) 
            df = pd.read_csv(file_path, encoding='latin-1') 
            all_data.append(df)
        except FileNotFoundError:
            st.warning(f"File not found: {file_path}. Skipping this list.")
        except Exception as e:
            st.error(f"Error loading {file_path}: {e}")

    if not all_data:
        st.error("No voter data could be loaded.")
        return pd.DataFrame()

    voter_data = pd.concat(all_data, ignore_index=True)

    # Clean the combined data
    voter_data.dropna(axis=1, how='all', inplace=True) 

    # Explicitly select the first 7 columns to ensure column count consistency
    if voter_data.shape[1] < 7:
        st.error(f"Data has too few columns ({voter_data.shape[1]}) after cleaning. Expected at least 7.")
        return pd.DataFrame()
        
    voter_data = voter_data.iloc[:, :7] 
    
    # Standardize and rename the expected 7 columns
    voter_data.columns = [
        'Serial No.', 
        'Name', 
        "Guardian's Name", 
        'OldWard No/ House No.', 
        'House Name', 
        'Gender / Age', 
        'New SEC ID No.'
    ]

    # Split the 'Gender / Age' column
    voter_data[['Gender', 'Age']] = voter_data['Gender / Age'].astype(str).str.split(' / ', expand=True)
    voter_data['Age'] = pd.to_numeric(voter_data['Age'], errors='coerce')
    voter_data.drop(columns=['Gender / Age'], inplace=True)
    
    final_columns = [
        'Serial No.', 'Name', 'Gender', 'Age', "Guardian's Name", 
        'House Name', 'OldWard No/ House No.', 'New SEC ID No.'
    ]
    
    present_columns = [col for col in final_columns if col in voter_data.columns]
    
    return voter_data[present_columns]

# --- Main Streamlit App Logic ---

st.title("Voter List Search Application 🔎")
st.markdown("Search for a voter by **Name** in the compiled list.")

df = load_and_clean_data()

if not df.empty:
    st.sidebar.success(f"✅ Total Voters Loaded: {len(df):,}")
    
    search_term = st.text_input("Enter Voter's Name to Search (case-insensitive):").strip()
    
    if search_term:
        # Filter for rows where 'Name' contains the search term
        filtered_df = df[
            df['Name'].astype(str).str.contains(search_term, case=False, na=False)
        ]
        
        st.subheader(f"Results for '{search_term}'")
        st.info(f"Found **{len(filtered_df)}** result(s).")
        
        if not filtered_df.empty:
            # Replaced use_container_width=True with width=1200
            st.dataframe(filtered_df.reset_index(drop=True), width=1200) 
        else:
            st.warning("No matching voters found. Try a broader search term.")
            
    else:
        st.subheader("Voter List Overview (Sample Data)")
        # Replaced use_container_width=True with width=1200
        st.dataframe(df.head(20), width=1200) 
        st.caption(f"Showing a sample of the first 20 records out of {len(df):,} total.")

else:
    st.error("The application failed to load data.")