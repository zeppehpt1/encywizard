import pandas as pd
from pathlib import PosixPath
from paths import PROJECT_ROOT # for tests: from KinfProjektPy.KinfProjektPy.paths import PROJECT_ROOT

def save_pd_as_csv(dataframe, path_data_folder):
    csv_path = path_data_folder
    return dataframe.to_csv(csv_path, index=False)

def append_df(old_df, newly_added_df) -> pd.DataFrame:
    try:
        df_combined = pd.concat([old_df, newly_added_df], axis=1)
        return df_combined
    except: # invalid index error happens
        print("Index mismatch while appending dataframe!")
        return pd.concat([old_df.reset_index(), newly_added_df], axis=1)

def strip_trailing_space(dataframe, column_name) -> pd.DataFrame:
    dataframe[column_name] = dataframe[column_name].str.strip()
    return dataframe

def remove_rows_with_nan_values(dataframe) -> pd.DataFrame:
    dataframe = dataframe.dropna()
    return dataframe 

def open_textfile(path_to_textfile):
    return open(path_to_textfile, 'r', encoding='UTF-8') # r = no error due to / or \ slashes of different OS
    # some OS using ascii as default encoding  

def modify_textfile_characters(path_to_textfile: PosixPath) -> PosixPath: 
    """
        Creates modified register file at a new location
        Original file is kept in place
    """

    modified_textfile_path = PROJECT_ROOT / 'data' / 'revised-register-modified.txt'
    with open(path_to_textfile, 'r', encoding='UTF-8') as textfile:
        textfile_data = textfile.read()
    textfile_data = textfile_data.replace("S.", "|")
    textfile_data = textfile_data.replace(", s.", " |")
    textfile_data = textfile_data.replace("s.", "|")
    textfile_data = textfile_data.replace("oder", "|")
    textfile_data = textfile_data.replace("od.", "|")

    with open(modified_textfile_path, 'w', encoding='UTF-8') as textfile:
        textfile.write(textfile_data)
    return modified_textfile_path