import tarfile
import glob
import numpy as np
import datetime
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import ListedColormap
import rasterio
import rasterio.mask
from shapely.geometry import Point
from datetime import timedelta
from GIS_operations import clip

def unzip_tar(f,dest):
    file = tarfile.open(f)
    file.extractall(dest)
    file.close()

def get_previous_and_next_month_dates(input_date):
    previous_month_date = input_date - timedelta(days=80)
    next_month_date = input_date + timedelta(days=80)  # Using 31 days to ensure we move to the next month
    return previous_month_date, next_month_date

def get_user_input(rad=2500,name='test',year=2023,month=7,day=8):
    latlong = input("Latitude, Longitude: ")
    latlong = latlong.split(",")
    lat = float(latlong[0])
    long = float(latlong[1])
    name = 'test'
    rad = float(input("Radius around point: "))
    name = input("Name area: ")
    year = int(input('Enter a year '))
    month = int(input('Enter a month (number) '))
    day = int(input('Enter a day (number) '))
    date = datetime.date(year, month, day)
    return lat,long,rad,name,date

def create_gpkg(lon, lat, output_file, buffer_meters=100):
    # Create a Point geometry at the specified longitude and latitude
    pt = Point(lon, lat)
    pt_df = gpd.GeoDataFrame(geometry=[pt], crs=4326)
    buff1 = pt_df.copy()
    buff1 = buff1.to_crs(3857)
    buff1['geometry'] = buff1.geometry.buffer(buffer_meters)
    buff1 = buff1.to_crs(32631)
    buff1.to_file(output_file, driver="GPKG")
    return buff1

def make_rgb(dest,image,data):
    with rasterio.open(
        dest,
        "w",
        driver="GTiff",
        height=image.height,
        width=image.width,
        count=3,
        dtype="uint8",
        crs=image.crs,
        transform=image.transform,
        nodata=255,
    ) as dst:
        dst.write((data["B4"]/65535*255), indexes=1)
        dst.write((data["B3"]/65535*255), indexes=2)
        dst.write((data["B2"]/65535*255), indexes=3)
    return dest

def get_clipped_rgb(curdest, curname, aoi, outputdest, qa_band):
    for i in glob.glob(curdest + "/unzipped/*"):
        if curname in i:
            bands = glob.glob(i + "/*")
            qa_aoi_clip = clip(outputdest+'qa_aoi_clip.tif', qa_band, aoi)
            image = rasterio.open(qa_aoi_clip)
            im = image.read(1)
            rgbbands = [j for j in bands if (("B2.TIF" in j) or ("B3.TIF" in j) or ("B4.TIF" in j)) and ("aux" not in j)]
            rgbdata = {}
            for rgbband in rgbbands:
                band = rgbband[-6:-4]
                r_dest = outputdest+band + ".tif"
                r_clipped = clip(r_dest, rgbband, aoi)
                image = rasterio.open(r_clipped)
                im = image.read(1)
                rgbdata[band] = im
            return make_rgb(outputdest+'rgb.tif', image, rgbdata)

def plot_rgb_temp(name, curtemp, currgb, outputdest,vmin=10,vmax=30):
    with rasterio.open(currgb) as src:
        rgb_data = src.read()
        rgb_data = rgb_data.astype(float)
    with rasterio.open(curtemp) as src:
        temp_data = src.read(1, masked=True)
        temp_data = temp_data.astype(float)
        temp_data[temp_data == 256] = np.nan

    fig, ax = plt.subplots(1)
    contrast = 3.5
    brightness = .01
    r = rgb_data[0]/256
    g = rgb_data[1]/256
    b = rgb_data[2]/256
    rgb_image = np.stack([r,g,b], axis=-1)
    rgb_image[rgb_image == 0.0] = 1
    rgb_image = (rgb_image*contrast)+brightness
    rgb_image = np.clip(rgb_image,a_min=0,a_max=1)
    pos = ax.imshow(rgb_image)

    hsv_modified2 = cm.get_cmap('Reds', 256)  # create new hsv colormaps in range of 0.3 (green) to 0.7 (blue)
    newcmp2 = ListedColormap(hsv_modified2(np.linspace(0.3, 1., 256)))  # show figure
    pos2 = ax.imshow(temp_data, cmap=newcmp2)

    pos2.set_clim(vmin, vmax)
    fig.colorbar(pos2,label="Celsius")
    plt.axis('off')
    plt.title(name[-10:])
    fig.tight_layout()
    plt.savefig(outputdest+'figures/'+name+'.png')
    # plt.show()
