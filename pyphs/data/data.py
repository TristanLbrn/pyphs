# -*- coding: utf-8 -*-
"""
Created on Thu Jun  9 10:22:56 2016

@author: Falaize
"""
from pyphs.misc.io import data_generator, write_data
import os


class Data:
    """
    container for simulation data
    """
    def __init__(self, phs):

        self.phs = phs

        def dummy_func(name):
            def get_seq(ind=None, postprocess=None, imin=None, imax=None,
                        decim=None):
                return self.data_generator(name, ind=ind, imin=imin,
                                           imax=imax, decim=decim,
                                           postprocess=postprocess)
            return get_seq

        for name in list(phs.symbs._args_names) + ['y', 'dxH', 'z', 'dx']:
            setattr(self, name, dummy_func(name))

    def t(self, imin=None, imax=None, decim=None):
        options = self.phs.simu.config['load_options']
        if imin is None:
            imin = options['imin']
        if imax is None:
            imax = options['imax']
            if imax is None:
                imax = float('Inf')
        if decim is None:
            decim = options['decim']

        def generator():
            for n in range(self.phs.simu.config['nt']):
                yield n/self.phs.simu.config['fs']
        i = 0
        for el in generator():
            if i >= imin and i < imax:
                if not bool(i % decim):
                    yield el
            i += 1

    def dtE(self, imin=None, imax=None, decim=None):
        """
        Energy variation
        """
        options = self.phs.simu.config['load_options']
        options = {'imin': options['imin'] if imin is None else imin,
                   'imax': options['imax'] if imax is None else imax,
                   'decim': options['decim'] if decim is None else decim}

        def dxtodtx(dx):
            return dx*self.phs.simu.config['fs']
        for dtx, dxh in zip(self.dx(postprocess=dxtodtx, **options),
                            self.dxH(**options)):
            yield scalar_product(dtx, dxh)

    def pd(self, imin=None, imax=None, decim=None):
        """
        Dissipated power
        """
        options = self.phs.simu.config['load_options']
        options = {'imin': options['imin'] if imin is None else imin,
                   'imax': options['imax'] if imax is None else imax,
                   'decim': options['decim'] if decim is None else decim}
        for w, z in zip(self.w(**options), self.z(**options)):
            yield scalar_product(w, z)

    def ps(self, imin=None, imax=None, decim=None):
        """
        Source power
        """
        options = self.phs.simu.config['load_options']
        options = {'imin': options['imin'] if imin is None else imin,
                   'imax': options['imax'] if imax is None else imax,
                   'decim': options['decim'] if decim is None else decim}
        for u, y in zip(self.u(**options),
                        self.y(postprocess=lambda el: -el, **options)):
            yield scalar_product(u, y)

    def data_generator(self, name, ind=None, postprocess=None,
                       imin=None, imax=None, decim=None):
        opts = self.phs.simu.config['load_options']
        options = {'imin': opts['imin'] if imin is None else imin,
                   'imax': opts['imax'] if imax is None else imax,
                   'decim': opts['decim'] if decim is None else decim}

        path = self.phs.paths['data']
        filename = path + os.sep + name.lower() + '.txt'
        generator = data_generator(filename, ind=ind, postprocess=postprocess,
                                   **options)
        return generator

    def init_data(self, sequ, seqp, x0, nt):
        # get number of time-steps
        if hasattr(sequ, 'index'):
            nt = len(sequ)
        elif hasattr(sequ, 'index'):
            nt = len(seqp)
        else:
            assert nt is not None, 'Unknown number of \
    iterations. Please tell either sequ (input sequence), seqp \
    (sequence of parameters) or nt (number of time steps).'
            assert isinstance(nt, int), 'number of time steps is not integer, \
    got {0!s} '.format(nt)

        # if sequ is not provided, a sequence of [[0]*ny]*nt is assumed
        if sequ is None:
            def generator_u():
                for _ in range(nt):
                    if self.phs.dims.y() > 0:
                        yield [0, ]*self.phs.dims.y()
                    else:
                        yield ""
            sequ = generator_u()
        # if seqp is not provided, a sequence of [[0]*np]*nt is assumed
        if seqp is None:
            def generator_p():
                for _ in range(nt):
                    if self.phs.dims.p() > 0:
                        yield [0, ]*self.phs.dims.p()
                    else:
                        yield ""
            seqp = generator_p()

        if x0 is None:
            x0 = [0, ]*self.phs.dims.x()
        else:
            assert isinstance(x0, list) and \
                len(x0) == self.phs.dims.x() and \
                isinstance(x0[0], (float, int)), 'x0 not understood, got \
    {0!s}'.format(x0)
        # write input sequence
        write_data(self.phs, sequ, 'u')
        # write parameters sequence
        write_data(self.phs, seqp, 'p')
        # write initial state
        write_data(self.phs, [x0, ], 'x0')

        self.phs.simu.config['nt'] = nt


def scalar_product(list1, list2):
    return sum(el1*el2 for (el1, el2) in zip(list1, list2))