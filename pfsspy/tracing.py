import abc

import astropy.constants as const
import numpy as np
import sunpy.coordinates.frames as frames

import pfsspy


class Tracer(abc.ABC):
    """
    Abstract base class for a streamline tracer.
    """
    @abc.abstractmethod
    def trace(self, seeds, output):
        """
        Parameters
        ----------
        seeds : (n, 3) array
            Coordinaes of the magnetic field seed points.
        output : pfsspy.Output
            pfss output.

        Returns
        -------
        streamlines : list of FieldLine
            List of traced streamlines
        """
        pass

    @staticmethod
    def validate_seeds_shape(seeds):
        """
        Check that *seeds* has the right shape.
        """
        if not seeds.ndim == 2:
            raise ValueError(f'seeds must be a 2D array (got shape {seeds.shape})')
        if not seeds.shape[1] == 3:
            raise ValueError(f'seeds must be a (n, 3) shaped array (got shape {seeds.shape})')

    @staticmethod
    def cartesian_to_coordinate():
        """
        Convert cartesian coordinate outputted by a tracer to a `FieldLine`
        object.
        """


class PythonTracer(Tracer):
    """
    Tracer using native python code.

    Uses `scipy.integrate.solve_ivp`, with an LSODA method.
    """
    def __init__(self, atol=1e-4, rtol=1e-4):
        """
        dtf : float, optional
            Absolute tolerance of the tracing.
        rtol : float, optional
            Relative tolerance of the tracing.
        """
        self.atol = atol
        self.rtol = rtol

    def trace(self, seeds, output):
        seeds = np.atleast_2d(seeds)
        self.validate_seeds_shape(seeds)
        flines = []
        for seed in seeds:
            xforw = output._integrate_one_way(1, seed, self.rtol, self.atol)
            xback = output._integrate_one_way(-1, seed, self.rtol, self.atol)
            xback = np.flip(xback, axis=1)
            xout = np.row_stack((xback.T, xforw.T))
            fline = pfsspy.FieldLine(x=xout[:, 0] * const.R_sun,
                                     y=xout[:, 1] * const.R_sun,
                                     z=xout[:, 2] * const.R_sun,
                                     frame=frames.HeliographicCarrington,
                                     obstime=output.dtime,
                                     representation_type='cartesian')
            fline._output = output
            fline._expansion_factor = None
            flines.append(fline)
        return flines

