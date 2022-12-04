#  2020 Tommaso Ciussani and Giacomo Giuliari
"""
Example usage of the icarus_simulator and sat_plotter libraries.
This file makes use of the configuration mechanism, described in configuration.py.

For general information on the library usage, refer to readme.md and to the following files:
    - icarus_simulator/icarus_simulator.py,
    - icarus_simulator/phases/base_phase.py,
    - icarus_simulator/strategies/base_strategy.py,
    - icarus_simulator/structure_definitions,
    - icarus_simulator/multiprocessor.py

This file first exemplifies the creation of the computation phases and the simulation execution, then extracts data
from the IcarusSimulator object and creates useful plots.
After adjusting the class constants, execute the file to create the plots and the result dumps.
Due to the computational burden, it is advised to always run this library on a heavy-multicore machine.
"""
from statistics import mean
import matplotlib.pyplot as plt
import numpy as np

from icarus_simulator.icarus_simulator import IcarusSimulator
from icarus_simulator.default_properties import *
from icarus_simulator.phases import *
from sat_plotter import GeoPlotBuilder
from sat_plotter.stat_plot_builder import StatPlotBuilder

from configuration import CONFIG, parse_config, get_strat

# Change these parameters to match your machine
CORE_NUMBER = 96
RESULTS_DIR = "result_dumps"


def main():
    results_detectability = list()
    results_cost = list()
    all_costs = dict()
    all_dectectability = dict()

    # Optional feature: parse the configuration file
    full_conf = parse_config(CONFIG)

    for conf_id, conf in enumerate(full_conf):
        # Repeat the simulation process for all configurations in the config file
        print(
            "---------------------------------------------------------------------------------"
        )
        # 1-based
        print(
            f"Configuration number {conf_id + 1} - {get_strat('rout', conf).name}")

        # SIMULATION: phase definition and final computation
        lsn_ph = LSNPhase(
            True,
            True,
            lsn_strat=get_strat("lsn", conf),
            lsn_out=SAT_POS,
            nw_out=SAT_NW,
            isls_out=SAT_ISLS,
        )

        grid_ph = GridPhase(
            True,
            True,
            grid_strat=get_strat("grid", conf),
            weight_strat=get_strat("gweight", conf),
            grid_out=FULL_GRID_POS,
            size_out=GRID_FULL_SZ,
        )

        cov_ph = CoveragePhase(
            True,
            True,
            cov_strat=get_strat("cover", conf),
            sat_in=SAT_POS,
            grid_in=FULL_GRID_POS,
            cov_out=COVERAGE,
            grid_out=GRID_POS,
        )

        rout_ph = RoutingPhase(
            True,
            True,
            CORE_NUMBER,
            2,
            rout_strat=get_strat("rout", conf),
            grid_in=GRID_POS,
            cov_in=COVERAGE,
            nw_in=SAT_NW,
            paths_out=PATH_DATA,
        )

        edge_ph = EdgePhase(
            True,
            True,
            CORE_NUMBER,
            1,
            ed_strat=get_strat("edges", conf),
            paths_in=PATH_DATA,
            nw_in=SAT_NW,
            sats_in=SAT_POS,
            grid_in=GRID_POS,
            edges_out=EDGE_DATA,
        )

        # FULL_GRID_POS is passed for consistency with other experiments, where the coverage grid filtering is different
        bw_ph = TrafficPhase(
            True,
            True,
            select_strat=get_strat("bw_sel", conf),
            assign_strat=get_strat("bw_asg", conf),
            grid_in=FULL_GRID_POS,
            paths_in=PATH_DATA,
            edges_in=EDGE_DATA,
            bw_out=BW_DATA,
        )

        latk_ph = LinkAttackPhase(
            True,
            True,
            CORE_NUMBER,
            3,
            geo_constr_strat=get_strat("atk_constr", conf),
            filter_strat=get_strat("atk_filt", conf),
            feas_strat=get_strat("atk_feas", conf),
            optim_strat=get_strat("atk_optim", conf),
            grid_in=GRID_POS,
            paths_in=PATH_DATA,
            edges_in=EDGE_DATA,
            bw_in=BW_DATA,
            latk_out=ATK_DATA,
        )

        zatk_ph = ZoneAttackPhase(
            True,
            True,
            CORE_NUMBER,
            4,
            geo_constr_strat=get_strat("atk_constr", conf),
            zone_select_strat=get_strat("zone_select", conf),
            zone_build_strat=get_strat("zone_build", conf),
            zone_edges_strat=get_strat("zone_edges", conf),
            zone_bneck_strat=get_strat("zone_bneck", conf),
            atk_filter_strat=get_strat("atk_filt", conf),
            atk_feas_strat=get_strat("atk_feas", conf),
            atk_optim_strat=get_strat("atk_optim", conf),
            grid_in=GRID_POS,
            paths_in=PATH_DATA,
            edges_in=EDGE_DATA,
            bw_in=BW_DATA,
            atk_in=ATK_DATA,
            zatk_out=ZONE_ATK_DATA,
        )

        sim = IcarusSimulator(
            [lsn_ph, grid_ph, cov_ph, rout_ph, edge_ph, bw_ph, latk_ph, zatk_ph],
            RESULTS_DIR,
        )
        sim.compute_simulation()
        print("Computation finished")

        # EXAMPLE PLOTS
        output_folder = f"output"

        # GEOGRAPHICAL PLOTS
        sat_pos, isls, grid_pos = (
            sim.get_property(SAT_POS),
            sim.get_property(SAT_ISLS),
            sim.get_property(GRID_POS),
        )
        edge_data, bw_data = sim.get_property(
            EDGE_DATA), sim.get_property(BW_DATA)
        path_data, atk_data = sim.get_property(
            PATH_DATA), sim.get_property(ATK_DATA)
        zatk_data = sim.get_property(ZONE_ATK_DATA)

        # PDF of attack detectability on ISL
        detects = [
            val.detectability / conf["bw_asg"]["udl_bw"]
            for ed, val in atk_data.items()
            if val is not None and -1 not in ed
        ]
        all_dectectability[get_strat('rout', conf).name2] = detects

        size = len(detects)
        pdf_count = sum(x <= 0.1 for x in detects)
        res = round(pdf_count / size, 3)
        print(f"{get_strat('rout', conf).name} Detectability PDF -> P(X<0.1)={res}")

        pair = (f"{get_strat('rout', conf).name}-detectability",
                size, pdf_count, res)
        results_detectability.append(pair)

        # PDF of attack cost on ISL
        costs = [
            val.cost / conf["bw_asg"]["isl_bw"]
            for ed, val in atk_data.items()
            if val is not None and -1 not in ed
        ]
        all_costs[get_strat('rout', conf).name2] = costs

        size = len(costs)
        pdf_count = sum(x >= 0.9 for x in costs)
        res = round(pdf_count / size, 3)

        print(f"{get_strat('rout', conf).name} Cost PDF -> P(X>0.9)={res}")

        pair = (f"{get_strat('rout', conf).name}-cost", size, pdf_count, res)
        results_cost.append(pair)

    # All graph cost PDF
    builder = StatPlotBuilder().set_bins(10).set_size(14, 5).set_thickness(5)
    for key, value in all_costs.items():
        builder.pdf(value, key)
    builder.labels("Cost", "PDF").set_zero_y().legend("upper left").save_to_file(
        f"{output_folder}/all-cost_pdf.png"
    )

    # All graph detect PDF
    builder = StatPlotBuilder().set_bins(10).set_size(14, 5).set_thickness(5)
    for key, value in all_dectectability.items():
        builder.pdf(value, key)
    builder.labels("MaxUp", "PDF").set_zero_y().legend("upper right").save_to_file(
        f"{output_folder}/all-detectability_pdf.png"
    )

    # All graph cost CDF
    builder = StatPlotBuilder().set_size(14, 5).set_thickness(5)
    all_costs_cdf = {}
    for key, value in all_costs.items():
        all_costs_cdf[key] = builder.cdf(value, key)

    builder.labels("Cost", "CDF").set_zero_y().legend("upper left").save_to_file(
        f"{output_folder}/all-cost_cdf.png"
    )
    
    # All graph detect CDF
    builder = StatPlotBuilder().set_size(14, 5).set_thickness(5)
    all_detectability_cdf = {}
    for key, value in all_dectectability.items():
        all_detectability_cdf[key] = builder.cdf(value, key)

    builder.labels("MaxUp", "CDF").set_zero_y().legend("lower right").save_to_file(
        f"{output_folder}/all-detectability_cdf.png"
    )

    # Exporting Results
    with open('output/results_detectability.csv', 'w') as fp:
        fp.write('algo, samples, number, probability\n')
        fp.write(
            '\n'.join(f'{x[0]}, {x[1]}, {x[2]}, {x[3]}' for x in results_detectability))

    with open('output/results_cost.csv', 'w') as fp:
        fp.write('algo, samples, number, probability\n')
        fp.write(
            '\n'.join(f'{x[0]}, {x[1]}, {x[2]}, {x[3]}' for x in results_cost))

    with open('output/results_cost_cdf.csv', 'w') as fp:
        fp.write(f'algo\n\n')
        for key, value in all_costs_cdf.items():
            fp.write(f"{key}\n")
            fp.write(f"cost, {', '.join(str(x) for x in value['cost'])}\n")
            fp.write(f"cdf, {', '.join(str(x) for x in value['cdf'])}\n")
            fp.write('\n')

    with open('output/results_detectability_cdf.csv', 'w') as fp:
        fp.write(f'algo\n\n')
        for key, value in all_detectability_cdf.items():
            fp.write(f"{key}\n")
            fp.write(f"cost, {', '.join(str(x) for x in value['cost'])}\n")
            fp.write(f"cdf, {', '.join(str(x) for x in value['cdf'])}\n")
            fp.write('\n')

    with open('output/detectability_data.csv', 'w') as fp:
        fp.write(f'algo\n\n')
        for key, value in all_dectectability.items():
            fp.write(f"{key}, {', '.join(str(x) for x in value)}")
            fp.write('\n')

    with open('output/cost_data.csv', 'w') as fp:
        for key, value in all_costs.items():
            fp.write(f"{key}, {', '.join(str(x) for x in value)}")
            fp.write('\n')

    plt.close('all')


# Execute on main
if __name__ == "__main__":
    main()
