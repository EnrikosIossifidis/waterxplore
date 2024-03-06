==================
waterxplore
==================

This Python package computes a GIF of any (Dutch) location with the water temperature, using Landsat images (USGS/NASA https://earthexplorer.usgs.gov/). Additionally, the graph of the median water temperature of each image is plotted.

.. image:: https://github.com/EnrikosIossifidis/waterxplore/blob/master/data/output/test/figures/testgif.gif
        :alt: Documentation Status

The user must give a latitude and longitude of any Dutch water (you can use Google Maps and right click to copy the coordinates of your location), the radius of the area and the time period to produce the GIF. 


* Free software: MIT license
** Documentation: https://python-boilerplate.readthedocs.io.


Features
--------

* Downloading Landsat images given latitude and longitude and time period
* Process and save Landsat images to compute water temperature for Dutch waters
* Adjust parameters to erode and select water pixels from borders
* Compute median water temperature of each frame in the GIF
* Compute hotspots of GIF: show map with pixels which have a positive devation overall


Requirements
-------

````
cd backend
echo "OPENAI_API_KEY=sk-your-key" > .env
poetry install
poetry shell
poetry run uvicorn main:app --reload --port 7001
````


Example 
-------



Important Notes
-------
* The first time the script will need to download and process many Landsat images, this will result in a long first runtime
* The Landsat images are large files, almost 1 GB per Landsat image
* Be cautious with jumping too fast to conclusions: the "waterxplore"-temperature can deviate, especially for small waters, from the real water temperature. It is likely to overestimate the real water temperature in summer for example


Credits
-------

First of all, the code was made possible by Willem Boone and the help of Rinus Schroevers. Thank you for help. Additionally I want to thank the Landelijk Meetnetwerk Water of Rijkswaterstaat and KNMI for providing daily free water and air temperature data of their stations. 

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
