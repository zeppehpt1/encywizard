import sys
import pandas as pd

import coordinate_process as cp
import regex_filters as rf
import spacy_tools as st
import visualize_data as vd
import utils.helper as helper

from paths import PROJECT_ROOT
from pathlib import Path

def main():
    
    create_data= True
    save_file = Path(PROJECT_ROOT / 'data' / 'map_data.csv')
    if save_file.is_file():
        choise = None
        while choise not in (1,2,3):
            print("Dataset already created, press one of the following numbers to move on. \n")
            print("1: Only create map")
            print("2: Create new dataset + map ")
            print("3: Exit application ")
            choise = int(input("Your choice: "))
            print("\n")
            if choise == 1:
                create_data = False
            elif choise == 2:
                create_data = True
            elif choise == 3:
                print("Gently closing application...")
                return sys.exit(0)
            else:
                print("WARNING! You have made an invalid choice, please try again.")

    if create_data:
        text_path = PROJECT_ROOT / 'data' / 'revised-register-org.txt'
        noback_text_path = PROJECT_ROOT / 'data' / 'noback-complete.txt'

        # get all cities from register
        dataf = rf.extract_cities_from_register(text_path)

        # add pages
        dataf = rf.get_page_numbers_from_register(dataf, text_path)

        # get texts LISAS METHOD
        dataf = rf.get_first_paragraph_from_noback(dataf, noback_text_path)

        # add lat and lon column to dataframe
        dataf = cp.gazetteer_lookup(dataf)
        dataf, country_df = cp.nominatim_lookup(dataf)

        # remove countries from main dataframe
        dataf = cp.remove_countries_from_df(dataf)

        # add population numbers
        nlp_documents = st.get_nlp_docs_from_dataframe(dataf)
        dataf = st.get_all_population_counts(dataf, nlp_documents)

        # add city type
        dataf = st.get_all_city_types(dataf, nlp_documents)

        # add historical state
        dataf = st.get_all_historical_states(dataf)
        
        # save df as csv
        helper.save_pd_as_csv(dataf, save_file)

        # create map
        return vd.karte(dataf, country_df)
    
    else:
        # read existing csv and create map
        dataf = pd.read_csv(save_file)
        country_df = pd.DataFrame(dataf['country'])
        country_df.drop_duplicates(keep='last', inplace=True)
        country_df.dropna(subset=['country'], inplace=True)
        country_df.reset_index(inplace=True, drop=True)
        vd.karte(dataf, country_df)

if __name__ == '__main__':
    main()