#!/usr/bin/env python

"""
This module provides utilities for calculating the level
variance data and then storing them together with their
corresponding metadata in the hdf5 format. The code below
relies heavily on the tools from the spectral_stats package,
which can be obtained from:
https://github.com/JanSuntajs/spectral_statistics_tools


"""

import os
import numpy as np
import glob
import h5py

from spectral_stats.spectra import Spectra

from qmbmodels.utils import set_mkl_lib
from qmbmodels.utils.cmd_parser_tools import arg_parser, arg_parser_general

_sff_keys = ['lvl_min_tau', 'lvl_max_tau', 'lvl_n_tau',
             'lvl_unfolding_n', ]

_sff_parse_dict = {'lvl_min_tau': [float, -5],
                   'lvl_max_tau': [float, 2],
                   'lvl_n_tau': [int, 1000],
                   'lvl_unfolding_n': [int, 3], }

# which attributes of the Spectra class instance to exclude
# from the final hdf5 file

_filt_exclude = ['filter', 'dims']
# which attributes to consider as separate datasets
_misc_include = ['mean_ener', 'sq_ham_tr', 'ham_tr_sq', 'gamma',
                 ]

# sfflist text descriptor
sfflist_desc = """
This string provides a textual descriptor of the
'SFF_spectra' hdf5 dataset. sfflist is a ndarray
of the shape (nsamples + 1, len(taulist)) where
nsamples is the number of different disorder
realizations for which the energy spectra of the
quantum hamiltonians have been calculated, and
len(taulist) is the number of tau values for which
the spectral form factor has been evaluated.
The first (zeroth, in python's numbering) entry
of the sfflist array is the list of tau values.
Other entries are calculated according to the
formula:


sfflist[m + 1, n] = np.sum(weights * np.exp(-1j * taulist[n] * spectrum[m]))

Where spectrum[m] is the m-th entry in the array of the
energy spectra and taulist[n] is the n-th entry in the
array of tau values. 'weights' is an array of some
multiplicative prefactors. No additional operations
have been performed on the spectra so that one can
also calculate averages, standard deviations and other
quantities of interest, if so desired. 'np' prefix
stands for the numpy python library, which we used
in the calculation.

See manuscript at: https://arxiv.org/abs/1905.06345
for a more technical introduction of the Spectral form
factor.

"""

sff_desc = """
This string provides a textual description of the
'SFF_spectrum' hdf5 dataset. sff is a ndarray of the
shape (3, len(taulist)) where len(taulist) stands for
the number of tau values at which sff has been
evaluated. Entries in the sff array:

sff[0]: taulist -> tau values, at which sff was evaluated
sff[1]: sff with the included disconnected part. This
        quantity is calculated according to the definition:
        np.mean(np.abs(sfflist)**2, axis=0). Here, sfflist
        is an array of sff spectra obtained for different
        disorder realizations.
sff[2]: disconnected part of the sff dependence, obtained
        according to the definition:
        np.abs(np.mean(sfflist, axis=0))**2

See manuscript at: https://arxiv.org/abs/1905.06345
for a more technical introduction of the Spectral form
factor.
"""

if __name__ == '__main__':

    sffDict, sffextra = arg_parser_general(_sff_parse_dict)
    argsDict, extra = arg_parser([], [])

    min_tau, max_tau, n_tau, eta, unfold_n, sff_filter = [
        sffDict[key] for key in _sff_parse_dict.keys()]

    print(min_tau, max_tau, n_tau, sff_filter)

    savepath = argsDict['results']
    print(savepath)

    try:
        file = glob.glob(f"{savepath}/*.hdf5")[0]
        print('delamo')

        with h5py.File(file, 'a') as f:

            data = f['Eigenvalues'][:]

            attrs = dict(f['Eigenvalues'].attrs)
            attrs.update(sffDict)
            # create the spectra class instance
            taulist = np.logspace(min_tau, max_tau, n_tau)

            # if the sff spectrum dataset does not yet exist, create it
            # perform the calculations
            spc = Spectra(data)
            spc.spectral_width = (0., 1.)
            spc.spectral_unfolding(n=unfold_n, merge=False, correct_slope=True)
            spc.get_ham_misc(individual=True)
            spc.spectral_filtering(filter_key=sff_filter, eta=eta)
            sfflist = np.zeros(
                (spc.nsamples + 1, len(taulist)), dtype=np.complex128)
            sfflist[0] = taulist
            # calculate the SFF
            sfflist[1:, :] = spc.calc_sff(taulist, return_sfflist=True)
            # gather the results
            sffvals = np.array([spc.taulist, spc.sff, spc.sff_uncon])

            # prepare additional attributes
            filt_dict = {key: spc.filt_dict[key] for key in spc.filt_dict
                         if key not in _filt_exclude}
            misc_dict = {key: spc.misc_dict[key]
                         for key in spc.misc_dict if key not in _misc_include}
            misc0 = spc.misc0_dict.copy()
            misc0_keys = [key for key in misc0]

            for key in misc0_keys:
                misc0[key + '0'] = misc0.pop(key)
            attrs.update(spc.unfold_dict.copy())

            for dict_ in (misc_dict, filt_dict, misc0):
                attrs.update(dict_)

            attrs.update({'nener': spc.nener, 'nsamples': spc.nsamples,
                          'nener0': spc._nener, 'nsamples0': spc._nsamples})

            # add the actual sff values
            if 'SFF_spectra' not in f.keys():

                f.create_dataset('SFF_spectra', data=sfflist,
                                 maxshape=(None, None))
                f.create_dataset('SFF_spectrum', data=sffvals,
                                 maxshape=(3, None))

                f['SFF_spectra'].attrs['Description'] = sfflist_desc
                f['SFF_spectrum'].attrs['Description'] = sff_desc

            else:
                f['SFF_spectra'].resize(sfflist.shape)
                f['SFF_spectrum'].resize(sffvals.shape)

                f['SFF_spectra'][()] = sfflist
                f['SFF_spectrum'][()] = sffvals

            # data which led to the SFF calculation
            for key in _misc_include:

                if key not in f.keys():

                    f.create_dataset(
                        key, data=spc.misc_dict[key], maxshape=(None,))
                else:
                    f[key].resize(spc.misc_dict[key].shape)
                    f[key][()] = spc.misc_dict[key]

            # append the attributes
            for key1 in ['SFF_spectra', 'SFF_spectrum'] + _misc_include:
                for key2, value in attrs.items():
                    f[key1].attrs[key2] = value

    except IndexError:
        print('ne delamo')
        pass
