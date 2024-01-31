# noback2map
This program generates a map based on some informations from the Noback book.

*Note*:
This program uses a slightly modified version of the Noback register from the book. But the use of the modified version is ensured in the program.

## Installation
These steps are for Linux. This will differ a bit for MacOS and windows.

### Via virtualvenv
````bash
git clone https://git.kinf.wiai.uni-bamberg.de/projekt22/teamD.git
cd teamD
python -m virtualvenv myenv
source myenv/bin/activate
pip install -r requirements.txt
````
### Via conda (not tested)
````bash
git clone https://git.kinf.wiai.uni-bamberg.de/projekt22/teamD.git
conda create --name myenv
conda activate myenv
conda install --file ...teamD/requirements.txt
````
## Usage
Just run the script **__main__.py** in the project folder with:
````bash
python __main__.py
````
Later you can open the map in the repo folder.

You can also display your own data (if they use the exact same column names) by exchanging the csv file in the **__main__.py** file.
### Example 1: Clickling marker on map
![example_map](examples/imgs/map_example.png)
### Example 2: Activated country polygons
![example_map](examples/imgs/map_example2.png)