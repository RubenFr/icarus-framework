
#  2021 Ruben Fratty and Yuval Saar
#  a1 = 0.703
#  a2 = 0.07
#  a3 = 0.143
#  a4 = 0.084
import networkx as nx

from icarus_simulator.strategies.routing.base_routing_strat import BaseRoutingStrat
from icarus_simulator.strategies.routing.kds_rout_strat import KDSRoutStrat
from icarus_simulator.strategies.routing.ksp_rout_strat import KSPRoutStrat
from icarus_simulator.strategies.routing.klo_rout_strat import KLORoutStrat
from icarus_simulator.strategies.routing.kdg_rout_strat import KDGRoutStrat
from icarus_simulator.structure_definitions import GridPos, SdPair, Coverage, LbSet

from random import random


class RandomRoutStrat(BaseRoutingStrat):
    def __init__(self, desirability_stretch: float, k: int, esx_theta: float, **kwargs):
        super().__init__()
        self.desirability_stretch = desirability_stretch
        self.k = k
        self.esx_theta = esx_theta
        if len(kwargs) > 0:
            pass  # Appease the unused param inspection

    @property
    def name(self) -> str:
        return "random"

    @property
    def name2(self) -> str:
        return "PROPOSED"

    @property
    def param_description(self) -> str:
        return f"{self.desirability_stretch}k{self.k}"

    def compute(
            self, pair: SdPair, grid: GridPos, network: nx.Graph, coverage: Coverage
    ) -> LbSet:

        # Random number between [0,1]
        a = random()

        if 0 <= a < 0.703:
            return KSPRoutStrat(self.desirability_stretch, self.k).compute(pair, grid, network, coverage)
        elif 0.703 <= a < 0.773:
            return KDGRoutStrat(self.desirability_stretch, self.k).compute(pair, grid, network, coverage)
        elif 0.773 <= a < 0.916:
            return KDSRoutStrat(self.desirability_stretch, self.k).compute(pair, grid, network, coverage)
        else:
            return KLORoutStrat(self.desirability_stretch, self.k, self.esx_theta).compute(pair, grid, network,
                                                                                           coverage)

