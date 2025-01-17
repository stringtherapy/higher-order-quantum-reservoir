import sys
import numpy as np
import os
import scipy
import argparse
import multiprocessing
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import ticker
import time
import datetime
import hqrc as hqrc
import utils
from utils import *
from loginit import get_module_logger

# virtuals = [5*n for n in range(1, 6)]
# virtuals.insert(0, 1)

# layers = [n for n in range(1, 6)]
# strengths = [0.0 0.1 0.3 0.5 0.7 0.9 1.0]

INTERVAL=0.1

def effdim_job(qparams, nqrc, layer_strength, sparsity, nonlinear, sigma_input, mask_input, buffer, length, Ntrials, send_end):
    print('Start process layer={}, taudelta={}, virtual={}, sparsity={}'.format(nqrc, qparams.tau, qparams.virtual_nodes, sparsity))
    btime = int(time.time() * 1000.0)
    effd_ls = []
    for n in range(Ntrials):
        effd, _ = hqrc.effective_dim(qparams, buffer=buffer, length=length, nqrc=nqrc, \
            gamma=layer_strength, sparsity=sparsity, sigma_input=sigma_input, mask_input=mask_input, \
            nonlinear=nonlinear, ranseed=n, Ntrials=1)
        effd_ls.append(effd)

    mean_effd, std_effd = np.mean(effd_ls), np.std(effd_ls)
    rstr = '{} {} {} {} {}'.format(\
        nqrc, qparams.tau, layer_strength, mean_effd, std_effd)
    etime = int(time.time() * 1000.0)
    now = datetime.datetime.now()
    datestr = now.strftime('{0:%Y-%m-%d-%H-%M-%S}'.format(now))
    print('{} Finish process {} in {}s'.format(datestr, rstr, etime-btime))
    send_end.send(rstr)

if __name__  == '__main__':
    # Check for command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--units', type=int, default=5)
    parser.add_argument('--coupling', type=float, default=1.0)
    parser.add_argument('--trotter', type=int, default=10)
    parser.add_argument('--rho', type=int, default=0)
    parser.add_argument('--beta', type=float, default=1e-14)

    parser.add_argument('--length', type=int, default=10000)
    parser.add_argument('--buffer', type=int, default=9000)
    parser.add_argument('--sparsity', type=float, default=1.0, help='The sparsity of the connection strength')
    
    parser.add_argument('--nproc', type=int, default=50)
    parser.add_argument('--ntrials', type=int, default=1)
    parser.add_argument('--taudeltas', type=str, default='-4,-3,-2,-1,0,1,2,3,4,5,6,7')
    parser.add_argument('--layers', type=str, default='5')
    parser.add_argument('--strength', type=float, default=0.0)
    parser.add_argument('--virtuals', type=int, default=1)
    parser.add_argument('--nonlinear', type=int, default=0)
    parser.add_argument('--mask_input', type=int, default=0)
    parser.add_argument('--sigma_input', type=float, default=1.0)
    
    parser.add_argument('--plot', type=int, default=0)
    parser.add_argument('--interval', type=float, default=INTERVAL, help='tau-interval')
    parser.add_argument('--dynamic', type=str, default=DYNAMIC_FULL_RANDOM)
    parser.add_argument('--savedir', type=str, default='res_high_eff_tau')
    args = parser.parse_args()
    print(args)

    n_units, max_energy, trotter_step, beta =\
        args.units, args.coupling, args.trotter, args.beta
    length, buffer, sparsity = args.length, args.buffer, args.sparsity
    nproc, layer_strength, V = args.nproc, args.strength, args.virtuals
    nonlinear, sigma_input, mask_input = args.nonlinear, args.sigma_input, args.mask_input
    init_rho = args.rho
    Ntrials = args.ntrials

    dynamic, savedir = args.dynamic, args.savedir
    if os.path.isfile(savedir) == False and os.path.isdir(savedir) == False:
        os.mkdir(savedir)

    #taudeltas = [float(x) for x in args.taudeltas.split(',')]
    taudeltas = list(np.arange(-7, 7.1, args.interval))
    taudeltas = [2**x for x in taudeltas]
    nproc = min(len(taudeltas), nproc)
    lst = np.array_split(taudeltas, nproc)

    layers = [int(x) for x in args.layers.split(',')]
    
    # Evaluation
    timestamp = int(time.time() * 1000.0)
    now = datetime.datetime.now()
    datestr = now.strftime('{0:%Y-%m-%d-%H-%M-%S}'.format(now))
    outbase = os.path.join(savedir, '{}_{}_strength_{:.2f}_sparsity_{}_V_{}_layers_{}_nonlinear_{}_sm_{}_mask_{}_ntrials_{}'.format(\
        dynamic, datestr, layer_strength, sparsity, V, '_'.join([str(o) for o in layers]), nonlinear, sigma_input, mask_input, Ntrials))
    outfile = '{}_eff.txt'.format(outbase)
    if os.path.isfile(outfile) == True:
        print('File existed {}'.format(outfile))
        exit(1)
    if os.path.isfile(savedir) == False:
        jobs, pipels = [], []
        for nqrc in layers:
            for tau in taudeltas:
                recv_end, send_end = multiprocessing.Pipe(False)
                qparams = QRCParams(n_units=n_units-1, n_envs=1, max_energy=max_energy,\
                    beta=beta, virtual_nodes=V, tau=tau, init_rho=init_rho, dynamic=dynamic, solver=LINEAR_PINV)
                p = multiprocessing.Process(target=effdim_job, args=(qparams, nqrc, layer_strength, sparsity, nonlinear, sigma_input, mask_input, buffer, length, Ntrials, send_end))
                jobs.append(p)
                pipels.append(recv_end)

        # Start the process
        for p in jobs:
            p.start()

        # Ensure all processes have finished execution
        for p in jobs:
            p.join()

        # Sleep 5s
        time.sleep(5)

        result_list = [np.array( [float(y) for y in x.recv().split(' ')]  ) for x in pipels]
        rsarr = np.array(result_list)
        # save the result
        np.savetxt(outfile, rsarr, delimiter=' ')

        # save experiments setting
        with open('{}_setting.txt'.format(outbase), 'w') as sfile:
            sfile.write('length={}, buffer={}\n'.format(length, buffer))
            sfile.write('n_units={}\n'.format(n_units))
            sfile.write('max_energy={}\n'.format(max_energy))
            sfile.write('sparsity={}, nonlinear={}, sigma_input={}, mask_input={}\n'.format(sparsity, nonlinear, sigma_input, mask_input))
            sfile.write('beta={}\n'.format(beta))
            sfile.write('taudeltas={}\n'.format(' '.join([str(v) for v in taudeltas])))
            sfile.write('layers={}\n'.format(' '.join([str(l) for l in layers])))
            sfile.write('V={}\n'.format(V))
            sfile.write('layer_strength={}, Ntrials={}\n'.format(layer_strength, Ntrials))

    else:
        # Read the result
        rsarr = np.loadtxt(savedir)
        outbase = savedir.replace('.txt', '')

    print(rsarr)
    print(rsarr.shape)

    if args.plot > 0:
        # plot the result
        xs = taudeltas
        avg_effs, std_effs = rsarr[:, 3], rsarr[:, 4]

        cmap = plt.get_cmap("viridis")
        plt.figure(figsize=(16,8))
        #plt.style.use('seaborn-colorblind')
        plt.rc('font', family='serif')
        plt.rc('mathtext', fontset='cm')
        plt.rcParams['font.size']=20

        for nqrc in layers:
            ids = (rsarr[:, 0] == nqrc)
            if len(ids) > 0:
                plt.plot(xs, avg_effs[ids], 'o--', linewidth=2, markersize=12, \
                    label='nqr={}'.format(nqrc))
                #plt.errorbar(xs, avg_effs[ids], yerr=std_effs[ids], elinewidth=2, linewidth=2, markersize=12, \
                #    label='nqr={}'.format(nqrc))
        #plt.xlim([1e-3, 1024])    
        #plt.ylim([1.0, 1.4])
        plt.xlabel('$\\tau\Delta$', fontsize=28)
        plt.ylabel('Eff. Dim', fontsize=28)
        plt.xscale('log', basex=2)
        plt.xticks([2**x for x in list(np.arange(-4, 4.1, 1.0))])
        

        plt.legend()
        plt.title(outbase, fontsize=12)
        plt.grid(True, which="both", ls="-", color='0.65')
        #plt.show()
        for ftype in ['png']:
            plt.savefig('{}_eff.{}'.format(outbase, ftype), bbox_inches='tight')
 
