import cv2
import numpy as np
import rasterio
import rasterio.mask
import waterxplore.level2_temperature as level2_temperature
import geopandas as gpd

def loadfile(file='../../data/brt/top100nl_Waterdeel.gpkg',dis=True):
    loaded = gpd.read_file(file)
    if dis:
        loaded = loaded.dissolve()
    return loaded

def clip(dest,qa_band, clip_area):
    with rasterio.open(qa_band) as src:
        if clip_area.crs != src.crs.to_epsg():
            clip_area = clip_area.to_crs(src.crs.to_epsg())

        nodata = 256
        out_image, out_transform = rasterio.mask.mask(src, clip_area.geometry, indexes=1,
                                                      crop=True, nodata=nodata)
        out_meta = src.meta
        out_meta.update({"driver": "GTiff",
                         "transform": out_transform,
                         "height": out_image.shape[0],
                         "width": out_image.shape[1],
                         })
        with rasterio.open(dest, "w", **out_meta) as out:
            out.write(out_image, indexes=1)

    return dest

def mask(dest,file,choice=0):
    image = rasterio.open(file)
    im = image.read(1)
    if choice == 0:
        print("MASK CHOICE",choice)
        im2 = (im == 21952) | (im == 21824) | (im == 23888) | (im == 23826) | (im == 21890) |\
            (im == 21762) | (im == 22018) | (im == 22080) | (im == 22280) | (im == 23826) | (im == 23888) |\
            (im == 24082) | (im == 24144)
    elif choice == 1:
        print("MASK CHOICE",choice)
        im2 = (im == 21952)
    else:
        im2 = im
    im2 = im2 * 1
    data = im * im2
    mask_filename = dest+'/masked_water_clip_'+str(choice)+'.tif'
    with rasterio.open(mask_filename, 'w', **image.profile) as dst:
        dst.write(data, indexes=1)
    return mask_filename

def erode(file,kernelsize=2,iter=1,nanval=0):
    image = rasterio.open(file)
    im = image.read(1)
    binary_mask = np.ones_like(im)
    binary_mask[im == nanval] = 0

    kernel = np.ones((kernelsize, kernelsize), np.uint8)
    binary_mask = cv2.erode(binary_mask, kernel, iterations=iter)

    im[binary_mask == 0] = 0
    return im

def temperature(dest,im,image):
    lst = level2_temperature.Level2Lst()
    wts = lst.process_landsat_temperature(band_10=im)
    wts[wts<-10] = np.nan
    with rasterio.open(dest+'/water_temperature.tif', 'w',**image.profile) as dst:
        dst.write(wts, indexes=1)
    return dest+'/water_temperature.tif'

def mask_erode_temperature(files,dest,kernel=2,iter=1,c=0):
    water = loadfile(r"C:\Users\RWS Datalab\Desktop\data\brt\top100nl_Waterdeel.gpkg")
    print("Load QA Pixel and B10 band")
    qa_file = ""
    b10_file = ""
    bands = [i for i in files if (i.endswith("QA_PIXEL.TIF")) or (i.endswith("B10.TIF"))]
    if "QA" in bands[0]:
        qa_file = bands[0]
        b10_file = bands[1]
    else:
        b10_file = bands[0]
        qa_file = bands[1]
    qa_file = clip(dest + '/qa_water_clip.tif', qa_file, water)
    print("Mask with QA pixel")
    masked = mask(dest,qa_file,c)
    print("Erode")
    masked_eroded = erode(masked, kernel, iter)
    print("Update and save B10 band with mask and erosion",b10_file)
    b10_file = clip(dest + '/water_clip.tif', b10_file, water)
    image = rasterio.open(b10_file)
    im = image.read(1)
    im[masked_eroded == 0] = 0
    im[im == 256] = 0
    with rasterio.open(dest + '/eroded_masked_water_clip.tif', 'w', **image.profile) as dst:
        dst.write(im, indexes=1)
    print("Temperature")
    temperature_filename = temperature(dest, im, image)
    return temperature_filename
