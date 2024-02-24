import glob
from waterxplore.helper import create_gpkg, get_previous_and_next_month_dates, \
                    get_user_input, plot_rgb_temp, get_clipped_rgb, unzip_tar
import os
os.chdir("../")
from landsatxplore.api import API
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
