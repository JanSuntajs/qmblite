import numpy as np
import os

from collections import MutableMapping
from contextlib import suppress
from glob import glob


def _extract_disorder(string, disorder_key, mode=0, idx=None):
    """
    An internal routine for returning the
    disorder key and the rest of the input
    string

    Parameters:
    -----------

    string: string
    A string from which the disorder key and its
    corresponding value are to be extracted. Example:
    'J1_1.0_J2_1.0_delta1_0.55_delta2_0.55_W_0.0_dW_1'

    disorder_key: {string, list}
    NOTE: see also the explanation of the mode
    argument below.
    If mode==0, the disorder key is a string
    designating which parameter descriptor
    corresponds to the disorder strength parameter.
    Example: 'dW'
    If mode==1, the disorder key should be a list of
    markers (specific substrings) between which a
    value of the disorder parameter is saved. TO DO:
    ADD AN EXAMPLE HERE.

    mode: int, optional
    For backwards compatibility and for compatibility
    with more general file-naming formats. The default
    value, which is also used for extracting the disorder
    from files saved according to the naming convention
    used in this package, is mode == 0.

    idx: {None, int}, optional
    If mode==1, this argument is used in case of ambiguity
    if more than one parameter value could be extracted.


    Returns:
    --------

    rest: string
    Part of the filename without the
    disorder key and its value. For the above example
    string and disorder_key, that would be:
    'J1_1.0_J2_1.0_delta1_0.55_delta2_0.55_W_0.0'

    disorder: float
    The numerical value of the disorder corresponding
    to the disorder key. In the above case, the return
    would be:
    1.0

    """

    if mode == 0:
        # append '_' at the beginning of the
        # string to make splitting w.r.t. the
        # disorder_key easier
        string = '_' + string

        # make sure there are no trailing or preceeding
        # multiple underscore by removing them
        disorder_key = disorder_key.lstrip('_').rstrip('_')
        # now make sure there is exactly one trailing
        # and one preceeding underscore
        disorder_key = '_{}_'.format(disorder_key)
        # split w.r.t. the disorder_key. The first
        # part does not contain the disorder parameter
        # value, while the second one does
        rest1, dis_string = string.split(disorder_key)
        # find the first occurence of '_' in the
        # dis_string, which indicates the length of
        # the disorder parameter value
        splitter = dis_string.find('_')
        if splitter < 0:
            disorder = dis_string
            rest2 = ''
        else:
            disorder, rest2 = dis_string[:splitter], dis_string[splitter:]

        disorder = np.float(disorder)

        # the part without the disorder value
        rest = rest1.lstrip('_') + rest2
        return rest, disorder

    elif mode == 1:

        markers = disorder_key

        markers = [marker.lstrip('_').rstrip('_') for marker in markers]

        substrings = string.split(markers[0])
        substring = [[i, subs]
                     for (i, subs) in enumerate(substrings)
                     if markers[1] in subs][idx]
        # string with the disorder parameter
        dis_string = substring[1].split(markers[1])[0]
        dis_string_ = f'{dis_string}{markers[1]}'

        substring[1] = substring[1].replace(dis_string_, '')
        substrings[substring[0]] = substring[1]
        dis_string = dis_string.replace('d', 'e')

        dis_string = dis_string.rstrip('_').lstrip('_')
        disorder = np.float(dis_string)

        return markers[0].join(substrings), disorder


def extract_single_model(topdir, descriptor, syspar, modpar):
    """
        A function for extracting the location of a file containing
        the numerical results for a single/unique set of data
        parameters

        The entries topdir, descriptor, syspar and modpar are strings
        from which the full path to the requested file is constructed.

    """
    filepath = os.path.join(topdir, descriptor, syspar, modpar)
    if os.path.isdir(filepath):

        try:

            file = glob('{}/*.hdf5'.format(filepath))[0]

        except IndexError:
            print('file in folder {} not present!'.format(filepath))

    else:

        print('folder {} does not exist!'.format(filepath))

        file = None

    return file


def delete_keys_from_dict(dictionary, keys):
    for key in keys:
        with suppress(KeyError):
            del dictionary[key]
    for value in dictionary.values():
        if isinstance(value, MutableMapping):
            delete_keys_from_dict(value, keys)
