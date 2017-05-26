#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 14 11:50:23 2017

@author: Falaize
"""

from __future__ import absolute_import, division, print_function

import os
import numpy
import matplotlib.pyplot as plt
from pyphs import PHSSimulation, PHSNetlist, PHSGraph
from pyphs.misc.signals.waves import wavwrite


# ---------------------------  NETLIST  ------------------------------------- #
label = 'rhodes'
this_script = os.path.realpath(__file__)
here = this_script[:this_script.rfind(os.sep)]
netlist_filename = here + os.sep + label + '.net'
netlist = PHSNetlist(netlist_filename)

# ---------------------------  GRAPH  --------------------------------------- #
graph = PHSGraph(netlist=netlist)

# ---------------------------  CORE  ---------------------------------------- #
core = graph.buildCore()

# ---------------------------  SIMULATION  ---------------------------------- #
if __name__ == '__main__':

    core.build_R()

    # Define the simulation parameters
    config = {'fs': 48e3,           # Sample rate (Hz)
              'grad': 'discret',    # In {'discret', 'theta', 'trapez'}
              'theta': 0.,          # Theta-scheme for the structure
              'split': True,       # split implicit from explicit part
              'maxit': 10,          # Max number of iterations for NL solvers
              'eps': 1e-16,         # Global numerical tolerance
              'path': None,         # Path to the results folder
              'pbar': True,         # Display a progress bar
              'timer': False,       # Display minimal timing infos
              'lang': 'c++',        # Language in {'python', 'c++'}
              # Options for the data reader. The data are read from index imin
              # to index imax, rendering one element out of the number decim
              'load': {'imin': None,
                       'imax': None,
                       'decim': None}
              }

    # Instanciate PHSSimulation class
    simu = PHSSimulation(core, config=config)

    def ordering(name, *args):
        def get_index(e):
            symb = simu.nums.method.symbols(e)
            return getattr(simu.nums.method, name).index(symb)
        return list(map(get_index, args))

    order = ordering('y', 'yout', 'ypickupMagnet')

    # def simulation time
    tmax = 5
    nmax = int(tmax*simu.config['fs'])
    t = [n/simu.config['fs'] for n in range(nmax)]
    nt = len(t)
    vin_max = 100  # [m/s] Maximal initial velocity of the hammer
    sig = list()
    for vin in numpy.linspace(0, vin_max, 6)[1:]:
        t0 = 1e-2  # [s] time between init of velocity and impact
        qh0 = -vin*t0  # [m] Hammer's initial position w.r.t the beam at rest
        # def generator for sequence of inputs to feed in the PHSSimulation object
        def sequ():
            """
            generator of input sequence for PHSSimulation
            """
            for tn in t:
                # numpy.array([u1, u2, ...])
                yield numpy.array([[0., 1.][i] for i in order])

        # state initialization
        # !!! must be array with shape (core.dims.x(), )
        x0 = numpy.array([0., ]*core.dims.x())
        core_simu = simu.nums.method
        x0[core_simu.x.index(core.symbols('qfelt'))] = qh0
        x0[core_simu.x.index(core.symbols('xmass'))] = vin

        # Initialize the simulation
        simu.init(u=sequ(), x0=x0, nt=nt)

        # Proceed
        simu.process()

        wave_path = os.path.join(here, 'ypickup_{}={}'.format('vin', str(vin)))
        simu.data.wavwrite('y', order[1], path=wave_path)

        sig += list(simu.data.y(order[1], decim=1))
        simu.data.plot([('x', 0), ('dtx', 0), ('y', 1)], load={'imin':100, 'imax':1000})

        pass

    wavwrite(sig, simu.config['fs'], 'ypickup', normalize=True)
