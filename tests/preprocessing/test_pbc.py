import os

import ase
import numpy as np
import pytest
from ase.io import read
from pymatgen.io.ase import AseAtomsAdaptor

from ocpmodels.common.utils import get_pbc_distances
from ocpmodels.preprocessing import AtomsToGraphs


@pytest.fixture(scope="class")
def load_data(request):
    atoms = read(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "atoms.json"),
        index=0,
        format="json",
    )
    a2g = AtomsToGraphs(
        max_neigh=12,
        radius=6,
        dummy_distance=7,
        dummy_index=-1,
        r_energy=True,
        r_forces=True,
        r_distances=True,
    )
    data_list = a2g.convert_all([atoms])
    request.cls.data = data_list[0]


@pytest.mark.usefixtures("load_data")
class TestPBC:
    def test_pbc_distances(self):
        data = self.data
        edge_index, pbc_distances = get_pbc_distances(
            data.pos,
            data.edge_index,
            data.cell,
            data.cell_offsets,
            data.natoms,
        )

        # consider non-dummy edges only
        nonnegative_idx = (data.edge_index[1] != -1).nonzero().view(-1)
        np.testing.assert_array_equal(
            data.edge_index[:, nonnegative_idx], edge_index,
        )
        np.testing.assert_array_almost_equal(
            data.distances[nonnegative_idx], pbc_distances
        )