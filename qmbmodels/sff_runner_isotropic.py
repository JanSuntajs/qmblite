import numpy as np
from scipy.special import comb

from senderscripts.batchsend import BatchSender
from utils.cmd_parser_tools import mode_parser
from models.prepare_model import import_model

wlist = np.unique(np.append(np.arange(0.25, 10., 0.25),
                            np.arange(0.1, 10., 0.2)))
# wlist = [1.1, 2.9, 3.3, 3.5, 3.7, 3.9, 4.1, 4.3, 4.5, 4.7, 4.9, 6.0, 7.0, 8.0]
#wlist = [4.1, 7.0]
if __name__ == '__main__':
    storage = '/scratch/jan/MBLexact_py/'
    ham_type = 'spin1d'
    model = 'heisenberg'
    mod = import_model(model)
    params = {
        'L': [18],
        'J1': [2.0],
        'J2': [0.0],
        'W': [0.],
        'dW': ['{:.2f}'.format(w) for w in wlist],
        'delta1': [1.0],
        'delta2': [0.0],
        'pbc': [True],
        'ham_type': [ham_type],
        'disorder': ['uniform'],
        'min_seed': [1],
        'max_seed': [400],
        'step_seed': [20],
        'sff_min_tau': [0],
        'sff_max_tau': [np.log10(5 * 2 * np.pi)],
        'sff_n_tau': [5000],
        'sff_eta': [0.5],  # [0.1, 0.2,0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.],
        'sff_unfolding_n': [3],
        'sff_filter': ['gaussian'],
        'r_step': [0.05],
    }
    params['nu'] = [int(val * 0.5) for val in params['L']]
    params['sff_min_tau'] = [np.log10(1 / comb(val, 0.5 * val))
                             for val in params['L']]

    # shift and invert parameters
    sinvert_params = ['--model={}'.format(model),
                      '-eps_type krylovschur', '-eps_nev 100',
                      '-st_type sinvert',
                      '-st_ksp_type preonly',
                      '-st_pc_factor_mat_solver_type mumps',
                      '-st_pc_type lu',
                      '-mat_mumps_icntl_28 2',
                      '-mat_mumps_icntl_29 2']

    syspar_keys = mod.syspar_keys
    modpar_keys = mod.modpar_keys
    auxpar_keys = ['sff_min_tau', 'sff_max_tau', 'sff_n_tau', 'sff_eta',
                   'sff_unfolding_n', 'sff_filter', 'r_step']

    name = 'to_py_from_fortran_new'
    time = "23:59:59"
    nodes = 1   # number of nodes
    ntasks = 1  # number of threads
    memcpu = 4  # memory in GB per CPU!
    cputask = 4
    slurm_opt = ['#SBATCH --partition=test',
                 '#SBATCH --distribution=cyclic:cyclic',
                 '#SBATCH --threads-per-core=2',
                 '\nexport MKL_DEBUG_CPU_TYPE=5\n', ]
    # f'#SBATCH -B 1:{int(cputask/2.)}:2',]
    slurm_opt = []
    queue, mode = mode_parser()

    print(f"{mode}")
    # args = arg_parser(syspar_keys, modpar_keys)

    sender = BatchSender(params, syspar_keys, modpar_keys,
                         auxpar_keys, cmd_opt=sinvert_params,
                         storage=storage, slurm_opt=slurm_opt)

    sender.run_jobs(mode, queue=queue, time=time, nodes=nodes, ntasks=ntasks,
                    memcpu=memcpu, name=name, sourcename='petscenv',
                    cputask=cputask)
