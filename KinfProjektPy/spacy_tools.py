from pathlib import PosixPath
from spacy.matcher import Matcher
from spacy.matcher import DependencyMatcher
from tqdm import tqdm
from utils import helper
import spacy
import pandas as pd

nlp = spacy.load("de_core_news_sm") # small model

def get_nlp_docs_from_csv(csv_path:PosixPath) -> list:

    dataframe = pd.read_csv(csv_path)
    dataframe['text'] = ['text'].astype(str)
    texts = dataframe['text']
    print("nlp processing of each text might take a while...")
    docs = list(nlp.pipe(texts)) # ensures that memory limit is not reached
    return docs

def get_nlp_docs_from_dataframe(dataframe_with_texts: pd.DataFrame) -> list:

    dataframe_with_texts['text'] = dataframe_with_texts['text'].astype(str) # ensures correct processing by spacy
    texts = dataframe_with_texts['text']
    print("nlp processing of each text might take a while...")
    docs = list(nlp.pipe(texts)) # ensures that memory limit is not reached
    return docs

def get_population_count(document): # for one document

    matcher = Matcher(nlp.vocab)
    pattern_a = [{"TEXT": {"REGEX": "(?:\d{4}|\d*'\d*)"}}, {"TEXT": "Einw"}]
    pattern_b = [{"TEXT": {"REGEX": "(?:\d{4}|\d*'\d*)"}}, {"TEXT": "Ein-"}]
    pattern_c = [{"TEXT": {"REGEX": "(?:\d{4}|\d*'\d*)"}}, {"TEXT": "Einwohnern"}]
    pattern_d = [{"TEXT": {"REGEX": "(?:\d{4}|\d*'\d*)"}}, {"TEXT": "Einwohner"}]
    pattern_e = [{"TEXT": {"REGEX": "(\d{1,2})"}}, {"ORTH": "Millionen"}, {"ORTH": "Einwohnern"} ] # e.g. Peking

    matcher.add("variant_a", [pattern_a])
    matcher.add("variant_b", [pattern_b])
    matcher.add("variant_c", [pattern_c])
    matcher.add("variant_d", [pattern_d])
    matcher.add("variant_e", [pattern_e])

    matches = matcher(document) 
    matches.sort(key = lambda x: x[1]) # sort matches (rather useless here)

    if not matches:
            return 0 # avoid weird nan values in later processing
    else:
        for match in matches[0:1]: # only use first match when a pattern was found
            result = document[match[1]:match[2]]
    return result

def get_all_population_counts(dataframe: pd.DataFrame, documents: list) -> pd.DataFrame:
    
    result_list = []
    for doc in (pbar := tqdm(documents)):
        pbar.set_description("Extraction of the population count from each text")
        result_list.append(str(get_population_count(doc)))

    population_df = pd.DataFrame({'population': result_list})
    population_df = clean_population_count_data(population_df) # remove strings from results
    population_df = handle_million_values(population_df) # normalize them for integer conversion
    population_df['population'] = population_df['population'].astype(str)
    population_df['population'] = population_df['population'].str.replace(r'\D', '0', regex=True) # deal with weird ocr occurrences in column
    population_df['population'] = population_df['population'].astype("Int64")
    dataframe = helper.append_df(dataframe, population_df) # append to the right
    return dataframe

def handle_million_values(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
        Transforms ambique million description into valid integer representation
    """

    for pop in dataframe['population']:
        if 'Millionen' in str(pop):
            number = (int(float(pop.split()[0]) * 10**6)) # split after number and add 6x zeros
            dataframe.loc[dataframe['population'] == pop] = int(number)
    return dataframe
    
def clean_population_count_data(dataframe: pd.DataFrame) -> pd.DataFrame:

    # remove unnecessary tokens from population data
    dataframe['population'] = dataframe['population'].replace(" Einw", '', regex=True)
    dataframe['population'] = dataframe['population'].replace(" Ein-", '', regex=True)
    dataframe['population'] = dataframe['population'].replace("'", '', regex=True)
    dataframe['population'] = dataframe['population'].replace("ohnern", '', regex=True)
    dataframe['population'] = dataframe['population'].replace("ohner", '', regex=True)
    return  dataframe

def get_city_type(document): # for one document

    matcher = Matcher(nlp.vocab)
    pattern_a = [{"LOWER": {"REGEX": "\w*stadt"}}] # upper- and lowercase

    matcher.add("variant_a", [pattern_a])

    matches = matcher(document)
    matches.sort(key = lambda x: x[1]) # sort matches (rather useless here)

    if not matches:
            return "Stadt" # avoid nan values
    else:
        for match in matches[0:1]: # only use first match if a pattern was 
            result = document[match[1]:match[2]]
    return result

def get_all_city_types(dataframe: pd.DataFrame, documents:list) -> pd.DataFrame:
    
    result_list = []
    for doc in (pbar := tqdm(documents)):
        pbar.set_description("Extracting city types from texts")
        result_list.append(str(get_city_type(doc)))
    city_type_df = pd.DataFrame({'city_type': result_list})

    # normalize strings of found city types
    city_type_df.replace("Ilauptstadt", "Hauptstadt", inplace=True)
    city_type_df.replace("Scestadt", "Seestadt", inplace=True)
    city_type_df.replace("Sechandelsstadt", "Seehandelsstadt", inplace=True)
    city_type_df.replace(r"^stadt$", "Stadt",regex=True, inplace=True)

    city_type_df.loc[city_type_df.groupby('city_type').city_type.transform('count').lt(3), 'city_type'] = 'Stadt' # replace  very few occurences of one city type with standard "Stadt" to avoid nan values
    dataframe = helper.append_df(dataframe, city_type_df) # append to the right
    return dataframe

def get_historical_state(city_text:str, city_type:str) -> list:
    
    matcher = DependencyMatcher(nlp.vocab)

    pattern = [
        {
            "RIGHT_ID": "anchor_founded",
            "RIGHT_ATTRS": {"ORTH": city_type}
        },
        {
            "LEFT_ID": "anchor_founded",
            "REL_OP": ">",
            "RIGHT_ID": "founded_ag",
            "RIGHT_ATTRS": {"DEP": "ag"},
        },
        {
            "LEFT_ID": "founded_ag",
            "REL_OP": ">",
            "RIGHT_ID": "founded_nk",
            "RIGHT_ATTRS": {"DEP": "nk"},
        },
        {
            "LEFT_ID": "founded_ag",
            "REL_OP": ".",
            "RIGHT_ID": "founded_nk2",
            "RIGHT_ATTRS": {"DEP": "nk"},
        }
    ]
    pattern_Region = [
        {
            "RIGHT_ID": "anchor_type",
            "RIGHT_ATTRS": {"ORTH": city_type}
        },
        {
            "LEFT_ID": "anchor_type",
            "REL_OP": ">",
            "RIGHT_ID": "type_mnr",
            "RIGHT_ATTRS": {"DEP": "mnr"},
        },
        {
            "LEFT_ID": "type_mnr",
            "REL_OP": ">",
            "RIGHT_ID": "type_mnr_nk",
            "RIGHT_ATTRS": {"DEP": "nk"},
        }]

    matcher.add("FOUNDED", [pattern])
    # matcher.add("REGION", [pattern_Region])
    doc = nlp(city_text)
    matches = matcher(doc)

    result_list = []
    if not matches:
        return "no_match"
    else:
        # Each token_id corresponds to one pattern dict
        match_id, token_ids = matches[0]
        for i in range(len(token_ids)):
            result_list.append(doc[token_ids[i]].text)
    return result_list

def get_all_historical_states(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Input and output is the main dataframe that is worked on

    """

    city_types = dataframe['city_type'].tolist()
    city_types_set = set(city_types) # get singular instances of entries ()
    city_types_cleaned = [x for x in city_types_set if str(x) != 'no_city_type_found'] # singular appearences of each city types without not found values
    dataframe['historical_state'] = ""

    with tqdm(total=dataframe.shape[0]) as pbar:
        for index, city_text in enumerate(dataframe['text']):
            pbar.update(1)
            pbar.set_description("Get historical state for %s" % dataframe.iloc[index]['city'])
            main_list = [] # initiate here, ensures getting "fresh" list after each iteration
            for city_type in city_types_cleaned: # check all city_type variants in each text
                result = get_historical_state(str(city_text), city_type)
                main_list.append(result)
            small_list = [x for x in main_list if str(x) != 'no_match'] # filter out no match occurrences, should find exactly one match
            if small_list: # if valid match is found
                flat_list = [x for xs in small_list for x in xs] # flatten the list, ensures that it always has only one list
                new_list = flat_list[1::1] # slice out the city_type from matches
                new_list[0], new_list[1] = new_list[1], new_list[0] # order the founded dependencies back in right order
                string_list = " ".join(str(x) for x in new_list) # convert list into string
                dataframe.at[index,'historical_state'] = string_list # insert found match at the correct cell
            else: dataframe.loc[dataframe['text'] == city_text, 'historical_state'] = "no_historical_state_found"
    return dataframe