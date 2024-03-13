import glob
import numpy as np
import pandas as pd
import rasterio
import rasterio.mask
import matplotlib.pyplot as plt
import glob
import pandas as pd
from PIL import Image
from datetime import datetime

def dateobj(cur):
    cur['date_str'] = str(cur['date'].strftime("%d-%m-%Y"))
    cur['date_ordinal'] = cur['date'].toordinal()
    return cur

def load_files(folder):
    tempfiles = [f for f in glob.glob(folder+"/*") if 'temp-clipped.tif' in f]
    medians = []
    dates = []
    prs = []
    for tempfile in tempfiles:
        image = rasterio.open(tempfile)
        data = image.read(1, masked=True)
        data = data.astype(float)
        data[data == 256] = np.nan
        med = np.nanmedian(data)
        medians.append(med)

        t = tempfile.split("_")
        date = datetime.strptime(t[1][:8],"%Y%m%d")
        pathrow = t[0][-6:]
        dates.append(date)
        prs.append(pathrow)
    return pd.DataFrame(data={'medians': medians, 'date': dates,'pathrow':prs})

def plot_timeline(folder,df):
    fig = plt.figure()
    x_data = df['date_str'].values
    y_data = df['medians'].values
    if np.isnan(y_data).all():
        ymin, ymax = -275, -275
    else:
        ymin, ymax = min(y_data) - 3, max(y_data) + 3

    # Function to update the plot at each step
    time_figs = []
    for frame in range(len(x_data)):
        cur_x = x_data[:frame + 1]
        cur_y = y_data[:frame + 1]
        plt.clf() # Clear the previous plot
        plt.plot(cur_x, cur_y, marker='o', linestyle='-') # Plot the updated data
        plt.xticks(cur_x,rotation=45) # Set plot limits
        plt.ylim(ymin, ymax)
        plt.ylabel('Median Temperature') # Add labels and title
        plt.title('Temperature over time of selected area')
        fig.subplots_adjust(bottom=0.18)
        figurename = folder+"/figures/"+"median_timeframe"+"_"+str(frame)+".png"
        time_figs.append(figurename)
        plt.savefig(figurename)
    df['timeline_file'] = time_figs
    return df

def makegif(folder):
    temp_imgs = glob.glob(folder + "/figures/*")
    df = load_files(folder)
    df = df.apply(dateobj, axis=1)
    df = df.sort_values('date_ordinal')
    df.to_csv(folder+"/medians_of_temp_data.csv")
    df = plot_timeline(folder, df)

    temps = []
    for p, t in df[['pathrow', 'date']].values:
        for temp_img in temp_imgs:
            if p +"_"+ str(t.strftime("%Y%m%d")) in temp_img:
                temps.append(temp_img)
                break
    df['temp_file'] = temps

    # combine temperature and lineplot images
    images = []
    for i, d in enumerate(df[['temp_file', 'timeline_file']].values):
        image1 = Image.open(d[0])
        image2 = Image.open(d[1])
        image1 = image1.resize((900, 600))
        image2 = image2.resize((600, 500))
        image1_size = image1.size
        image2_size = image2.size
        new_image = Image.new('RGB', (image1_size[0], image1_size[1] + image2_size[1]), (250, 250, 250))
        new_image.paste(image1, (0, 0))
        new_image.paste(image2, (120, image1_size[1]))
        new_image = new_image.resize((900, 900), resample=0)  # resize them to make them a bit smaller.
        images.append(new_image)

    # create and save gif
    images[0].save(folder + '/figures/testgif.gif',
                   save_all=True, append_images=images[1:], optimize=False, duration=1000, loop=0)

if __name__ == "__main__":
    folder = r"C:\Users\RWS Datalab\Desktop\data\output\test"
    makegif(folder)
