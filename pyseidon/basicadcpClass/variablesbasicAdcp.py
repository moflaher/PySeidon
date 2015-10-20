#!/usr/bin/python2.7
# encoding: utf-8

from __future__ import division
import numpy as np
from numpy.ma import MaskError
import h5py
from pyseidon.utilities.miscellaneous import mattime_to_datetime

class _load_basicadcp:
    """
    **'Variables' subset in ADCP class**

    It contains the following numpy arrays: ::

                      _bins = depth of measurement bins, 1D array, shape=(bins)
                     |_depth = depth, negative from surface down, time serie, 2D array, shape=(time,bins)
                     |_dir_vel = velocity direction time serie, 2D array, shape=(time,bins)
                     |_east_vel = East velocity time serie, 2D array, shape=(time,bins)
                     |_lat = latitude, float, decimal degrees
                     |_lon = lontitude, float, decimal degrees
                     |_mag_signed_vel = signed velocity time serie, 2D array, shape=(time,bins)
                     |_matlabTime = matlab time, 1D array, shape=(time)
     ADCP.Variables._|_north_vel = East velocity time serie, 2D array, shape=(time,bins)
                     |_percent_of_depth = percent of the water column measured by ADCP, float
                     |_surf = pressure at surface timeserie, 1D array, shape=(time)
                     |_el = elevation (m) at surface timeserie, 1D array, shape=(time)
                     |_ua = depth averaged velocity component timeserie, 1D array, shape=(time)
                     |_va = depth averaged velocity component timeserie, 1D array, shape=(time)
                     |_ucross = ???, 1D array, shape=(time)
                     |_ualong = ???, 1D array, shape=(time)

    """
    def __init__(self,cls, History, debug=False):
        if debug:
            print 'Loading variables...'
        # Pointer to History
        setattr(self, '_History', History)


        # TR: fudge factor, squeeze out the 5 top % of the water column
        self.percent_of_depth=0.95

        #Test if load with h5py or scipy
        if not type(cls.Data)==h5py._hl.files.File:
            self.lat = cls.Data['lat']
            self.lon = cls.Data['lon']
            #self.bins = cls.Data['data'].bins[:].ravel()
            self.north_vel = cls.Data['data'].north_vel[:]
            self.east_vel = cls.Data['data'].east_vel[:]
            #self.vert_vel = cls.Data['data'].vert_vel[:]
            #self.dir_vel = cls.Data['data'].dir_vel[:]
            #self.mag_signed_vel = cls.Data['data'].mag_signed_vel[:]
            #self.pressure = cls.Data['pres']
            #self.surf = self.pressure.surf[:].ravel()
            #self.el = self.surf
            self.time = cls.Data['time']
            self.matlabTime = self.time.mtime[:].ravel()
            #try:
            #    self.ucross = cls.Data['data'].ucross[:]
            #    self.ualong = cls.Data['data'].ualong[:]
            #except AttributeError:
            #    pass

        else:
            self.lat = cls.Data['lat'][0][0]
            self.lon = cls.Data['lon'][0][0]
            #self.bins = cls.Data['data']['bins'][:].ravel()
            self.north_vel = cls.Data['data']['north_vel'][:].T
            self.east_vel = cls.Data['data']['east_vel'][:].T
            #self.vert_vel = cls.Data['data']['vert_vel'][:].T
            #self.dir_vel = cls.Data['data']['dir_vel'][:].T
            #self.mag_signed_vel = cls.Data['data']['mag_signed_vel'][:].T
            #self.pressure = cls.Data['pres']
            #self.surf = self.pressure['surf'][:].ravel()
            #self.el = self.surf
            self.time = cls.Data['time']
            self.matlabTime = self.time['mtime'][:].ravel()
            #try:
            #    self.ucross = cls.Data['data']['Ucross'][:].T
            #    self.ualong = cls.Data['data']['Ualong'][:].T
            #except KeyError:
            #    pass

        #-Append message to History field
        start = mattime_to_datetime(self.matlabTime[0])
        end = mattime_to_datetime(self.matlabTime[-1])
        text = 'Temporal domain from ' + str(start) +\
                ' to ' + str(end)
        self._History.append(text)

        #Find the depth average of a variable based on percent_of_depth
        #choosen by the user. Currently only working for east_vel (u) and
        #north_vel (v)
        #TR: alaternative with percent of the depth
        #ind = np.argwhere(self.bins < self.percent_of_depth * self.surf[:,np.newaxis])
        #ind = np.argwhere(self.bins < self.surf[:,np.newaxis])
        #index = ind[np.r_[ind[1:,0] != ind[:-1,0], True]]
        #try:
        #    data_ma_u = np.ma.array(self.east_vel,
        #                mask=np.arange(self.east_vel.shape[1]) > index[:, 1, np.newaxis])
        #    data_ma_u=np.ma.masked_array(data_ma_u,np.isnan(data_ma_u))
        #except MaskError:
        data_ma_u=np.ma.masked_array(self.east_vel,np.isnan(self.east_vel))

        #try:
            #data_ma_v = np.ma.array(self.north_vel,
                        #mask=np.arange(self.north_vel.shape[1]) > index[:, 1, np.newaxis])
            #data_ma_v=np.ma.masked_array(data_ma_v,np.isnan(data_ma_v))
        #except MaskError:
        data_ma_v=np.ma.masked_array(self.north_vel,np.isnan(self.north_vel))
        
        self.ua = data_ma_u
        self.va = data_ma_v

        # Compute depth with fvcom convention, negative from surface down
        #self.depth = np.ones(self.north_vel.shape) * np.nan
        #for t in range(self.matlabTime.shape[0]):
            ##i = np.where(np.isnan(self.north_vel[t,:]))[0][0]
            ##z = self.bins[i]
            #self.depth[t, :] = self.bins[:] - self.surf[t]
        #self.depth[np.where(self.depth>0.0)] = np.nan

        #if debug:
            #print '...Passed'

        return
