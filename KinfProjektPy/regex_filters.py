from pathlib import PosixPath
import pandas as pd
import utils.helper as helper #für unittest: import KinfProjektPy.KinfProjektPy.utils.helper as helper
import numpy as np
from tqdm import tqdm
import re

def extract_cities_from_register(path_to_file:PosixPath) -> pd.DataFrame: 

    import re
    path_to_file = helper.modify_textfile_characters(path_to_file) # ensure better processing of original register file
    textfile = helper.open_textfile(path_to_file)
    
    places = [] # container for all cities/places/regions
    re = re.compile(r"^([a-zA-ZäöüÄÖÜâéá']{2,}(?: |[St.]|-|[a-zA-ZäöüÄÖÜâéá']+)*)")
    # match any string at the beginning of a line which can consists of two or more characters per word + can be combined with separtors zero or many times
    for line in (textfile):
        places += re.findall(line)
    textfile.close()
    # print("places count:", len(places)) # counts matches
    places = pd.DataFrame({'city': places})
    places = helper.strip_trailing_space(places, 'city')
    return places

def get_page_numbers_from_register(dataframe: pd.DataFrame, path_to_file:PosixPath) -> pd.DataFrame: # one page reference per line
    """
    Mainly needed for the get_text function of lisa
    """
    import re
    textfile = helper.open_textfile(path_to_file)
    pages = [] # container for all page occurences
    re = re.compile(r"^([^-][^0-9]+)([0-9]+)")
    # uses two capturing groups, match a single character not present in the brackets + to infinite times (greedy), second group matches the number
    for line in textfile:
        pages += re.findall(line)
    textfile.close()
    new_list = [aTuple[1:] for aTuple in pages] # extract desired tuple element
    result = [item for item, in new_list] # produce nice list of values
    # print("pages count:", len(result))
    result = pd.DataFrame({'page': result})
    dataframe = helper.append_df(dataframe, result) # append column to the right
    return dataframe

def get_first_paragraph_from_noback_light(dataframe_with_extracted_cities: pd.DataFrame, filepath_to_noback_text:PosixPath) -> pd.DataFrame: # includes removed NaN values
    '''
    City names should equal those from the register
    '''
    places = []
    df = dataframe_with_extracted_cities
    noback = helper.open_textfile(filepath_to_noback_text)
    lines = noback.read()
    #print(type(lines))
    
    city_no_text_found = []
    with tqdm(total=df.shape[0]) as pbar:
        for row in df['city']:
            pbar.update(1)
            pbar.set_description("Collect the first paragraph of each city")
            city = str(row)
            #print(city)
            places = [] # container for all cities/places/regions
                #city = "Aachen"
                # my_regex = city + r",$\n.+?(?=\.)"
            import re
            re = re.compile(r"^{}(?!, siehe|, \w+, siehe|, \w+ \w+, siehe|, siche|, siehc| oder \w+, siehe)(?:,| oder| od.).*?(?:stadt|Stadt|ort|Ort|Städte).*?(?<=Einw|Ein-)".format(city), flags=re.S | re.M | re.U | re.IGNORECASE)
                # match any string at the beginning of a line which can consists of two or more characters per word + can be combined with separtors zero or many times
                #for line in textfile:
            places += re.findall(lines)
            try:
                for index, t in enumerate(places):
                    # determine the right number?
                    if len(t) < 500: 
                        df.loc[df['city'] == city, 'text'] = places[index]
                        break # stop after first valid finding --> heuristic otherwise alwaays the latest foundings would be used, stop 
            except IndexError:
                city_no_text_found.append(city)
    
    df = helper.remove_rows_with_nan_values(df) # remove NaN
    df = df.replace("\n", ' ', regex=True) # remove newlines
    df.reset_index(drop=True, inplace=True) # ensure correct index values after removal
    return df
    

def cut_text_for_place_from_reference_place(place, ref_text):

    #if pd.isna(ref_text):
    #   cut_ref_text = ""
    if re.search(r"\s{}\s".format(place), ref_text, flags=re.I):
        if ref_text or place == "": # für unittest: <if ref_text == "" or place == "":>
            cut_ref_text = ""
        else:
            cut_ref_text = re.search(r"^.+?\s({}\s.*$)".format(place), ref_text, flags=re.I).groups()
    else:
        cut_ref_text = ""

    return cut_ref_text


def get_text_from_reference_place(dataframe):

    df = dataframe
    #print(df.columns)
    # iterate over rows in dataframe
    for row in df.itertuples():

        # get text from given row in df
        place = row[1]
        reference_place = ""
        text = row[3]
        ref_text = ""

    # function: liefere mir den Alternativtext aus, sonst liefere den alten Text
        searchstring = r"^.(?:\w+\s*).{0,9}\s(siehe|siebe|siehc|siche)\s"

        # ignore nan's
        if pd.isna(text):
            continue

        # if "siehe" is in first ten words of the text, take the place after "siehe"
        elif re.search(searchstring, text, flags=re.I):
            reference_place = re.search(r"^.+?\s([s][i][ce][bh][ce])\s+((st\. )?\w+)", text, flags=re.I).groups()
            # search for combination of "siehe" and give back the next word after whitespace(s) (St. in front of place is possible)
            # lazy search (?): takes first hit
            reference_place = reference_place[1]
            # take first tuple of reference_place as string
            #print("SIEHE: ", place, reference_place)

    # function: for loop to search text for given place: liefert false oder string oder gib Fehlermeldung aus
            for ref_row in df.itertuples():
                s_place = ref_row[1]
#                print(reference_place, s_place)

#                if s_place == "Zwoll":
#                    break

                if re.search("^{}".format(reference_place), s_place, flags=re.I):
                    #reference_place in s_row[1]:
                    ref_text = ref_row[3]
                    break

            if ref_text == "":
                print("Der Ort konnte im Referenztext nicht gefunden werden")
            else:
                #print(place, ref_text)
                ref_text = cut_text_for_place_from_reference_place(place, ref_text)

                #print("NEU: ", ref_text)
                row_index = row[0]
                df.iat[row_index, 2] = ref_text

        # df.to_csv(PROJECT_ROOT / 'data' / 'compare_after_reference.txt', index=False)

    return df


def get_first_paragraph_from_noback(dataframe_with_extracted_cities: pd.DataFrame, filepath_to_noback_text) -> pd.DataFrame:

    '''
    City names should equal those from the register
    '''
    print("... extract each text for each city")
    df = dataframe_with_extracted_cities

    df["text"] = ""
    # iterate over rows in dataframe
    
    for city, page in zip(df.city, df.page):
        # get place and page from given row in df
        
        place = city
        page = int(page)
        #print(place, page)

        if page > 890:
            page = page + 69
        else:
            page = page + 56  # 56, but give some room for errors (like Aarau)

        # call method to get the textpassage in noback fitting to place and page
        place_text = get_lines_from_text(place, page, filepath_to_noback_text)
        # fill found text into given row / text cell in csv
        #print(place_text)

        df.loc[df['city'] == place, 'text'] = place_text
        # df.to_csv(PROJECT_ROOT / 'data' / 'compare_after_first_iteration.csv', index=False)

    df = get_text_from_reference_place(df)
    # df.to_csv(PROJECT_ROOT / 'data' / 'compare_after_reference.csv', index=False)

    df = df.replace('', np.nan)
    df = helper.remove_rows_with_nan_values(df) # remove NaN
    df = df.replace("\n", ' ', regex=True) # remove newlines
    df.reset_index(drop=True, inplace=True) # ensure correct index values after removal
    return df


def get_lines_from_text(place, page, filepath_to_noback_text):
    text = ""
    place_container = r"^{}(\s*)?((.)*)?,((s.|[s][i][ce][bh][ce])(.)*)?"
    # finds text with place, optional whitespaces and symbols before comma, optional: "siehe" and symbols after the comma
    place_string = re.compile(place_container.format(place), flags=re.I | re.M | re.S)

    page_string_container = "----- {} / 1985 -----"
    page_string = page_string_container.format(page)
    next_page_int = page + 3  # scans 3 pages, 1 for 55 instead of 56, one for page break
    next_page_string = page_string_container.format(next_page_int)

    # search for city name on page xy by finding the span with the name in a single line with a comma at the end
    with open(filepath_to_noback_text, "r", encoding='UTF-8') as text_file:  # ISO-8859-1
        lines = text_file.readlines()

        # iterate whole noback.txt
        for i in range(len(lines)):
            stop = 0
            if stop == 1:
                break

            # if pagebreak is found
            elif page_string in lines[i]:

                # iterate from line, where pagebreak was found for next 100 lines
                for j in range(i, i + 100):
                    if stop == 1:
                        break
                    elif next_page_string in lines[i]: # To Do rausnehmen, wenn der Code durchläuft!!! mit Variablen oben
                        text = place_string, "Nothing found until page: ", next_page_string

                    # if heading for place is found
                    elif re.search(place_string, lines[j]):
                        # iterate from line, where place was found for next 10 lines
                        for k in range(j, j + 10):
                            if re.search("^.*?Rechnungs.+", lines[k]):
                                stop = 1
                                break
                            else:
                                text = text + lines[k]
    return text