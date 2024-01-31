import requests
import pandas as pd
import urllib.parse
from tqdm import tqdm
from geopy.geocoders import Nominatim


def gazetteer_lookup(dataframe):
    # containers that later become columns
    latitude = []
    longitude = []
    modern_name = []
    placetype = []

    with tqdm(total=dataframe.shape[0]) as pbar:
        for row in dataframe.itertuples():
            pbar.update(1)
            pbar.set_description("Processing lookup for %s" % row.city )
            city = row.city
            # gazetteer query, response as dictionary
            r_dict = gazetteer_query(city)
            # for every column try to extract information from the gazetteer response
            extract_response_data(r_dict, latitude, longitude, modern_name, placetype, city)
    # add each list to the dataframe
    dataframe['modern_name'] = pd.Series(modern_name)
    dataframe['placetype'] = pd.Series(placetype)
    dataframe['latitude'] = pd.Series(latitude)
    dataframe['longitude'] = pd.Series(longitude)
    return dataframe


def gazetteer_query(city):
    query_url = 'https://www.whgazetteer.org/api/index/?name={}'
    encoded_loc = urllib.parse.quote(city.encode("utf-8"))
    response = requests.get(query_url.format(encoded_loc))
    r_dict = response.json()
    return r_dict


def extract_response_data(r_dict, latitude, longitude, modern_name, placetype, noback_name):
    try:
        latitude.append(r_dict["features"][0]["geometry"]["coordinates"][1])
        longitude.append(r_dict["features"][0]["geometry"]["coordinates"][0])
    except:
        latitude.append(None)
        longitude.append(None)
    try:
        if noback_name == r_dict["features"][0]["properties"]["title"]:
            modern_name.append(None)
        else:
            modern_name.append(r_dict["features"][0]["properties"]["title"])
    except:
        modern_name.append(None)
    try:
        placetype.append(r_dict["features"][0]["properties"]["placetypes"][0])
    except:
        placetype.append(None)


def nominatim_lookup(dataframe):
    # get location object from Nominatim for every city entry
    geolocator = Nominatim(user_agent="noback-register")
    counter = -1
    raws = []
    with tqdm(total=dataframe.shape[0]) as pbar:
        for i in range(0, len(dataframe)):
            pbar.update(1)
            pbar.set_description("Adding alternative coordinates for %s" %  dataframe.iloc[i]['city'])
            raws.append(geolocator.geocode(dataframe.iloc[i]['city'], exactly_one=True, language="de", namedetails=True, addressdetails=True, timeout=1000000))

    country = []
    for i in raws:
        counter += 1
        # if Nominatim cannot find coordinates, but the gazetteer has found some,
        # reverse geocode to get the country with gazetteer coordinates
        if i is None and pd.notnull(dataframe.loc[counter, 'latitude']):
            lat = dataframe.loc[counter, 'latitude']
            lon = dataframe.loc[counter, 'longitude']
            temp = geolocator.reverse((lat, lon), exactly_one=True, language="de", addressdetails=True, timeout=1000000)
            country.append(temp.raw['address']['country'])
        # if geocode response is empty, add a None value
        elif i is None:
            country.append(None)
        else:
            try:
                # add coordinates from Nominatim response
                country.append(i.raw['address']['country'])
                dataframe.loc[counter, 'latitude'] = i.raw['lat']
                dataframe.loc[counter, 'longitude'] = i.raw['lon']
                # in case that there is no country that can be extracted due to a missing country key, add no_country_key
            except KeyError:
                country.append('no_country_key')
    # add country column to df1 and create a separate df2 which also receives the country column
    dataframe['country'] = pd.Series(country)
    dataframe2 = pd.DataFrame()
    dataframe2['country'] = pd.Series(country)
    # remove all entries for which the Nominatim response had no valid country key that could be accessed
    dataframe = dataframe[dataframe.country != 'no_country_key']
    dataframe.reset_index(inplace=True, drop=True)
    # clean up dataframe2
    dataframe2.drop_duplicates(keep='last', inplace=True)
    dataframe2.dropna(subset=['country'], inplace=True)
    dataframe2.reset_index(inplace=True, drop=True)
    return dataframe, dataframe2


def extract_country_geojson(country):
    geolocator = Nominatim(user_agent="noback-register")
    polygon = geolocator.geocode(country, geometry='geojson', timeout=1000000)
    if polygon.raw['geojson']['type'] == 'Point':
        return None
    else:
        return polygon.raw['geojson']


def remove_countries_from_df(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Removes a row if city == country in a dataframe
    """
    for city, country in zip(dataframe.city, dataframe.country):
        if city == country:
            new_dataframe = dataframe.drop(dataframe[(dataframe['city'] == dataframe['country'])].index) # false would return a copy
            new_dataframe.reset_index(drop=True, inplace=True)
    return new_dataframe