"""StressPost class for post-processing FE stress results."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import matplotlib.axes
import matplotlib.cm as cm
import matplotlib.tri as tri
import numpy as np
from matplotlib.colors import CenteredNorm
from matplotlib.patches import Circle
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable

import sectionproperties.post.post as post


if TYPE_CHECKING:
    from sectionproperties.analysis.section import MaterialGroup, Section


class StressPost:
    """Class for post-processing finite element stress results.

    A StressPost object is created when a stress analysis is carried out and is returned
    as an object to allow post-processing of the results. The StressPost object creates
    a ``deepcopy`` of the :class:`~sectionproperties.analysis.section.MaterialGroup` s
    within the cross-section to allow the calculation of stresses for each material.
    Methods for post-processing the calculated stresses are provided.

    Attributes:
        section (Section): Cross-section object for stress calculation
        material_groups (MaterialGroup): A deep copy of the
            :class:`~sectionproperties.analysis.section.Section` ``material_groups``
    """

    def __init__(
        self,
        section: Section,
    ) -> None:
        """Inits the StressPost class.

        Args:
            section (Section): Cross-section object for stress calculation
        """
        self.section = section

        # make a deep copy of the material groups to the StressPost object such that
        # stress results can be saved to a new material group when a new stress analysis
        # is performed
        self.material_groups: list[MaterialGroup] = deepcopy(section.material_groups)

    def plot_stress(
        self,
        stress: str,
        title: str | None = None,
        cmap: str = "coolwarm",
        normalize: bool = True,
        **kwargs,
    ) -> matplotlib.axes.Axes:
        r"""Plots filled stress contours over the finite element mesh.

        Args:
            stress: Type of stress to plot, see below for allowable values
            title: Plot title, if None uses default plot title for selected stress
            cmap: Matplotlib color map, see
                https://matplotlib.org/stable/tutorials/colors/colormaps.html for more
                detail
            normalize: If set to True, ``CenteredNorm`` is used to scale the colormap,
                if set to False, the default linear scaling is used
            kwargs: Passed to :func:`~sectionproperties.post.post.plotting_context`

        Raises:
            RuntimeError: If the plot failed to be generated

        Returns:
            Matplotlib axes object

        .. admonition:: Stress contour plotting options

          In general the stresses are described by an action followed by a stress
          direction  ``(action)_(stress-direction)``, e.g. ``mzz_zx`` represents the
          shear stress in the ``zx`` direction caused by the torsion ``mzz``.

          Below is a list of the acceptable values for ``stress``:

          - ``stress="n_zz"`` - normal stress :math:`\sigma_{zz,N}` resulting from the
            axial load :math:`N`

          - ``stress="mxx_zz"`` - normal stress :math:`\sigma_{zz,Mxx}` resulting from
            the bending moment :math:`M_{xx}`

          - ``stress="myy_zz"`` - normal stress :math:`\sigma_{zz,Myy}` resulting from
            the bending moment :math:`M_{yy}`

          - ``stress="m11_zz"`` - normal stress :math:`\sigma_{zz,M11}` resulting from
            the bending moment :math:`M_{11}`

          - ``stress="m22_zz"`` - normal stress :math:`\sigma_{zz,M22}` resulting from
            the bending moment :math:`M_{22}`

          - ``stress="m_zz"`` - normal stress :math:`\sigma_{zz,\Sigma M}` resulting
            from all bending moments :math:`M_{xx} + M_{yy} + M_{11} + M_{22}`

          - ``stress="mzz_zx"`` - ``x`` component of the shear stress
            :math:`\sigma_{zx,Mzz}` resulting from the torsion moment :math:`M_{zz}`

          - ``stress="mzz_zy"`` - ``y`` component of the shear stress
            :math:`\sigma_{zy,Mzz}` resulting from the torsion moment :math:`M_{zz}`

          - ``stress="mzz_zxy"`` - resultant shear stress :math:`\sigma_{zxy,Mzz}`
            resulting from the torsion moment :math:`M_{zz}`

          - ``stress="vx_zx"`` - ``x`` component of the shear stress
            :math:`\sigma_{zx,Vx}` resulting from the shear force :math:`V_{x}`

          - ``stress="vx_zy"`` - ``y`` component of the shear stress
            :math:`\sigma_{zy,Vx}` resulting from the shear force :math:`V_{x}`

          - ``stress="vx_zxy"`` - resultant shear stress :math:`\sigma_{zxy,Vx}`
            resulting from the shear force :math:`V_{x}`

          - ``stress="vy_zx"`` - ``x`` component of the shear stress
            :math:`\sigma_{zx,Vy}` resulting from the shear force :math:`V_{y}`

          - ``stress="vy_zy"`` - ``y`` component of the shear stress
            :math:`\sigma_{zy,Vy}` resulting from the shear force :math:`V_{y}`

          - ``stress="vy_zxy"`` - resultant shear stress :math:`\sigma_{zxy,Vy}`
            resulting from the shear force :math:`V_{y}`

          - ``stress="v_zx"`` - ``x`` component of the shear stress
            :math:`\sigma_{zx,\Sigma V}` resulting from the sum of the applied shear
            forces :math:`V_{x} + V_{y}`.

          - ``stress="v_zy"`` - ``y`` component of the shear stress
            :math:`\sigma_{zy,\Sigma V}` resulting from the sum of the applied shear
            forces :math:`V_{x} + V_{y}`.

          - ``stress="v_zxy"`` - resultant shear stress :math:`\sigma_{zxy,\Sigma V}`
            resulting from the sum of the applied shear forces :math:`V_{x} + V_{y}`

          - ``stress="zz"`` - combined normal stress :math:`\sigma_{zz}` resulting from
            all actions

          - ``stress="zx"`` - ``x`` component of the shear stress :math:`\sigma_{zx}`
            resulting from all actions

          - ``stress="zy"`` - ``y`` component of the shear stress :math:`\sigma_{zy}`
            resulting from all actions

          - ``stress="zxy"`` - resultant shear stress :math:`\sigma_{zxy}` resulting
            from all actions

          - ``stress="zxy"`` - resultant shear stress :math:`\sigma_{zxy}` resulting
            from all actions

          - ``stress="11"`` - major principal stress :math:`\sigma_{11}` resulting from
            all actions

          - ``stress="33"`` - minor principal stress :math:`\sigma_{33}` resulting from
            all actions

          - ``stress="vm"`` - von Mises stress :math:`\sigma_{vM}` resulting from all
            actions
        """
        # get required variables for stress plot
        stress_dict = {
            "n_zz": {
                "attribute": "sig_zz_n",
                "title": r"Stress Contour Plot - $\sigma_{zz,N}$",
            },
            "mxx_zz": {
                "attribute": "sig_zz_mxx",
                "title": r"Stress Contour Plot - $\sigma_{zz,Mxx}$",
            },
            "myy_zz": {
                "attribute": "sig_zz_myy",
                "title": r"Stress Contour Plot - $\sigma_{zz,Myy}$",
            },
            "m11_zz": {
                "attribute": "sig_zz_m11",
                "title": r"Stress Contour Plot - $\sigma_{zz,M11}$",
            },
            "m22_zz": {
                "attribute": "sig_zz_m22",
                "title": r"Stress Contour Plot - $\sigma_{zz,M22}$",
            },
            "m_zz": {
                "attribute": "sig_zz_m",
                "title": r"Stress Contour Plot - $\sigma_{zz,\Sigma M}$",
            },
            "mzz_zx": {
                "attribute": "sig_zx_mzz",
                "title": r"Stress Contour Plot - $\sigma_{zx,Mzz}$",
            },
            "mzz_zy": {
                "attribute": "sig_zy_mzz",
                "title": r"Stress Contour Plot - $\sigma_{zy,Mzz}$",
            },
            "mzz_zxy": {
                "attribute": "sig_zxy_mzz",
                "title": r"Stress Contour Plot - $\sigma_{zxy,Mzz}$",
            },
            "vx_zx": {
                "attribute": "sig_zx_vx",
                "title": r"Stress Contour Plot - $\sigma_{zx,Vx}$",
            },
            "vx_zy": {
                "attribute": "sig_zy_vx",
                "title": r"Stress Contour Plot - $\sigma_{zy,Vx}$",
            },
            "vx_zxy": {
                "attribute": "sig_zxy_vx",
                "title": r"Stress Contour Plot - $\sigma_{zxy,Vx}$",
            },
            "vy_zx": {
                "attribute": "sig_zx_vy",
                "title": r"Stress Contour Plot - $\sigma_{zx,Vy}$",
            },
            "vy_zy": {
                "attribute": "sig_zy_vy",
                "title": r"Stress Contour Plot - $\sigma_{zy,Vy}$",
            },
            "vy_zxy": {
                "attribute": "sig_zxy_vy",
                "title": r"Stress Contour Plot - $\sigma_{zxy,Vy}$",
            },
            "v_zx": {
                "attribute": "sig_zx_v",
                "title": r"Stress Contour Plot - $\sigma_{zx,\Sigma V}$",
            },
            "v_zy": {
                "attribute": "sig_zy_v",
                "title": r"Stress Contour Plot - $\sigma_{zy,\Sigma V}$",
            },
            "v_zxy": {
                "attribute": "sig_zxy_v",
                "title": r"Stress Contour Plot - $\sigma_{zxy,\Sigma V}$",
            },
            "zz": {
                "attribute": "sig_zz",
                "title": r"Stress Contour Plot - $\sigma_{zz}$",
            },
            "zx": {
                "attribute": "sig_zx",
                "title": r"Stress Contour Plot - $\sigma_{zx}$",
            },
            "zy": {
                "attribute": "sig_zy",
                "title": r"Stress Contour Plot - $\sigma_{zy}$",
            },
            "zxy": {
                "attribute": "sig_zxy",
                "title": r"Stress Contour Plot - $\sigma_{zxy}$",
            },
            "11": {
                "attribute": "sig_11",
                "title": r"Stress Contour Plot - $\sigma_{11}$",
            },
            "33": {
                "attribute": "sig_33",
                "title": r"Stress Contour Plot - $\sigma_{33}$",
            },
            "vm": {
                "attribute": "sig_vm",
                "title": r"Stress Contour Plot - $\sigma_{vM}$",
            },
        }

        # populate stresses
        sigs = []

        for group in self.material_groups:
            sigs.append(getattr(group.stress_result, stress_dict[stress]["attribute"]))

        # apply title
        if not title:
            title = stress_dict[stress]["title"]

        # create plot and setup the plot
        with post.plotting_context(title=title, **kwargs) as (fig, ax):
            # set up the colormap
            colormap = cm.get_cmap(name=cmap)

            # create triangulation
            triang = tri.Triangulation(
                self.section._mesh_nodes[:, 0],
                self.section._mesh_nodes[:, 1],
                self.section._mesh_elements[:, 0:3],
            )

            # determine minimum and maximum stress values for the contour list
            sig_min = min([min(x) for x in sigs])
            sig_max = max([max(x) for x in sigs])

            v = np.linspace(start=sig_min, stop=sig_max, num=15, endpoint=True)

            if np.isclose(v[0], v[-1], atol=1e-12):
                v = 15
                ticks = None
            else:
                ticks = v

            norm = None
            trictr = None
            if normalize:
                norm = CenteredNorm()

            # plot the filled contour, looping through the materials
            for i, sig in enumerate(sigs):
                # create and set the mask for the current material
                mask_array = np.ones(shape=len(self.section.elements), dtype=bool)
                mask_array[self.material_groups[i].el_ids] = False
                triang.set_mask(mask_array)

                # plot the filled contour
                if ax:
                    trictr = ax.tricontourf(triang, sig, v, cmap=colormap, norm=norm)

            # display the colorbar
            divider = make_axes_locatable(axes=ax)
            cax = divider.append_axes(position="right", size="5%", pad=0.1)

            if trictr:
                fig.colorbar(
                    mappable=trictr, label="Stress", format="%.4e", ticks=ticks, cax=cax
                )

            # plot the finite element mesh
            self.section.plot_mesh(materials=False, **dict(kwargs, ax=ax))

        if ax:
            return ax
        else:
            raise RuntimeError("Plot failed.")

    def plot_stress_vector(
        self,
        stress: str,
        title: str | None = None,
        cmap: str = "YlOrBr",
        normalize: bool = False,
        **kwargs,
    ) -> matplotlib.axes.Axes:
        r"""Plots stress vectors over the finite element mesh.

        Args:
            stress: Type of stress to plot, see below for allowable values
            title: Plot title, if None uses default plot title for selected stress
            cmap: Matplotlib color map, see
                https://matplotlib.org/stable/tutorials/colors/colormaps.html for more
                detail
            normalize: If set to True, ``CenteredNorm`` is used to scale the colormap,
                if set to False, the default linear scaling is used
            kwargs: Passed to :func:`~sectionproperties.post.post.plotting_context`

        Raises:
            RuntimeError: If the plot failed to be generated

        Returns:
            Matplotlib axes object

        .. admonition:: Stress vector plotting options

          Below is a list of the acceptable values for ``stress``:

          - ``stress="mzz_zxy"`` - resultant shear stress :math:`\sigma_{zxy,Mzz}`
            resulting from the torsion moment :math:`M_{zz}`

          - ``stress="vx_zxy"`` - resultant shear stress :math:`\sigma_{zxy,Vx}`
            resulting from the torsion moment :math:`V_{x}`

          - ``stress="vy_zxy"`` - resultant shear stress :math:`\sigma_{zxy,Vy}`
            resulting from the torsion moment :math:`V_{y}`

          - ``stress="v_zxy"`` - resultant shear stress :math:`\sigma_{zxy,\Sigma V}`
            resulting from the sum of the applied shear forces :math:`V_{x} + V_{y}`

          - ``stress="zxy"`` - resultant shear stress :math:`\sigma_{zxy}` resulting
            from all actions
        """
        # get required variables for stress plot
        stress_dict = {
            "mzz_zxy": {
                "sigx": "sig_zx_mzz",
                "sigy": "sig_zy_mzz",
                "title": r"Stress Vector Plot - $\sigma_{zxy,Mzz}$",
            },
            "vx_zxy": {
                "sigx": "sig_zx_vx",
                "sigy": "sig_zy_vx",
                "title": r"Stress Vector Plot - $\sigma_{zxy,Vx}$",
            },
            "vy_zxy": {
                "sigx": "sig_zx_vy",
                "sigy": "sig_zy_vy",
                "title": r"Stress Vector Plot - $\sigma_{zxy,Vy}$",
            },
            "v_zxy": {
                "sigx": "sig_zx_v",
                "sigy": "sig_zy_v",
                "title": r"Stress Vector Plot - $\sigma_{zxy,\Sigma V}$",
            },
            "zxy": {
                "sigx": "sig_zx",
                "sigy": "sig_zy",
                "title": r"Stress Vector Plot - $\sigma_{zxy}$",
            },
        }

        # populate stresses
        sigxs = []
        sigys = []

        for group in self.material_groups:
            sigxs.append(getattr(group.stress_result, stress_dict[stress]["sigx"]))
            sigys.append(getattr(group.stress_result, stress_dict[stress]["sigy"]))

        # apply title
        if not title:
            title = stress_dict[stress]["title"]

        # create plot and setup the plot
        with post.plotting_context(title=title, **kwargs) as (fig, ax):
            # set up the colormap
            colormap = cm.get_cmap(name=cmap)

            # initialise quiver plot list max scale
            quiv_list = []
            max_scale = 0

            norm = None
            quiv = None
            if normalize:
                norm = CenteredNorm()

            # initialise colormap values
            c = np.hypot(sigxs[0], sigys[0])
            c_min = min(c)
            c_max = max(c)

            # plot the vectors
            for idx, sigx in enumerate(sigxs):
                sigy = sigys[idx]

                # scale the color with respect to the magnitude of the vector
                c = np.hypot(sigx, sigy)

                if ax:
                    quiv = ax.quiver(
                        self.section._mesh_nodes[:, 0],
                        self.section._mesh_nodes[:, 1],
                        sigx,
                        sigy,
                        c,
                        cmap=colormap,
                        norm=norm,
                    )

                    # get the scale and store the max value
                    quiv._init()
                    max_scale = max(max_scale, quiv.scale)
                    quiv_list.append(quiv)

                # update the colormap values
                c_min = min(c_min, min(c))
                c_max = max(c_max, max(c))

            # apply the scale
            for quiv_plot in quiv_list:
                quiv_plot.scale = max_scale

            # apply the colorbar
            v1 = np.linspace(start=c_min, stop=c_max, num=15, endpoint=True)
            divider = make_axes_locatable(axes=ax)
            cax = divider.append_axes(position="right", size="5%", pad=0.1)

            fig.colorbar(
                mappable=quiv, label="Stress", format="%.4e", ticks=v1, cax=cax
            )

            # plot the finite element mesh
            self.section.plot_mesh(materials=False, **dict(kwargs, ax=ax))

        if ax:
            return ax
        else:
            raise RuntimeError("Plot failed.")

    def get_stress(self) -> list[dict]:
        r"""Returns the stresses within each material.

        Returns:
            A list of dictionaries containing the cross-section stresses at each node
            for each material

        Note:
            Each list of stresses in the dictionary contains the stresses at every node
            (order from ``node 0`` to ``node n``) in the entire mesh. As a result, when
            the current material does not exist at a node, a value of zero will be
            reported.

        .. admonition:: Dictionary keys and values

          In general the stresses are described by an action followed by a stress
          direction  ``(action)_(stress-direction)``, e.g. ``mzz_zx`` represents the
          shear stress in the ``zx`` direction caused by the torsion ``mzz``.

          Below is a list of the returned dictionary keys and values:

          - ``"material"`` - material name

          - ``"n_zz"`` - normal stress :math:`\sigma_{zz,N}` resulting from the
            axial load :math:`N`

          - ``"mxx_zz"`` - normal stress :math:`\sigma_{zz,Mxx}` resulting from
            the bending moment :math:`M_{xx}`

          - ``"myy_zz"`` - normal stress :math:`\sigma_{zz,Myy}` resulting from
            the bending moment :math:`M_{yy}`

          - ``"m11_zz"`` - normal stress :math:`\sigma_{zz,M11}` resulting from
            the bending moment :math:`M_{11}`

          - ``"m22_zz"`` - normal stress :math:`\sigma_{zz,M22}` resulting from
            the bending moment :math:`M_{22}`

          - ``"m_zz"`` - normal stress :math:`\sigma_{zz,\Sigma M}` resulting
            from all bending moments :math:`M_{xx} + M_{yy} + M_{11} + M_{22}`

          - ``"mzz_zx"`` - ``x`` component of the shear stress
            :math:`\sigma_{zx,Mzz}` resulting from the torsion moment :math:`M_{zz}`

          - ``"mzz_zy"`` - ``y`` component of the shear stress
            :math:`\sigma_{zy,Mzz}` resulting from the torsion moment :math:`M_{zz}`

          - ``"mzz_zxy"`` - resultant shear stress :math:`\sigma_{zxy,Mzz}`
            resulting from the torsion moment :math:`M_{zz}`

          - ``"vx_zx"`` - ``x`` component of the shear stress
            :math:`\sigma_{zx,Vx}` resulting from the shear force :math:`V_{x}`

          - ``"vx_zy"`` - ``y`` component of the shear stress
            :math:`\sigma_{zy,Vx}` resulting from the shear force :math:`V_{x}`

          - ``"vx_zxy"`` - resultant shear stress :math:`\sigma_{zxy,Vx}`
            resulting from the shear force :math:`V_{x}`

          - ``"vy_zx"`` - ``x`` component of the shear stress
            :math:`\sigma_{zx,Vy}` resulting from the shear force :math:`V_{y}`

          - ``"vy_zy"`` - ``y`` component of the shear stress
            :math:`\sigma_{zy,Vy}` resulting from the shear force :math:`V_{y}`

          - ``"vy_zxy"`` - resultant shear stress :math:`\sigma_{zxy,Vy}`
            resulting from the shear force :math:`V_{y}`

          - ``"v_zx"`` - ``x`` component of the shear stress
            :math:`\sigma_{zx,\Sigma V}` resulting from the sum of the applied shear
            forces :math:`V_{x} + V_{y}`.

          - ``"v_zy"`` - ``y`` component of the shear stress
            :math:`\sigma_{zy,\Sigma V}` resulting from the sum of the applied shear
            forces :math:`V_{x} + V_{y}`.

          - ``"v_zxy"`` - resultant shear stress :math:`\sigma_{zxy,\Sigma V}`
            resulting from the sum of the applied shear forces :math:`V_{x} + V_{y}`

          - ``"zz"`` - combined normal stress :math:`\sigma_{zz}` resulting from
            all actions

          - ``"zx"`` - ``x`` component of the shear stress :math:`\sigma_{zx}`
            resulting from all actions

          - ``"zy"`` - ``y`` component of the shear stress :math:`\sigma_{zy}`
            resulting from all actions

          - ``"zxy"`` - resultant shear stress :math:`\sigma_{zxy}` resulting
            from all actions

          - ``"zxy"`` - resultant shear stress :math:`\sigma_{zxy}` resulting
            from all actions

          - ``"11"`` - major principal stress :math:`\sigma_{11}` resulting from
            all actions

          - ``"33"`` - minor principal stress :math:`\sigma_{33}` resulting from
            all actions

          - ``"vm"`` - von Mises stress :math:`\sigma_{vM}` resulting from all
            actions
        """
        # generate list
        stress = []

        for group in self.material_groups:
            stress.append(
                {
                    "material": group.material.name,
                    "sig_zz_n": group.stress_result.sig_zz_n,
                    "sig_zz_mxx": group.stress_result.sig_zz_mxx,
                    "sig_zz_myy": group.stress_result.sig_zz_myy,
                    "sig_zz_m11": group.stress_result.sig_zz_m11,
                    "sig_zz_m22": group.stress_result.sig_zz_m22,
                    "sig_zz_m": group.stress_result.sig_zz_m,
                    "sig_zx_mzz": group.stress_result.sig_zx_mzz,
                    "sig_zy_mzz": group.stress_result.sig_zy_mzz,
                    "sig_zxy_mzz": group.stress_result.sig_zxy_mzz,
                    "sig_zx_vx": group.stress_result.sig_zx_vx,
                    "sig_zy_vx": group.stress_result.sig_zy_vx,
                    "sig_zxy_vx": group.stress_result.sig_zxy_vx,
                    "sig_zx_vy": group.stress_result.sig_zx_vy,
                    "sig_zy_vy": group.stress_result.sig_zy_vy,
                    "sig_zxy_vy": group.stress_result.sig_zxy_vy,
                    "sig_zx_v": group.stress_result.sig_zx_v,
                    "sig_zy_v": group.stress_result.sig_zy_v,
                    "sig_zxy_v": group.stress_result.sig_zxy_v,
                    "sig_zz": group.stress_result.sig_zz,
                    "sig_zx": group.stress_result.sig_zx,
                    "sig_zy": group.stress_result.sig_zy,
                    "sig_zxy": group.stress_result.sig_zxy,
                    "sig_11": group.stress_result.sig_11,
                    "sig_33": group.stress_result.sig_33,
                    "sig_vm": group.stress_result.sig_vm,
                }
            )

        return stress

    def plot_mohrs_circles(
        self,
        x: float,
        y: float,
        title: str | None = None,
        **kwargs,
    ) -> matplotlib.axes.Axes:
        r"""Plots Mohr's circles of the 3D stress state at position (``x``, ``y``).

        Args:
            x: x-coordinate of the point to draw Mohr's Circle
            y: y-coordinate of the point to draw Mohr's Circle
            title: Plot title, if None uses default plot title "Mohr's Circles for 3D
                Stress State at {pt}"
            kwargs: Passed to :func:`~sectionproperties.post.post.plotting_context`

        Raises:
            ValueError: If the point (``x``, ``y``) is not within the mesh
            RuntimeError: If the plot failed to be generated

        Returns:
            Matplotlib axes object

        Example:
            The following example plots the Mohr's circles for the 3D stress state
            within a 150x90x12 UA section at the point ``x=10``, ``y=88.9`` resulting
            from the following actions:

            - :math:`N = 50` kN

            - :math:`M_{xx} = -5` kN.m

            - :math:`M_{22} = 2.5` kN.m

            - :math:`M_{zz} = 1.5` kN.m

            - :math:`V_{x} = 10` kN

            - :math:`V_{y} = 5` kN

            .. plot::
                :include-source: True
                :caption: Mohr's circles for a 150x90x12 UA

                from sectionproperties.pre.library import angle_section
                from sectionproperties.analysis import Section

                # create geometry and section
                geom = angle_section(d=150, b=90, t=12, r_r=10, r_t=5, n_r=8)
                geom.create_mesh(mesh_sizes=[0])
                sec = Section(geometry=geom)

                # perform analysis
                sec.calculate_geometric_properties()
                sec.calculate_warping_properties()
                post = sec.calculate_stress(
                    n=50e3, mxx=-5e6, m22=2.5e6, mzz=0.5e6, vx=10e3, vy=5e3
                )

                # plot mohr's circle
                post.plot_mohrs_circles(x=10, y=88.9)
        """
        # get mesh data
        pt = x, y
        nodes = self.section._mesh_nodes
        ele = self.section._mesh_elements
        triang = tri.Triangulation(nodes[:, 0], nodes[:, 1], ele[:, 0:3])

        # find in which material group the point lies
        pt_group = None

        for group in self.material_groups:
            mask_array = np.ones(len(self.section.elements), dtype=bool)
            mask_array[group.el_ids] = False
            triang.set_mask(mask_array)
            trifinder = triang.get_trifinder()

            if trifinder(*pt) != -1:
                pt_group = group

            triang.set_mask(None)

        if pt_group is None:
            raise ValueError(f"Point {(*pt,)} is not within mesh")

        # assesmble the stress results from the relevant material group
        sigma_zz_v = pt_group.stress_result.sig_zz
        tau_xz_v = pt_group.stress_result.sig_zx
        tau_yz_v = pt_group.stress_result.sig_zy

        # get the interpolators
        sigma_zz_interp = tri.LinearTriInterpolator(triang, sigma_zz_v)
        tau_xz_interp = tri.LinearTriInterpolator(triang, tau_xz_v)
        tau_yz_interp = tri.LinearTriInterpolator(triang, tau_yz_v)

        # get the stresses at the point
        sigma_zz = sigma_zz_interp(*pt).item()
        tau_xz = tau_xz_interp(*pt).item()
        tau_yz = tau_yz_interp(*pt).item()

        # assemble the stress tensor
        sigma_xx = 0
        sigma_yy = 0
        tau_xy = 0
        sigma = np.array(
            [
                [sigma_xx, tau_xy, tau_xz],
                [tau_xy, sigma_yy, tau_yz],
                [tau_xz, tau_yz, sigma_zz],
            ],
            dtype=float,
        )

        # solve for the principal stresses using the general approach
        s, n = np.linalg.eig(a=sigma)
        sigma_3, sigma_2, sigma_1 = np.sort(s)

        # the tractions on each plane in cartesian coords wrt principal axes
        n_inv = np.linalg.inv(n)
        tractions = []

        for col in range(3):
            ss = n_inv[:, col].T @ np.diag(s) @ n_inv[:, col]
            ts = np.sqrt(np.linalg.norm(np.diag(s) @ n_inv[:, col]) ** 2 - ss**2)
            tractions.append((ss, ts))

        def plot_circle(
            ax: matplotlib.axes.Axes,
            c: tuple[float, float],
            r: float,
            col: str,
            label: str | None = None,
            fill: bool | None = None,
        ) -> None:
            circ = Circle(c, r, fill=fill, ec=col, label=label)
            ax.add_patch(circ)
            ax.set_aspect(1)
            ax.autoscale_view()

        if not title:
            title = f"Mohr's Circles for 3D Stress State at {(*pt,)}"

        # create plot and setup the plot
        with post.plotting_context(title=title, **kwargs) as (fig, ax):
            plot_circle(
                ax,
                (0.5 * (sigma_2 + sigma_3), 0),
                0.5 * (sigma_2 - sigma_3),
                "r",
                r"C1: ($\sigma_{22}$, $\sigma_{33}$)",
            )
            plot_circle(
                ax,
                (0.5 * (sigma_1 + sigma_3), 0),
                0.5 * (sigma_1 - sigma_3),
                "b",
                r"C2: ($\sigma_{11}$, $\sigma_{33}$)",
            )
            plot_circle(
                ax,
                (0.5 * (sigma_1 + sigma_2), 0),
                0.5 * (sigma_1 - sigma_2),
                "k",
                r"C3: ($\sigma_{11}$, $\sigma_{22}$)",
            )

            for i, plane, col in zip(range(3), ["X", "Y", "Z"], ["r", "b", "k"]):
                if ax:
                    ax.plot(*tractions[i], f"{col}.", label=rf"{plane}-face")

            if ax:
                ax.set_axisbelow(True)
                ax.grid(which="both")
                ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5))

                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)

                ax.set_ylabel(r"Shear stress $\tau$ (MPa)")
                ax.set_xlabel(r"Direct stress $\sigma$ (MPa)")

                ax.xaxis.set_tick_params(bottom=True, top=False, direction="inout")
                ax.yaxis.set_tick_params(left=True, right=False, direction="inout")

            # the following is just to get the labels positioned outside the axes
            if ax:
                # store default label positions
                x_lbl_pos = ax.xaxis.label.get_position()
                y_lbl_pos = ax.yaxis.label.get_position()

                # Make spines pass through zero of the other axis
                ax.spines["bottom"].set_position(("data", 0.0))
                ax.spines["left"].set_position(position=("data", 0.0))

                # Now set the coords
                ax.xaxis.set_label_coords(*x_lbl_pos)
                ax.yaxis.set_label_coords(*y_lbl_pos)

        if ax:
            return ax
        else:
            raise RuntimeError("Plot failed.")


@dataclass
class StressResult:
    r"""Class for storing a stress result.

    Provides variables to store the results from a cross-section stress analysis. Also
    provides a method to calculate combined stresses.

    Attributes:
        num_nodes: Number of nodes in the finite element mesh
        sig_zz_n: Normal stress (:math:`\sigma_{zz,N}`) resulting from an axial force
        sig_zz_mxx: Normal stress (:math:`\sigma_{zz,Mxx}`) resulting from a bending
            moment about the xx-axis
        sig_zz_myy: Normal stress (:math:`\sigma_{zz,Myy}`) resulting from a bending
            moment about the yy-axis
        sig_zz_m11: Normal stress (:math:`\sigma_{zz,M11}`) resulting from a bending
            moment about the 11-axis
        sig_zz_m22: Normal stress (:math:`\sigma_{zz,M22}`) resulting from a bending
            moment about the 22-axis
        sig_zx_mzz: Shear stress (:math:`\sigma_{zx,Mzz}`) resulting from a torsio
             moment about the zz-axis
        sig_zy_mzz: Shear stress (:math:`\sigma_{zy,Mzz}`) resulting from a torsio
             moment about the zz-axis
        sig_zx_vx: Shear stress (:math:`\sigma_{zx,Vx}`) resulting from a shear force in
            the x-direction
        sig_zy_vx: Shear stress (:math:`\sigma_{zy,Vx}`) resulting from a shear force in
            the x-direction
        sig_zx_vy: Shear stress (:math:`\sigma_{zx,Vy}`) resulting from a shear force in
            the y-direction
        sig_zy_vy: Shear stress (:math:`\sigma_{zy,Vy}`) resulting from a shear force in
            the y-direction
        sig_zz_m: Normal stress (:math:`\sigma_{zz,\Sigma M}`) resulting from all
            bending moments
        sig_zxy_mzz: Resultant shear stress (:math:`\sigma_{zxy,Mzz}`) resulting from a
            torsion moment in the zz-direction
        sig_zxy_vx: Resultant shear stress (:math:`\sigma_{zxy,Vx}`) resulting from a a
            shear force in the x-direction
        sig_zxy_vy: Resultant shear stress (:math:`\sigma_{zxy,Vy}`) resulting from a a
            shear force in the y-direction
        sig_zx_v: Shear stress (:math:`\sigma_{zx,\Sigma V}`) resulting from all shear
            forces
        sig_zy_v: Shear stress (:math:`\sigma_{zy,\Sigma V}`) resulting from all shear
            forces
        sig_zxy_v: Resultant shear stress (:math:`\sigma_{zxy,\Sigma V}`) resulting from
            all shear forces
        sig_zz: Combined normal force (:math:`\sigma_{zz}`) resulting from all actions
        sig_zx: Combined shear stress (:math:`\sigma_{zx}`) resulting from all actions
        sig_zy: Combined shear stress (:math:`\sigma_{zy}`) resulting from all actions
        sig_zxy: Combined resultant shear stress (:math:`\sigma_{zxy}`) resulting from
            all actions
        sig_11: Major principal stress (:math:`\sigma_{11}`) resulting from all actions
        sig_33: Minor principal stress (:math:`\sigma_{33}`) resulting from all actions
        sig_vm: von Mises stress (:math:`\sigma_{VM}`) resulting from all actions
    """
    num_nodes: int
    sig_zz_n: np.ndarray = field(init=False)
    sig_zz_mxx: np.ndarray = field(init=False)
    sig_zz_myy: np.ndarray = field(init=False)
    sig_zz_m11: np.ndarray = field(init=False)
    sig_zz_m22: np.ndarray = field(init=False)
    sig_zx_mzz: np.ndarray = field(init=False)
    sig_zy_mzz: np.ndarray = field(init=False)
    sig_zx_vx: np.ndarray = field(init=False)
    sig_zy_vx: np.ndarray = field(init=False)
    sig_zx_vy: np.ndarray = field(init=False)
    sig_zy_vy: np.ndarray = field(init=False)
    sig_zz_m: np.ndarray = field(init=False)
    sig_zxy_mzz: np.ndarray = field(init=False)
    sig_zxy_vx: np.ndarray = field(init=False)
    sig_zxy_vy: np.ndarray = field(init=False)
    sig_zx_v: np.ndarray = field(init=False)
    sig_zy_v: np.ndarray = field(init=False)
    sig_zxy_v: np.ndarray = field(init=False)
    sig_zz: np.ndarray = field(init=False)
    sig_zx: np.ndarray = field(init=False)
    sig_zy: np.ndarray = field(init=False)
    sig_zxy: np.ndarray = field(init=False)
    sig_11: np.ndarray = field(init=False)
    sig_33: np.ndarray = field(init=False)
    sig_vm: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        """Preallocates the numpy arrays in StressResult."""
        # allocate stresses arising directly from actions
        self.sig_zz_n = np.zeros(self.num_nodes)
        self.sig_zz_mxx = np.zeros(self.num_nodes)
        self.sig_zz_myy = np.zeros(self.num_nodes)
        self.sig_zz_m11 = np.zeros(self.num_nodes)
        self.sig_zz_m22 = np.zeros(self.num_nodes)
        self.sig_zx_mzz = np.zeros(self.num_nodes)
        self.sig_zy_mzz = np.zeros(self.num_nodes)
        self.sig_zx_vx = np.zeros(self.num_nodes)
        self.sig_zy_vx = np.zeros(self.num_nodes)
        self.sig_zx_vy = np.zeros(self.num_nodes)
        self.sig_zy_vy = np.zeros(self.num_nodes)

        # allocate combined stresses
        self.sig_zz_m = np.zeros(self.num_nodes)
        self.sig_zxy_mzz = np.zeros(self.num_nodes)
        self.sig_zxy_vx = np.zeros(self.num_nodes)
        self.sig_zxy_vy = np.zeros(self.num_nodes)
        self.sig_zx_v = np.zeros(self.num_nodes)
        self.sig_zy_v = np.zeros(self.num_nodes)
        self.sig_zxy_v = np.zeros(self.num_nodes)
        self.sig_zz = np.zeros(self.num_nodes)
        self.sig_zx = np.zeros(self.num_nodes)
        self.sig_zy = np.zeros(self.num_nodes)
        self.sig_zxy = np.zeros(self.num_nodes)
        self.sig_11 = np.zeros(self.num_nodes)
        self.sig_33 = np.zeros(self.num_nodes)
        self.sig_vm = np.zeros(self.num_nodes)

    def calculate_combined_stresses(self) -> None:
        """Calculates and stores the combined cross-section stresses."""
        self.sig_zz_m = (
            self.sig_zz_mxx + self.sig_zz_myy + self.sig_zz_m11 + self.sig_zz_m22
        )
        self.sig_zxy_mzz = (self.sig_zx_mzz**2 + self.sig_zy_mzz**2) ** 0.5
        self.sig_zxy_vx = (self.sig_zx_vx**2 + self.sig_zy_vx**2) ** 0.5
        self.sig_zxy_vy = (self.sig_zx_vy**2 + self.sig_zy_vy**2) ** 0.5
        self.sig_zx_v = self.sig_zx_vx + self.sig_zx_vy
        self.sig_zy_v = self.sig_zy_vx + self.sig_zy_vy
        self.sig_zxy_v = (self.sig_zx_v**2 + self.sig_zy_v**2) ** 0.5
        self.sig_zz = self.sig_zz_n + self.sig_zz_m
        self.sig_zx = self.sig_zx_mzz + self.sig_zx_v
        self.sig_zy = self.sig_zy_mzz + self.sig_zy_v
        self.sig_zxy = (self.sig_zx**2 + self.sig_zy**2) ** 0.5
        self.sig_1 = self.sig_zz / 2 + np.sqrt(
            (self.sig_zz / 2) ** 2 + self.sig_zxy**2
        )
        self.sig_33 = self.sig_zz / 2 - np.sqrt(
            (self.sig_zz / 2) ** 2 + self.sig_zxy**2
        )
        self.sig_vm = (self.sig_zz**2 + 3 * self.sig_zxy**2) ** 0.5
