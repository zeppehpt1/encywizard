import folium
import pandas as pd
from tqdm import tqdm
from folium.plugins import MarkerCluster
from paths import PROJECT_ROOT
from coordinate_process import extract_country_geojson

def karte(df: pd.DataFrame, df2: pd.DataFrame):
    output_path = PROJECT_ROOT / 'noback_map.html'
    # clean up dataframe
    df = clean_up(df)
    # create map
    karte_voll = folium.Map(location=(40, 10), zoom_start=2, control_scale=True)
    # add places as markers to the marker cluster/layer with colors for groups
    full_layer(karte_voll, df, 'Orte', 'Stadt', 'orange')
    full_layer(karte_voll, df, 'Hauptstädte', 'Hauptstadt', 'red')
    full_layer(karte_voll, df, 'Handelsstädte', 'Handelsstadt' or 'Haupthandelsstadt', 'green')
    full_layer(karte_voll, df, 'Seestädte', 'Seestadt', 'lightblue')
    full_layer(karte_voll, df, 'Seehandelsstädte', 'Seehandelsstadt', 'darkblue')
    full_layer(karte_voll, df, 'Fabrikstädte', 'Fabrikstadt', 'darkred')
    full_layer(karte_voll, df, 'Freistädte', 'Freistadt', 'lightgreen')
    # add country polygons to country_layer
    add_country_polygons(df2, karte_voll)
    print("\nYou can find the map at: ", str(output_path))
    return karte_voll.save(output_path)


def clean_up(df):
    df.dropna(subset=['latitude'], inplace=True)
    df.drop_duplicates(subset=['longitude', 'latitude'], keep='last', inplace=True)
    df = df[df.placetype != 'historical regions']
    df = df[df.placetype != 'countries']
    df = df[df.placetype != 'states']
    df.reset_index(inplace=True, drop=True)
    return df


def add_marker_layers(karte, city_type, color):
    layer_text = '<span style="color: {col};">{txt}</span>'
    cluster = MarkerCluster(control=False)
    karte.add_child(cluster)
    marker_layer = folium.plugins.FeatureGroupSubGroup(cluster,
        name=layer_text.format(txt=city_type, col=color), show=True)
    karte.add_child(marker_layer)
    return marker_layer


def full_layer(karte, df, displayed_layer_name, city_type, color):
    layer = add_marker_layers(karte, displayed_layer_name, color)
    add_markers(df, layer, city_type, color)
    return layer


def add_markers(df: pd.DataFrame, marker_layer, city_type, color):
    for i in range(0,len(df)):
        if df.iloc[i]['city_type'] == city_type:
            html = f""""""
            if df.iloc[i]['modern_name'] is None or pd.isna(df.iloc[i]['modern_name']):
                html += f"""
                        <h3> {df.iloc[i]['city']}</h3>
                        """
            else:
                html += f"""
                        <h3> {df.iloc[i]['modern_name']}</h3>
                        """
            html += f"""
                    <br>Name im Jahre 1851: {df.iloc[i]['city']}</br>
                    """
            if not df.iloc[i]['historical_state'] or df.iloc[i]['historical_state'] == 'no_historical_state_found': #or pd.isna(df.iloc[i]['historical_state']):
                html += f"""
                        <br> Informationen zur damaligen Region/Zugehörigkeit leider nicht verfügbar! </br>
                        """
            else:
                html += f"""
                        <br>{df.iloc[i]['city']} war früher Teil {df.iloc[i]['historical_state']}. </br> 
                        """
            if df.iloc[i]['population'] == 0:
                html += f"""
                        <br> Informationen zur damaligen Population leider nicht verfügbar! </br>
                        """
            else:
                html += f"""
                        <br>Die damalige Population belief sich auf {int(df.iloc[i]['population'])}. </br>
                        """
            iframe = folium.IFrame(html=html, width=250, height=200)
            popup = folium.Popup(iframe, max_width=2650)
            if df.iloc[i]['population'] == 'nan' or '' or pd.isna(df.iloc[i]['population']):
                folium.CircleMarker(
                    location=(df.iloc[i]['latitude'], df.iloc[i]['longitude']),
                    popup=popup,
                    tooltip="Klick mich!",
                    color=color,
                    fill_color=color,
                    fill=True,
                    fill_opacity=0.50,
                ).add_to(marker_layer)
            else:
                population = int(df.iloc[i]['population'])
                folium.CircleMarker(
                    location=(df.iloc[i]['latitude'], df.iloc[i]['longitude']),
                    popup=popup,
                    tooltip="Klick mich!",
                    color=color,
                    fill_color=color,
                    radius=adjust_circle_markers(population)*0.0002,
                    fill=True,
                    fill_opacity=0.50,
                ).add_to(marker_layer)


def adjust_circle_markers(population):
    if population < 3000:
        x = population*16
        return x
    if population >= 3000 and population < 5000:
        x = population*8
        return x
    if population >= 5000 and population < 10000:
        x = population*4
        return x
    if population >= 10000 and population < 20000:
        x = population*3
        return x
    if population >= 20000 and population < 40000:
        x = population*1.5
        return x
    if population > 100000 and population < 250000:
        x = population/1.5
        return x
    if population >= 250000 and population < 500000:
        x = population/3
        return x
    if population >= 500000 and population < 1000000:
        x = population/5
        return x
    if population >= 1000000:
        x = population/10
        return x
    return population


def add_country_polygons(df, karte):
    country_layer = folium.FeatureGroup(name='Länder', show=False)
    karte.add_child(country_layer)
    folium.LayerControl().add_to(karte)
    with tqdm(total=df.shape[0]) as pbar:
        for i in range(0, len(df)):
            pbar.update(1)
            pbar.set_description("Adding polygon of %s to map" % df.iloc[i]['country'])
            polygon = extract_country_geojson(df.iloc[i]['country'])
            if polygon is None:
                pass
            else:
                folium.GeoJson(polygon).add_to(country_layer)
