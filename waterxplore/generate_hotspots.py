import glob
import numpy as np
import pandas as pd
import rasterio as rio
import matplotlib.pyplot as plt
import glob
import pandas as pd
from PIL import Image
from datetime import datetime
from waterxplore.helper import plot_rgb_temp

def load_tempfiles(tempfiles):
    rowdata = []
    shape = ()
    for tempfile in tempfiles:
        image = rio.open(tempfile)
        data = image.read(1, masked=True)
        data = data.astype(float)
        data[data == 256] = np.nan
        # print(data.shape)
        shape = data.shape
        med = np.nanmedian(data)
        data = data - med
        # data[data>5] = np.nan
        data = data.flatten()
        rowdata.append(data.data)
    return np.array(rowdata),shape,image

def comp_mean(a, l):
    if np.isnan(a).all():
        return np.nan
    else:
        s = 0
        for i in a:
            if not np.isnan(i):
                s += i
        return s / l

def plot_hotspots(dest=r"C:\Users\RWS Datalab\Desktop\cc\waterxplore\data\output\test"):
    tempfiles = [f for f in glob.glob(dest + "/*.tif") if 'temp' in f and 'aux' not in f]

    rowdata, org_shape, org_image = load_tempfiles(tempfiles)

    rowdata[abs(rowdata) > 6] = np.nan  # remove pixels that differ more than 5 Celsius degrees
    rowdata[rowdata < 0] = np.nan   # remove pixels that are colder than the median

    # compute the mean deviation of each pixel over all tempfiles
    l = len(tempfiles)
    means = np.array([comp_mean(r, l) for r in rowdata.T])
    means = np.reshape(means, org_shape)

    temp_file_means = dest+"/temp-means.tif"
    with rio.open(temp_file_means, 'w',**org_image.profile) as dst:
        dst.write(means, indexes=1)

    name = "HOTSPOTS"
    rgb_file = [f for f in glob.glob(dest+"/*.tif") if 'rgb' in f and 'aux' not in f][0]
    plot_rgb_temp(name,temp_file_means,rgb_file,dest+"/",np.nanmin(means),np.nanmax(means),name)
