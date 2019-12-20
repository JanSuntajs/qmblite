#!/usr/bin/env python


from utils import set_mkl_lib
from utils.cmd_parser_tools import arg_parser
from models.prepare_model import get_module_info
from utils.filesaver import savefile
from models.prepare_model import select_model

save_metadata = True

if __name__ == '__main__':

    (mod, model_name, argsDict, seedDict, syspar_keys,
     modpar_keys, savepath, syspar, modpar, *rest) = get_module_info()

    print('Using seed: {}'.format(argsDict['seed']))

    # get the instance of the appropriate hamiltonian
    # class and the diagonal random fields used
    model, fields = mod.construct_hamiltonian(argsDict)

    print('Starting diagonalization ...')
    eigvals = model.eigvals(complex=False)
    # eigvals, eigvecs = model.eigsystem(complex=False, turbo=True)
    print('Diagonalization finished!')

    print('Displaying eigvals')
    print(eigvals)

    # ----------------------------------------------------------------------
    # save the files
    eigvals_dict = {'Eigenvalues': eigvals,
                    **fields}
    savefile(eigvals_dict, savepath, syspar, modpar, argsDict,
             syspar_keys, modpar_keys, 'full', save_metadata, save_type='npz')
