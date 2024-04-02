"""The main script."""
import os
import glob
import rasterio
import shutil
import numpy as np
from datetime import datetime
from waterxplore.helper import create_gpkg, get_previous_and_next_month_dates, \
                    get_user_input, plot_rgb_temp, get_clipped_rgb, unzip_tar
from waterxplore.GIS_operations import mask_erode_temperature,clip,loadfile
from waterxplore.make_gif import makegif
from waterxplore.generate_gif import get_landsat_scenes,get_existing_temp_files
from waterxplore.generate_hotspots import plot_hotspots
from landsatxplore.api import API
from landsatxplore.earthexplorer import EarthExplorer, EarthExplorerError
from setuptools import setup, find_packages

def get_existing_temp_files2(dest,im_list):
    files = glob.glob(dest+"/*")
    tempfiles = {i: 0 for i in im_list}
    for i in im_list:
        for f in files:
            if i in f:
                temp_file = [file for file in glob.glob(f+"/*.tif") if 'temperature' in file]
                if temp_file:
                    tempfiles[i] = temp_file[0]
    return tempfiles

if __name__ == "__main__":
    months = {1:"januari",2:"februari",3:"maart",4:"april",5:"mei",6:"juni",7:"juli",
              8:"augustus",9:"september",10:"oktober", 11:"november", 12:"december"}

    # get user input
    lat,long,rad,name,date,period = get_user_input()
    output_dest = "./data/output/"+name
    if os.path.exists(output_dest):
        shutil.rmtree(output_dest)
    os.mkdir(output_dest)
    os.mkdir(output_dest+"/figures")

    # get aoi radius -> create shp area
    create_gpkg(long, lat, output_dest+"/"+name+'.gpkg',rad)
    aoi = loadfile(output_dest+"/"+name+'.gpkg')

    # get landsat images in area (around date)
    username = 'enrikosiossifidis'
    password = 'dummy'
    images, im_list = get_landsat_scenes(username,password,lat,long,date,period)
    print("LEN IMAGES",len(im_list))

    # retrieve existing temperature images
    classification_method = 0
    k = 3
    iterations = 1
    method = str(classification_method)+str(k)+str(iterations)
    processed_dest = "./data/processed/"+method
    if not os.path.exists(processed_dest):
        os.mkdir(processed_dest)
    tempfiles = get_existing_temp_files2(processed_dest, im_list)
    todownload = [k for k,v in tempfiles.items() if v==0]
    print("\nLEN MISSING RAW FILES", len(todownload))

    download = True
    for cur in todownload:
        curdate = datetime.strptime(cur.split("_")[3],"%Y%m%d")
        curmonth = months[curdate.month]
        landsat_dest = "./data/raw/" + curmonth + "/" + cur
        if not os.path.exists(landsat_dest):
            if download:
                try:
                    ee = EarthExplorer(username, password)
                    ee.download(cur, output_dir=landsat_dest)
                    ee.logout()
                except EarthExplorerError:
                    print("")
                tarfilename = glob.glob(landsat_dest+"/*.tar")
                if tarfilename:
                    unzip_tar(tarfilename[0],landsat_dest)
                    os.remove(tarfilename[0])

        if os.path.exists(landsat_dest):
            # compute temperature maps (if not already computed)
            processed_files_dest = processed_dest+"/"+cur
            if os.path.exists(processed_files_dest):
                os.remove(processed_files_dest)
            os.mkdir(processed_files_dest)
            landsat_files = list(glob.glob(landsat_dest+"/*"))
            if landsat_files:
                curtempfile = mask_erode_temperature(landsat_files,processed_files_dest,k,iterations,classification_method)
                tempfiles[cur] = curtempfile # update tempfiles with last computed file

    # tempfiles = {cur:curtempfile}
    # print("TEMPFILES AFTER", tempfiles)

    temp_clipped_files = []
    rgb_clipped_files = []
    names = []
    for name, curtemp in tempfiles.items():
        if curtemp:
            # clip satellite bands to aoi and save plot
            curdate = datetime.strptime(name.split("_")[-4], "%Y%m%d")
            curmonth = months[curdate.month]
            curdest = processed_dest+"/"+name
            cursplit = name.split("_")
            curname = cursplit[2]+"_"+cursplit[3]
            if os.path.isfile(curdest+"/qa_water_clip.tif"):
                qa_file = curdest+"/qa_water_clip.tif"
            else:
                continue
            landsat_dest = "./data/raw/" + curmonth + "/" + name
            rgb_clipped_files.append(get_clipped_rgb(landsat_dest, aoi, output_dest+"/"+curname, qa_file))
            temp_clipped_files.append(clip(output_dest+"/"+curname+'-temp-clipped.tif', curtemp, aoi))
            names.append(name)

    vmin = 100
    vmax = 0
    for t in temp_clipped_files:
        with rasterio.open(t) as src:
            temp_im = src.read(1, masked=True)
            temp_im = temp_im.astype(float)
            temp_im[temp_im > 255] = np.nan
        curmin = np.nanmin(temp_im)
        curmax = np.nanmax(temp_im)
        if vmin > curmin:
            vmin = curmin
        if vmax < curmax:
            vmax = curmax

    for ix, rgb in enumerate(rgb_clipped_files):
        plot_rgb_temp(names[ix],temp_clipped_files[ix],rgb,output_dest+"/",vmin,vmax)

    makegif(output_dest)
    plot_hotspots(output_dest)
