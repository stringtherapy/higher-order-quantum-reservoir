#!/usr/bin/env python
"""
Emulate Lorentz attractor on HQRC

"""

import sys
import numpy as np
import os
import argparse
import multiprocessing
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d
from matplotlib import ticker
import time
import hqrc as hqrc
import utils as utils
import gendata as gdata
import pickle
from loginit import get_module_logger

LORENTZ_LYAPUNOV = 0.9056

def chaos_job(dataset, args, strength, noise_level):
    nqrc, type_input, combine_input, type_op = args.nqrc, args.type_input, args.combine_input, args.type_op
    nonlinear, sigma_input = args.nonlinear, args.sigma_input
    n_units, max_energy, reg = args.units, args.coupling, args.reg
    tau, V, rseed = args.tau, args.virtuals, args.rseed
    init_rho, solver, load_result = args.rho, args.solver, args.load_result
    Ntrials = args.Ntrials
    non_diag_const, non_diag_var = args.non_diag_const, args.non_diag_var
    T_buf, T_train, T_val, dt = args.T_buf, args.T_train, args.T_val, args.dt

    dynamic, savedir, datname = args.dynamic, args.savedir, args.datname
    os.makedirs(savedir, exist_ok=True)
    save_fig = os.path.join(savedir, 'figs')
    os.makedirs(save_fig, exist_ok=True)
    logdir = os.path.join(savedir, 'log')
    os.makedirs(logdir, exist_ok=True)
    datdir = os.path.join(savedir, 'data')
    os.makedirs(datdir, exist_ok=True)
    resdir = os.path.join(savedir, 'results')
    os.makedirs(resdir, exist_ok=True)

    # Evaluation
    basename = '{}_{}_var_{}_{}_units_{}_V_{}_QRs_{}_trials_{}_tau_{}_alpha_{:.3f}_cb_{}_op_{}_tp_{}_nl_{}_sig_{}_noise_{:.3f}_dt_{}_T_{}_{}_{}_seed_{}'.format(\
        datname, dynamic, non_diag_var, solver, n_units, V, nqrc, Ntrials, \
        tau, strength, combine_input, type_op, type_input, nonlinear, sigma_input, \
        noise_level, dt, T_buf, T_train, T_val, rseed)
    
    log_filename = os.path.join(logdir, '{}.log'.format(basename))
    logger = get_module_logger(__name__, log_filename)
    logger.info(log_filename)
    logger.info(args)

    buffer = int(T_buf / dt)
    train_len = int(T_train / dt)
    val_len  = int(T_val / dt)
    length = buffer + train_len + val_len

    data = dataset['u'][:(length)]
    target_seq = data[(buffer+1):length]
    
    train_input_seq = np.array(data[: buffer + train_len]).T
    ndup = int(nqrc/train_input_seq.shape[0])
    train_input_seq = np.tile(train_input_seq, (ndup, 1))
    train_input_seq = utils.add_noise(train_input_seq, noise_level)

    vmin, vmax = np.min(train_input_seq), np.max(train_input_seq)
    train_input_seq = utils.min_max_norm(train_input_seq, vmin, vmax)
    
    train_output_seq = utils.min_max_norm(np.array(data[1 : buffer + train_len + 1]), vmin, vmax)
    #val_output_seq = np.array(data[(buffer + train_len + 1):])
    qparams = utils.QRCParams(n_units=n_units-1, n_envs=1, max_energy=max_energy, non_diag_var=non_diag_var, non_diag_const=non_diag_const,\
        beta=reg, virtual_nodes=V, tau=tau, init_rho=init_rho, solver=solver, dynamic=dynamic)
    
    for ntrial in range(Ntrials):
        res_path = os.path.join(resdir, 'rs_{}_{}.pickle'.format(ntrial, basename))
        ranseed = rseed + (ntrial+1)*100
        if load_result == 0:
            train_pred_seq, val_pred_seq = hqrc.closed_loop(qparams, buffer, train_input_seq, train_output_seq, val_len, ranseed=ranseed, nqrc=nqrc,\
                gamma=strength, sigma_input=sigma_input, type_input=type_input, type_op=type_op, \
                combine_input=combine_input, nonlinear=nonlinear)
            
            pred_seq = np.concatenate([train_pred_seq, val_pred_seq])
            # descaling data
            pred_seq = vmin + pred_seq * (vmax - vmin)
            # Compute NRMSE
            pred_seq = pred_seq[buffer:(length-1)]
            nrmse = np.array(utils.cal_NRMSE(pred_seq, target_seq))
            
            nrmse_file = log_filename.replace('.log', '_nrmse_{}.txt'.format(ntrial))
            np.savetxt(nrmse_file, nrmse)
            #np.save(pred_file, pred_seq)

            train_loss, val_loss = np.mean(nrmse[:train_len]), np.mean(nrmse[train_len:])
            num_accurate_pred_005 = utils.get_num_accurate_pred(nrmse[train_len:], thresh=0.005)
            num_accurate_pred_05  = utils.get_num_accurate_pred(nrmse[train_len:], thresh=0.05)
            pred_time_005 = num_accurate_pred_005 * LORENTZ_LYAPUNOV * dt
            pred_time_05  = num_accurate_pred_05  * LORENTZ_LYAPUNOV * dt

            logger.info('ntrial={}, loss val={}, train={}, pred_time_005={}, pred_time_05={}'.format(\
                ntrial, val_loss, train_loss, pred_time_005, pred_time_05))
            logger.debug('ntrial={}, shape train_pred={}, val_pred={}, pred_seq={}'.format(\
                ntrial, train_pred_seq.shape, val_pred_seq.shape, pred_seq.shape))
            
            # Save results
            if ntrial == 0:
                results = {
                    'args': args,
                    'qparams': qparams,
                    'vmin': vmin,
                    'vmax': vmax,
                    'prediction': pred_seq,
                    'nrmse': nrmse,
                    'train_loss': train_loss,
                    'val_loss': val_loss,
                    'ntrial': ntrial,
                    'lyapunov': LORENTZ_LYAPUNOV,
                    'num_accurate_pred_005': num_accurate_pred_005,
                    'num_accurate_pred_05': num_accurate_pred_05,
                    'pred_time_005': pred_time_005,
                    'pred_time_05': pred_time_05
                }
                with open(res_path, "wb") as wfile:
                    pickle.dump(results, wfile, pickle.HIGHEST_PROTOCOL)
                    logger.info('Dumped results to {}'.format(res_path))
                    del results
        else:
            with open(res_path, "rb") as rfile:
                results = pickle.load(rfile)
                logger.info('Loaded results from {}'.format(res_path))
                nrmse = results['nrmse']
                pred_seq = results['prediction']
                train_loss = results['train_loss']
                val_loss = results['val_loss']
                vmin, vmax = results['vmin'], results['vmax']

        if ntrial == 0:
            n_title = 'ntrial={}, loss val={:.6f}, train={:.6f}'.format(ntrial, val_loss, train_loss)
            outbase = os.path.join(save_fig, '{}_test_{}'.format(basename, ntrial))
            utils.plot_lorentz(target_seq, pred_seq, nrmse, buffer, train_len, val_len, outbase, n_title, ftypes=['png'])
            logger.info('Output to file {}'.format(outbase))

if __name__  == '__main__':
    # Check for command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--units', type=int, default=5, help='Number of the hidden units')
    parser.add_argument('--coupling', type=float, default=1.0, help='Maximum coupling energy')
    parser.add_argument('--rho', type=int, default=0, help='Flag for initializing the density matrix')
    parser.add_argument('--reg', type=float, default=1e-14, help='reg term')
    parser.add_argument('--solver', type=str, default=utils.LINEAR_PINV, \
        help='regression solver by linear_pinv,ridge_pinv,auto,svd,cholesky,lsqr,sparse_cg,sag')
    parser.add_argument('--dynamic', type=str, default=utils.DYNAMIC_FULL_RANDOM,\
        help='full_random,half_random,full_const_trans,full_const_coeff,ion_trap')
    parser.add_argument('--non_diag_var', type=float, default=2.0, help='non_diag_var for phase_trans dynamic')
    parser.add_argument('--non_diag_const', type=float, default=2.0, help='non_diag_const for phase_trans dynamic')

    parser.add_argument('--datname', type=str, default='lorentz')
    parser.add_argument('--dt', type=float, default=0.01)
    parser.add_argument('--T_buf', type=int, default=20)
    parser.add_argument('--T_train', type=int, default=20)
    parser.add_argument('--T_val', type=int, default=10)
    
    parser.add_argument('--Ntrials', type=int, default=1)
    parser.add_argument('--virtuals', type=int, default=1)

    parser.add_argument('--tau', type=float, default=10.0, help='Interval between the inputs')
    parser.add_argument('--strengths', type=str, default='0.0', help='Connection strengths')
    parser.add_argument('--nqrc', type=int, default=3, help='Number of reservoirs')

    parser.add_argument('--savedir', type=str, default='../results/test_lorentz')
    parser.add_argument('--rseed', type=int, default=0)
    parser.add_argument('--combine_input', type=int, default=1)
    parser.add_argument('--type_input', type=int, default=0)
    parser.add_argument('--type_op', type=str, default='Z')
    
    parser.add_argument('--sigma_input', type=float, default=1.0)
    parser.add_argument('--nonlinear', type=int, default=0)
    parser.add_argument('--noise_level', type=float, default=0.1)

    parser.add_argument('--load_result', type=int, default=0)

    args = parser.parse_args()
    T_buf, T_train, T_val, dt = args.T_buf, args.T_train, args.T_val, args.dt
    savedir, datname = args.savedir, args.datname
    strengths = [float(x) for x in args.strengths.split(',')]

    os.makedirs(savedir, exist_ok=True)
    save_fig = os.path.join(savedir, 'figs')
    os.makedirs(save_fig, exist_ok=True)
    logdir = os.path.join(savedir, 'log')
    os.makedirs(logdir, exist_ok=True)
    datdir = os.path.join(savedir, 'data')
    os.makedirs(datdir, exist_ok=True)
    resdir = os.path.join(savedir, 'results')
    os.makedirs(resdir, exist_ok=True)
    
    if datname == 'lorentz':
        data_path = os.path.join(datdir, '{}_dt_{}_{}_{}_{}.pickle'.format(datname, dt, T_buf, T_train, T_val))
        if os.path.isfile(data_path) == True:
            with open(data_path, "rb") as dfile:
                dataset = pickle.load(dfile)
                print('Loaded data from {}'.format(data_path))
        else:
            dataset = gdata.Lorenz3D(T1 = 0, T2 = T_val + T_train + T_buf, dt = dt)
            with open(data_path, "wb") as dfile:
                pickle.dump(dataset, dfile, pickle.HIGHEST_PROTOCOL)
                print('Dumped data to {}'.format(data_path))
        print('Data set shape {}'.format(dataset['u'].shape))
    else:
        print('Data {} not found. Exited!'.format(datname))
        exit(1)
    
    jobs, pipels = [], []
    for strength in strengths:
        for noise_level in [0.0, 0.01, 0.05, 0.1]:
            p = multiprocessing.Process(target=chaos_job, args=(dataset, args, strength, noise_level))
            jobs.append(p)
    
    # Start the process
    for p in jobs:
        p.start()

    # Ensure all processes have finished execution
    for p in jobs:
        p.join()

    # Sleep 5s
    time.sleep(5)


    