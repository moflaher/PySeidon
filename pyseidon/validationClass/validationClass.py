#!/usr/bin/python2.7
# encoding: utf-8

from __future__ import division

import numpy as np
import pandas as pd
import cPickle as pkl

#Quick fix
from scipy.io import savemat
from utide import solve

#Local import
from compareData import *
from valTable import valTable
from variablesValidation import _load_validation
from pyseidon.utilities.interpolation_utils import *

# Local import
from plotsValidation import taylorDiagram, benchmarksMap
# Custom error
from pyseidon.utilities.pyseidon_error import PyseidonError


class Validation:
    """
    **Validation class/structure**

    Class structured as follows: ::

                   _History = Quality Control metadata
                  |_Variables. = observed and simulated variables and quantities
                  |_validate_data = validation method/function against timeseries
      Validation._|_validate_harmonics = validation method/function against
                  |                      harmonic coefficients
                  |_Save_as = "save as" function

    Inputs:
      - observed = standalone or tuple of PySeidon measurement object (i.e. ADCP, TideGauge, Drifter,...)
      - simulated = any PySeidon simulation object (i.e. FVCOM or Station)
    Option:
      - flow = impose flow comparison by surface flow ('sf'), depth-averaged flow ('daf') or at any depth (float)
    """
    def __init__(self, observed, simulated, flow=[], closefallback=False, debug=False, debug_plot=False):
        self._debug = debug
        self._flow = flow
        if type(observed) in [tuple, list]:
            self._multi = True
        else:
            self._multi = False
        self._debug_plot = debug_plot
        if debug: print '-Debug mode on-'
        
        self._closefallback=closefallback

        #Metadata
        if not self._multi:
            self.History = ['Created from ' + observed._origin_file +\
                            ' and ' + simulated._origin_file]
        else:
            self.History = ['Created from multiple measurement sources' +\
                            ' and ' + simulated._origin_file]
        self._observed = observed
        self._simulated = simulated
        if not self._multi:
            self.Variables = _load_validation(self._observed, self._simulated, flow=self._flow, closefallback=self._closefallback,debug=self._debug)

        return

    def _validate_data(self, filename=[], depth=[], plot=False,  save_csv=False, debug=False, debug_plot=False):
        """
        This method computes series of standard validation benchmarks.

        Options:
          - filename = file name of the .csv file to be saved, string.
          - depth = depth at which the validation will be performed, float.
                   Only applicable for 3D simulations.
          - plot = plot series of validation graphs, boolean.
          - flow = flow comparison by surface flow ('sf'), depth-averaged flow ('daf') or at any depth (float)

        *References*
          - NOAA. NOS standards for evaluating operational nowcast and
            forecast hydrodynamic model systems, 2003.

          - K. Gunn, C. Stock-Williams. On validating numerical hydrodynamic
            models of complex tidal flow, International Journal of Marine Energy, 2013

          - N. Georgas, A. Blumberg. Establishing Confidence in Marine Forecast
            Systems: The design and skill assessment of the New York Harbor Observation
            and Prediction System, version 3 (NYHOPS v3), 2009

          - Liu, Y., P. MacCready, B. M. Hickey, E. P. Dever, P. M. Kosro, and
            N. S. Banas (2009), Evaluation of a coastal ocean circulation model for
            the Columbia River plume in summer 2004, J. Geophys. Res., 114
        """
        debug = debug or self._debug
        debug_plot = debug_plot or self._debug_plot
        #User input
        if filename==[]:
            filename = raw_input('Enter filename for csv file: ')
            filename = str(filename)
        if type(self._flow) == float:
            depth = self._flow
        if (depth==[] and self.Variables._3D):
            depth = input('Depth from surface at which the validation will be performed: ')
            depth = float(depth)
            if depth < 0.0: depth = -1.0 * depth
        if depth==[]: depth=5.0

        #initialisation
        vars = []
        threeD = self.Variables.sim._3D
        if self._flow == 'daf': threeD = False

        if self.Variables.struct['type'] == 'ADCP':
            (elev_suite, speed_suite, dir_suite, u_suite, v_suite,
             vel_suite, csp_suite) = compareUV(self.Variables.struct, threeD,
                                    plot=plot, depth=depth, save_csv=save_csv,
                                    debug=debug, debug_plot=debug_plot)
            self.Variables.struct['elev_val'] = elev_suite
            self.Variables.struct['speed_val'] = speed_suite
            self.Variables.struct['dir_val'] = dir_suite
            self.Variables.struct['u_val'] = u_suite
            self.Variables.struct['v_val'] = v_suite
            self.Variables.struct['vel_val'] = vel_suite
            # custom benchmark
            self.Variables.struct['cubic_speed_val'] = csp_suite
            # Variable to processed
            vars.append('elev')
            vars.append('speed')
            vars.append('dir')
            vars.append('u')
            vars.append('v')
            vars.append('vel')
            # custom var
            vars.append('cubic_speed')
        elif self.Variables.struct['type'] == 'basicADCP':
            (speed_suite, dir_suite, u_suite, v_suite,
             vel_suite, csp_suite) = compareUV(self.Variables.struct, threeD,
                                    plot=plot, depth=depth, save_csv=save_csv,
                                    debug=debug, debug_plot=debug_plot)
            
            self.Variables.struct['speed_val'] = speed_suite
            self.Variables.struct['dir_val'] = dir_suite
            self.Variables.struct['u_val'] = u_suite
            self.Variables.struct['v_val'] = v_suite
            self.Variables.struct['vel_val'] = vel_suite
            # custom benchmark
            self.Variables.struct['cubic_speed_val'] = csp_suite
            # Variable to processed
            
            vars.append('speed')
            vars.append('dir')
            vars.append('u')
            vars.append('v')
            vars.append('vel')
            # custom var
            vars.append('cubic_speed')

        elif self.Variables.struct['type'] == 'TideGauge':
            elev_suite_dg = compareTG(self.Variables.struct,
                                      plot=plot, save_csv=save_csv,
                                      debug=debug, debug_plot=debug_plot)
            self.Variables.struct['tg_val'] = elev_suite_dg
            #Variable to processed
            vars.append('tg')

        elif self.Variables.struct['type'] == 'Drifter':
            (elev_suite, speed_suite, dir_suite, u_suite, v_suite,
             vel_suite, csp_suite) = compareUV(self.Variables.struct, self.Variables._3D,
                                    depth=depth, plot=plot, save_csv=save_csv,
                                    debug=debug, debug_plot=debug_plot)

            self.Variables.struct['speed_val'] = speed_suite
            self.Variables.struct['dir_val'] = dir_suite
            self.Variables.struct['u_val'] = u_suite
            self.Variables.struct['v_val'] = v_suite
            # custom benchmark
            self.Variables.struct['vel_val'] = vel_suite
            self.Variables.struct['cubic_speed_val'] = csp_suite

            # Variable to processed
            vars.append('speed')
            vars.append('dir')
            vars.append('u')
            vars.append('v')
            vars.append('vel')
            # custom var
            vars.append('vel')
            vars.append('cubic_speed')

        else:
            raise PyseidonError("-This kind of measurements is not supported yet-")

        # Make csv file
        self._Benchmarks = valTable(self.Variables.struct, filename,  vars,
                                    debug=debug, debug_plot=debug_plot)

        # Display csv
        print "---Validation benchmarks---"
        pd.set_option('display.max_rows', len(self._Benchmarks))
        print(self._Benchmarks)
        pd.reset_option('display.max_rows')

    def _validate_harmonics(self, filename='', save_csv=False, debug=False, debug_plot=False):
        """
        This method computes and store in a csv file the error in %
        for each component of the harmonic analysis (i.e. *_error.csv).

        Options:
          filename: file name of the .csv file to be saved, string.
          save_csv: will save both observed and modeled harmonic
                    coefficients into *.csv files (i.e. *_harmo_coef.csv)
        """
        # User input
        if filename==[]:
            filename = raw_input('Enter filename for csv file: ')
            filename = str(filename)


        # Harmonic analysis over matching time
        if self.Variables._obstype=='adcp':
            time = self.Variables.struct['obs_time']
            lat = self.Variables.struct['lat']
            ua =  self.Variables.struct['obs_timeseries']['ua'][:]
            va =  self.Variables.struct['obs_timeseries']['va'][:]
            el =  self.Variables.struct['obs_timeseries']['elev'] [:]

            self.Variables.obs.velCoef = solve(time, ua, va, lat,
                                         constit='auto', trend=False, Rayleigh_min=0.95,
                                         method='ols', conf_int='linear')


            self.Variables.obs.elCoef = solve(time, el, None, lat,
                                         constit='auto', trend=False, Rayleigh_min=0.95,
                                         method='ols', conf_int='linear')
        elif self.Variables._obstype=='basicadcp':
            time = self.Variables.struct['obs_time']
            lat = self.Variables.struct['lat']
            ua =  self.Variables.struct['obs_timeseries']['ua'][:]
            va =  self.Variables.struct['obs_timeseries']['va'][:]


            self.Variables.obs.velCoef = solve(time, ua, va, lat,
                                         constit='auto', trend=False, Rayleigh_min=0.95,
                                         method='ols', conf_int='linear')


        elif self.Variables._obstype=='tidegauge':
            time = self.Variables.struct['obs_time']
            lat = self.Variables.struct['lat']
            el =  self.Variables.struct['obs_timeseries']['elev'] [:]

            self.Variables.obs.elCoef = solve(time, el, None, lat,
                                         constit='auto', trend=False, Rayleigh_min=0.95,
                                         method='ols', conf_int='linear')
        else:
            raise PyseidonError("--This kind of observations is not supported---")

        if self.Variables._simtype=='fvcom':
            time = self.Variables.struct['mod_time']
            lat = self.Variables.struct['lat']
            el =  self.Variables.struct['mod_timeseries']['elev'][:]

            self.Variables.sim.elCoef = solve(time, el, None, lat,
                                         constit='auto', trend=False, Rayleigh_min=0.95,
                                         method='ols', conf_int='linear')
            if self.Variables._obstype=='adcp' or self.Variables._obstype=='basicadcp':
                ua =  self.Variables.struct['mod_timeseries']['ua'][:]
                va =  self.Variables.struct['mod_timeseries']['va'][:]
                self.Variables.sim.velCoef = solve(time, ua, va, lat,
                                         constit='auto', trend=False, Rayleigh_min=0.95,
                                         method='ols', conf_int='linear')

        elif self.Variables._simtype=='station':
            time = self.Variables.struct['mod_time']
            lat = self.Variables.struct['lat']
            el = self.Variables.struct['mod_timeseries']['elev'][:]

            self.Variables.sim.elCoef = solve(time, el, None, lat,
                                         constit='auto', trend=False, Rayleigh_min=0.95,
                                         method='ols', conf_int='linear')
            if self.Variables._obstype=='adcp':
                ua = self.Variables.struct['mod_timeseries']['ua'][:]
                va = self.Variables.struct['mod_timeseries']['va'][:]
                self.Variables.sim.velCoef = solve(time, ua, va, lat,
                                         constit='auto', trend=False, Rayleigh_min=0.95,
                                         method='ols', conf_int='linear')


        # find matching and non-matching coef
        matchElCoef = []
        matchElCoefInd = []
        try:
            for i1, key1 in enumerate(self.Variables.sim.elCoef['name']):
                for i2, key2 in enumerate(self.Variables.obs.elCoef['name']):
                    if key1 == key2:
                       matchElCoefInd.append((i1,i2))
                       matchElCoef.append(key1)
            matchElCoefInd=np.array(matchElCoefInd)
            noMatchElCoef = np.delete(self.Variables.sim.elCoef['name'],
                                      matchElCoefInd[:,0])
            np.hstack((noMatchElCoef,np.delete(self.Variables.obs.elCoef['name'],
                       matchElCoefInd[:,1]) ))
        except AttributeError:
            pass

        matchVelCoef = []
        matchVelCoefInd = []
        try:
            for i1, key1 in enumerate(self.Variables.sim.velCoef['name']):
                for i2, key2 in enumerate(self.Variables.obs.velCoef['name']):
                    if key1 == key2:
                        matchVelCoefInd.append((i1, i2))
                        matchVelCoef.append(key1)
            matchVelCoefInd = np.array(matchVelCoefInd)
            noMatchVelCoef = np.delete(self.Variables.sim.velCoef['name'], matchVelCoefInd[:, 0])
            np.hstack((noMatchVelCoef, np.delete(self.Variables.obs.velCoef['name'], matchVelCoefInd[:, 1])))
        except AttributeError:
            pass


        # Compare obs. vs. sim. elevation harmo coef
        data = {}
        columns = ['A', 'g', 'A_ci', 'g_ci']

        # Store harmonics in csv files
        if save_csv:
            try:
                # observed elevation coefs
                for key in columns:
                    data[key] = self.Variables.obs.elCoef[key]
                table = pd.DataFrame(data=data, index=self.Variables.obs.elCoef['name'],
                                     columns=columns)
                # export as .csv file
                name = self.Variables.struct['name']
                save_path = name.split('/')[-1].split('.')[0]+'/'
                out_file = '{}{}_obs_el_harmo_coef.csv'.format(save_path,filename)
                table.to_csv(out_file)
                data = {}

                #modeled elevation coefs
                for key in columns:
                    data[key] = self.Variables.sim.elCoef[key]
                table = pd.DataFrame(data=data, index=self.Variables.sim.elCoef['name'],
                                     columns=columns)
                # export as .csv file
                out_file = '{}{}_sim_el_harmo_coef.csv'.format(save_path,filename)
                table.to_csv(out_file)
                data = {}
            except:
                pass

        # error in %
        if not matchElCoef==[]:
            for key in columns:
                b=self.Variables.sim.elCoef[key][matchElCoefInd[:,0]]
                a=self.Variables.obs.elCoef[key][matchElCoefInd[:,1]]
                err = abs((a-b)/a) * 100.0
                data[key] = err

            ##create table
            table = pd.DataFrame(data=data, index=matchElCoef, columns=columns)
            ##export as .csv file
            out_file = '{}{}_el_harmo_error.csv'.format(save_path,filename)
            table.to_csv(out_file)
            ##print non-matching coefs
            if not noMatchElCoef.shape[0]==0:
                print "Non-matching harmonic coefficients for elevation: ", noMatchElCoef
        else:
            print "-No matching harmonic coefficients for elevation-"

        #Compare obs. vs. sim. velocity harmo coef
        data = {}
        columns = ['Lsmaj', 'g', 'theta_ci', 'Lsmin_ci',
                   'Lsmaj_ci', 'theta', 'g_ci']

        #Store harmonics in csv files
        if (save_csv and self.Variables._obstype!='tidegauge'):
            #observed elevation coefs
            for key in columns:
                data[key] = self.Variables.obs.velCoef[key]
            table = pd.DataFrame(data=data, index=self.Variables.obs.velCoef['name'],
                                 columns=columns)
            ##export as .csv file
            out_file = '{}_obs_velo_harmo_coef.csv'.format(filename)
            table.to_csv(out_file)
            data = {}

            #modeled elevation coefs
            for key in columns:
                data[key] = self.Variables.sim.velCoef[key]
            table = pd.DataFrame(data=data, index=self.Variables.sim.velCoef['name'],
                                 columns=columns)
            ##export as .csv file
            out_file = '{}_sim_velo_harmo_coef.csv'.format(filename)
            table.to_csv(out_file)
            data = {}

        ##error in %
        if not matchVelCoef==[]:
            for key in columns:
                b=self.Variables.sim.velCoef[key][matchVelCoefInd[:,0]]
                a=self.Variables.obs.velCoef[key][matchVelCoefInd[:,1]]
                err = abs((a-b)/a) * 100.0
                data[key] = err

            ##create table
            table = pd.DataFrame(data=data, index=matchVelCoef, columns=columns)
            ##export as .csv file
            out_file = '{}_vel0_harmo_error.csv'.format(filename)
            table.to_csv(out_file)
            ##print non-matching coefs
            if not noMatchVelCoef.shape[0]==0:
                print "Non-matching harmonic coefficients for velocity: ", noMatchVelCoef
        else:
            print "-No matching harmonic coefficients for velocity-"

    def validate_data(self, filename=[], depth=[], plot=False, save_csv=False, debug=False, debug_plot=False):
        """
        This method computes series of standard validation benchmarks.

        Options:
          - filename = file name of the .csv file to be saved, string.
          - depth = depth at which the validation will be performed, float.
                   Only applicable for 3D simulations.
          - plot = plot series of validation graphs, boolean.
          - save_csv = will save benchmark values into *.csv file
                       as well as associated plots in specific folderssta

        *References*
          - NOAA. NOS standards for evaluating operational nowcast and
            forecast hydrodynamic model systems, 2003.

          - K. Gunn, C. Stock-Williams. On validating numerical hydrodynamic
            models of complex tidal flow, International Journal of Marine Energy, 2013

          - N. Georgas, A. Blumberg. Establishing Confidence in Marine Forecast
            Systems: The design and skill assessment of the New York Harbor Observation
            and Prediction System, version 3 (NYHOPS v3), 2009

          - Liu, Y., P. MacCready, B. M. Hickey, E. P. Dever, P. M. Kosro, and
            N. S. Banas (2009), Evaluation of a coastal ocean circulation model for
            the Columbia River plume in summer 2004, J. Geophys. Res., 114
        """
        if not self._multi:
            self._validate_data(filename, depth, plot, save_csv, debug, debug_plot)
            self.Benchmarks = self._Benchmarks
        else:
            I=0
            for meas in self._observed:
                try:
                    self.Variables = _load_validation(meas, self._simulated, flow=self._flow, closefallback=self._closefallback, debug=self._debug)
                    self._validate_data(filename, depth, plot, save_csv, debug, debug_plot)
                    if I == 0:
                        self.Benchmarks = self._Benchmarks
                        I += 1
                    else:
                        self.Benchmarks = pd.concat([self.Benchmarks, self._Benchmarks])
                except PyseidonError:
                    pass
        if save_csv:
            try:
                out_file = '{}_val.csv'.format(filename)
                self.Benchmarks.to_csv(out_file)
            except AttributeError:
                raise PyseidonError("-No matching measurement-")

    def validate_harmonics(self, filename=[], save_csv=False, debug=False, debug_plot=False):
        """
        This method computes and store in a csv file the error in %
        for each component of the harmonic analysis (i.e. *_error.csv).

        Options:
          filename: file name of the .csv file to be saved, string.
          save_csv: will save both observed and modeled harmonic
                    coefficients into *.csv files (i.e. *_harmo_coef.csv)
        """
        if not self._multi:
            self.Variables = _load_validation(self._observed, self._simulated, flow=self._flow, closefallback=self._closefallback, debug=self._debug)
            self._validate_harmonics(filename, save_csv, debug, debug_plot)
        else:
            for i, meas in enumerate(self._observed):
                self.Variables = _load_validation(meas, self._simulated, flow=self._flow, closefallback=self._closefallback, debug=self._debug)
                if filename == []:
                    filename = 'meas'+str(i)
                else:
                    filename = filename + '_meas'+str(i)
                self._validate_harmonics(filename, save_csv, debug, debug_plot)

    def taylor_diagram(self, savepath='', fname="taylor_diagram", debug=False):
        """
        Plots Taylor diagram based on the results of 'validate_data'

        Options:
          - savepath = folder path for saving plot, string
          - fname = filename for saving plot, string
        """
        try:
            taylorDiagram(self.Benchmarks, savepath=savepath, fname=fname, debug=debug)
        except AttributeError:
            raise PyseidonError("-validate_data needs to be run first-")

    def benchmarks_map(self, savepath='', fname="benchmarks_map", debug=False):
        """
    Plots bathymetric map & model validation benchmarks

    Options:
      - savepath = folder path for saving plot, string
      - fname = filename for saving plot, string

    Note: this function shall work only if ADCP object(s) and FVCOM object
          have been used as inputs
        """
        if not self._simulated.__module__=='pyseidon.fvcomClass.fvcomClass':
            raise PyseidonError("---work only with a combination ADCP object(s) and FVCOM object---")
        try:
            benchmarksMap(self.Benchmarks, self._observed, self._simulated, savepath=savepath, fname=fname, debug=debug)
        except AttributeError:
            raise PyseidonError("---validate_data needs to be run first---")

    def save_as(self, filename, fileformat='pickle', debug=False):
        """
        This method saves the current Validation structure as:
           - *.p, i.e. python file
           - *.mat, i.e. Matlab file

        Inputs:
          - filename = path + name of the file to be saved, string

        Options:
          - fileformat = format of the file to be saved, i.e. 'pickle' or 'matlab'
        """
        debug = debug or self._debug
        if debug: print 'Saving file...'

        #Save as different formats
        if fileformat=='pickle':
            filename = filename + ".p"
            f = open(filename, "wb")
            data = {}
            data['History'] = self.History
            try:
                data['Benchmarks'] = self.Benchmarks
            except AttributeError:
                pass
            data['Variables'] = self.Variables.__dict__
            #TR: Force caching Variables otherwise error during loading
            #    with 'netcdf4.Variable' type (see above)
            for key in data['Variables']:
                listkeys=['Variable', 'ArrayProxy', 'BaseType']
                if any([type(data['Variables'][key]).__name__==x for x in listkeys]):
                    if debug:
                        print "Force caching for " + key
                    data['Variables'][key] = data['Variables'][key][:]
            #Save in pickle file
            if debug:
                print 'Dumping in pickle file...'
            try:
                pkl.dump(data, f, protocol=pkl.HIGHEST_PROTOCOL)
            except (SystemError, MemoryError) as e:
                print '---Data too large for machine memory---'
                raise

            f.close()
        elif fileformat=='matlab':
            filename = filename + ".mat"
            #TR comment: based on MitchellO'Flaherty-Sproul's code
            dtype = float
            data = {}
            Grd = {}
            Var = {}
            Bch = {}

            data['History'] = self.History
            Bch = self.Benchmarks
            for key in Bch:
                data[key] = Bch[key]
            Var = self.Variables.__dict__
            #TR: Force caching Variables otherwise error during loading
            #    with 'netcdf4.Variable' type (see above)
            for key in Var:
                listkeys=['Variable', 'ArrayProxy', 'BaseType']
                if any([type(Var[key]).__name__==x for x in listkeys]):
                    if debug:
                        print "Force caching for " + key
                    Var[key] = Var[key][:]
                #keyV = key + '-var'
                #data[keyV] = Var[key]
                data[key] = Var[key]

            #Save in mat file file
            if debug:
                print 'Dumping in matlab file...'
            savemat(filename, data, oned_as='column')
        else:
            print "---Wrong file format---"

