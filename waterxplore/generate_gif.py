import glob
import rasterio
import numpy as np
from datetime import datetime
from waterxplore.helper import create_gpkg, get_previous_and_next_month_dates, \
                    get_user_input, plot_rgb_temp, get_clipped_rgb, unzip_tar
from waterxplore.GIS_operations import mask_erode_temperature,clip,loadfile
from waterxplore.make_gif import makegif
import os
os.chdir("../")
from landsatxplore.api import API
from landsatxplore.earthexplorer import EarthExplorer, EarthExplorerError
os.chdir("./waterxplore")

def get_landsat_scenes(username, password, lat, long, date):
    previous_month, next_month = get_previous_and_next_month_dates(date)
    print("Previous Month:", previous_month.strftime('%Y-%m-%d'))
    print("Next Month:", next_month.strftime('%Y-%m-%d'))
    api = API(username, password)
    scenes = api.search(
        dataset='landsat_ot_c2_l2',
        latitude=lat,
        longitude=long,
        start_date=previous_month.strftime('%Y-%m-%d'),
        end_date=next_month.strftime('%Y-%m-%d'),
        max_cloud_cover=10
    )

    # change filename to another format
    images = {}
    for i, s in enumerate(scenes):
        n = s['display_id']
        c = n.split("_")
        curdate = s['acquisition_date']
        curname = c[2] + curdate.strftime("%d-%m-%Y")
        images[curname] = s
    return images, [s['display_id'] for s in scenes]

def get_existing_temp_files(dest,method,im_list):
    files = glob.glob(dest+"/*")
    tempfiles = {i: 0 for i in im_list}
    for file in files:
        c = file[-16:]
        if c in im_list:
            cur = dest+"/"+c
            curfiles = glob.glob(cur+"/*")
            checkcurfiles = [i[-3:] for i in curfiles]
            if '011' in checkcurfiles:
                curfiles = glob.glob(cur+"/"+method+"/*")
            for f in curfiles:
                if 'temperature' in f:
                    tempfiles[c] = f
    return tempfiles

if __name__ == "__main__":

    # get user input
    lat,long,rad,name,date = get_user_input()
    outputdest = r"C:\Users\RWS Datalab\Desktop\data\output/"+name+"/"
    if not os.path.exists(outputdest):
        os.mkdir(outputdest)
        os.mkdir(outputdest+"figures")
    months = {1:"januari",2:"februari",3:"maart",4:"april",5:"mei",6:"juni",7:"juli",
              8:"augustus",9:"september"}

    # get aoi radius -> create shp area
    create_gpkg(long, lat, outputdest+name+'.gpkg',rad)
    aoi = loadfile(outputdest+name+'.gpkg')

    # get landsat images in area (around date)
    username = 'enrikosiossifidis'
    password = 'Jodenbuurt1011!'
    images, im_list = get_landsat_scenes(username,password,lat,long,date)

    # retrieve existing temperature images
    d = r"C:\Users\RWS Datalab\Desktop\data\clip\temp"
    classification_method = 0
    k = 2
    iterations = 1
    method = str(classification_method)+str(k)+str(iterations)
    tempfiles = get_existing_temp_files(d,method,list(images.keys()))
    print("TEMPFILES BEFORE", tempfiles)

    # compute temperature maps (if not already computed)
    todownload = [(e,im_list[i]) for i,e in enumerate(tempfiles) if not tempfiles[e]]
    print("LEN MISSING FILES", len(todownload),todownload[0])
    cur = todownload[0][0]
    curname = "_".join(images[cur]['display_id'].split("_")[2:5])
    curmonth = months[int(cur.split("-")[-2])]
    curdest = r"C:\Users\RWS Datalab\Desktop\data\landsat/" + curmonth + "/unzipped/" + curname
    try:
        ee = EarthExplorer(username, password)
        ee.download(todownload[0][1], output_dir=curdest)
        ee.logout()
    except EarthExplorerError:
        print("")
    tarfilename = glob.glob(curdest+"/*.tar")
    if tarfilename:
        unzip_tar(tarfilename[0],curdest)
    processed_files_dest = d+"/"+cur
    if not os.path.exists(processed_files_dest):
        os.mkdir(processed_files_dest)
    curtempfile = mask_erode_temperature(glob.glob(curdest+"/*"),processed_files_dest,k,iterations)
    tempfiles[cur] = curtempfile # update tempfiles with last computed file

    # tempfiles = {cur:curtempfile}
    print("TEMPFILES AFTER", tempfiles)

    temp_clipped_files = []
    rgb_clipped_files = []
    names = []
    for name, curtemp in tempfiles.items():
        if curtemp:
            # clip satellite bands to aoi and save plot
            date_str = name[6:]
            date_format = "%d-%m-%Y"
            date_obj = datetime.strptime(date_str, date_format)
            curdate = str(date_obj.strftime("%Y%m%d"))
            curname = name[:6]+"_"+curdate
            curdest = r"C:\Users\RWS Datalab\Desktop\data\landsat"+"/"+months[date_obj.month]
            qa_file = d+"/"+name+"/"
            if not os.path.isfile(qa_file+"qa_water_clip.tif"):
                if os.path.isfile(qa_file+method+"/qa_clip_water.tif"):
                    qa_file = qa_file+method+"/qa_clip_water.tif"
            else:
                qa_file = qa_file+"qa_water_clip.tif"
            rgb_clipped_files.append(get_clipped_rgb(curdest, curname, aoi, outputdest+name, qa_file))
            temp_clipped_files.append(clip(outputdest+name+'-temp-clipped.tif', curtemp, aoi))
            names.append(name)

    vmin = 100
    vmax = 0
    for t in temp_clipped_files:
        with rasterio.open(t) as src:
            temp_im = src.read(1, masked=True)
            temp_im = temp_im.astype(float)
            temp_im[temp_im == 256] = np.nan
        curmin = np.nanmin(temp_im)
        curmax = np.nanmax(temp_im)
        if vmin > curmin:
            vmin = curmin
        if vmax < curmax:
            vmax = curmax

    for ix, rgb in enumerate(rgb_clipped_files):
        plot_rgb_temp(names[ix],temp_clipped_files[ix],rgb,outputdest,vmin,vmax)

    makegif(outputdest)
