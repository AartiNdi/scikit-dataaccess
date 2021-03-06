# The MIT License (MIT)
# Copyright (c) 2016 Massachusetts Institute of Technology
#
# Authors: Victor Pankratius, Justin Li, Cody Rude
# This software has been created in projects supported by the US National
# Science Foundation and NASA (PI: Pankratius)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# """@package GLDAS
# Provides classes for accessing GLDAS data.
# """

# mithagi required Base imports
from skdaccess.framework.data_class import DataFetcherStorage, TableWrapper
from skdaccess.utilities.grace_util import read_grace_data


# Standard library imports
import os
from ftplib import FTP
import re
from collections import OrderedDict

# 3rd party package imports
import pandas as pd
import numpy as np

class DataFetcher(DataFetcherStorage):
    ''' Data Fetcher for GLDAS data '''

    def __init__(self, ap_paramList, start_date = None, end_date = None, resample = False):
        '''
        Construct a GLDAS Data Fetcher

        @param ap_paramList[geo_point]: Autolist of Geographic location tuples
        @param start_date: Beginning date
        @param end_date: Ending date
        @param resample: Resample the data to daily resolution, leaving NaN's in days without data (Default True)
        '''
        
        self.start_date = start_date
        self.end_date = end_date
        self.resample = resample
        super(DataFetcher, self).__init__(ap_paramList)
        
    def output(self):
        ''' 
        Create data wrapper of GLDAS data for specified geopoint.

        @return GLDAS Data Wrapper
        '''

        data_file = DataFetcher.getDataLocation('gldas')
        if data_file is None:
            print("No data available")
            return None


        geo_point_list = self.ap_paramList[0]()

        full_data = read_grace_data(data_file, 'Latitude','Longitude','Water_Thickness','Time')
        
        # Get appropriate time range
        start_date = self.start_date
        end_date = self.end_date

        if start_date == None:
            start_date = dates.iloc[0]

        elif type(start_date) == str:
            start_date = pd.to_datetime(start_date)


        if end_date == None:
            end_date = dates.iloc[-1]

        elif type(end_date) == str:
            end_date == pd.to_datetime(end_date)
        
        data = full_data[start_date:end_date]

        data_dict = OrderedDict()
        for geo_point in geo_point_list:
            

            lat = geo_point[0]
            lon = (geo_point[1] + 360) % 360

            lat_index = round(lat - (lat % 1)) + 0.5
            lon_index = round(lon - (lon % 1)) + 0.5

            gldas_data = data.loc[:,lat_index, lon_index]
            gldas_data.name = 'Equivalent Water Depth (cm)'

            gldas_unc = pd.Series(np.ones(len(gldas_data),dtype=np.float) * np.nan, index=gldas_data.index,name="Uncertainty")
            gldas_data = pd.concat([gldas_data, gldas_unc], axis=1)

            if self.resample == True:
                gldas_data = gldas_data.reindex(pd.date_range(start_date, end_date))

            label = str(geo_point[0]) + ', ' + str(geo_point[1])

            data_dict[label] = gldas_data

        gldas_data.columns = ['Equivalent Water Thickness (cm)', 'Uncertainty']
        return(TableWrapper(data_dict, default_columns = ['Equivalent Water Thickness (cm)'],
                            default_error_columns=['Uncertainty']))


    @classmethod
    def downloadFullDataset(cls, out_file=None, use_file=None):
        '''
        Download GLDAS data
        
        @param out_file: Output filename for parsed data
        @param use_file: Directory of downloaded data. If None, data will be downloaded.

        @return Absolute path of parsed data
        '''

        # No post processing for this data is necessary. If local data is
        # specified, just set its location.
        if use_file != None:
            print('Setting data location for local data')
            return os.path.abspath(use_file)


        # If no local data, download data from server
        print("Downloading GLDAS Land Mass Data")
        ftp = FTP("podaac-ftp.jpl.nasa.gov")
        ftp.login()
        ftp.cwd('allData/tellus/L3/gldas_monthly/netcdf/')
        dir_list = list(ftp.nlst(''))
        file_list = [file for file in dir_list if re.search('.nc$', file)]
        if len(file_list) > 1:
            raise ValueError('Too many files found in GLDAS directory')

        if out_file == None:
            out_file = file_list[0]

        ftp.retrbinary('RETR ' + file_list[0], open(''+out_file, 'wb').write)


        cls.setDataLocation('gldas', os.path.abspath(file_list[0]))

            

    def __str__(self):
        '''
        String representation of data fetcher

        @return String listing the name and geopoint of data fetcher
        '''
        return 'GLDAS Data Fetcher' + super(DataFetcher, self).__str__()


