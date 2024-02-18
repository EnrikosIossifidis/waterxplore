# -*- coding: utf-8 -*-
"""Documentation about the Landsat module."""

import numpy as np


class Level2Lst(object):
    """
    Module for converting Landsat level-2 DN to LST degrees Celcius.
    """
    def __init__(self):
        self._scaler_factor = 0.00341802
        self._offset = 149
        self._diff_kelving_celcius = 273.15

    def _scale(self, DN):
        """
        Convert level 2 digital number to kelvin temperature.
        Parameters
        ----------
        DN: ditigal number.

        Returns
        -------
        temperature in Kelvin.
        """
        return (DN * self._scaler_factor) + self._offset

    def _kelvin_to_degree(self, kelvin):
        """
        Convert Kelvin to degrees.

        Parameters
        ----------
        kelvin: kelvin degrees.

        Returns
        -------
        Celcius degrees.
        """
        return kelvin - self._diff_kelving_celcius

    def process_landsat_temperature(self, band_10):
        """
        Convert landsat level 2 TIR to temperature (Degrees Celcius).

        Parameters
        ----------
        DN: Digital Number Landsat level-2.

        Returns
        -------
        Temperature (Degrees Celcius).
        """
        scaled = self._scale(band_10)
        celcius = self._kelvin_to_degree(scaled)
        celcius[band_10 == np.nan] = np.nan
        return celcius
