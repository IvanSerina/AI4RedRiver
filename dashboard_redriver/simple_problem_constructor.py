import pandas as pd
import numpy as np
import os
from enum import Enum
import calendar
import statsmodels.api as sm
from scipy.optimize import minimize
import scipy.io

from datetime import datetime, timedelta

from number_helper import NumberHelper
from coefficients_evaluation import coefficients_evaluation

from unified_planning.shortcuts import *
from unified_planning.model import Problem, Object
from unified_planning.model.metrics import MinimizeExpressionOnFinalState

INPUT_TURBINE = 147.5 # 295
INPUT_BOTTOM_RELEASE = 1833
INPUT_SPILLWAY_RELEASE = 2350
MIN_HOA_BINH_HEIGHT = 80.0
MAX_HOA_BINH_HEIGHT = 117.0
MIN_LEVEL_HANOI = 1.4
MAX_LEVEL_HANOI = 11.5
LEVEL_LOSS_DAM = 5.79e-03
SWI_DEMAND = 500
MIN_RELEASES_HOA_BINH = 214
FLOW_ALPHA_INPUT_HOA_BINH_HOA_BIN_DAM = 1
FLOW_BETA_HOA_BINH_DAM = 0

LEVEL_CONSTANT_HOA_BINH_DAM = 60.79

MIN_STORAGE_HOA_BINH_DAM = (MIN_HOA_BINH_HEIGHT - 60.79) / 5.79e-3
MAX_STORAGE_HOA_BINH_DAM = (MAX_HOA_BINH_HEIGHT - 60.79) / 5.79e-3
POLICY_PENALTY = 10000
POLICY_REWARD = -100

BOTTOM_GATE_MULTIPLIER = 3

LAMBDA_R = 1

LAMBDA_RELEASE = 1
LAMBDA_ENERGY = -0.08

EFFICIENCY_HIGH = 1
EFFICIENCY_MEDIUM = 0.8
LIV_EFFICIENCY_MEDIUM = 9500.0
EFFICIENCY_LOW = 0.5
LIV_EFFICIENCY_LOW = 7800.0

OBJECTIVE_THRESHOLD = 999999
MIN_TOTAL_PRODUCTION = 0

MEDIUM_LEVEL_STORAGE = 100
MEDIUM_STORAGE = 8500 #(MEDIUM_LEVEL_STORAGE - 60.79) / 5.79e-3
PENALITY_MEDIUM_LEVEL_STORAGE = 5000
LOW_LEVEL_STORAGE = 90
LOW_STORAGE =  6772.02 #(LOW_LEVEL_STORAGE - 60.79) / 5.79e-3
PENALITY_LOW_LEVEL_STORAGE = 10000

class SimpleProblemConstructor(object):
    """RedRiverProblemsConstructor constructor for the simplified version of the problem"""

    _problem_path: str = None
    _problem: Problem = None
    _COEFFICIENTS_DICT: dict = None

    def __init__(
        self,
        coefficients_dict: dict = None,
        simulation = False
    ):
        super(SimpleProblemConstructor, self).__init__()
        self._problem = Problem()

        self._COEFFICIENTS_DICT = coefficients_dict
        
        self._simulation = simulation

        self.FLOW_GAMMA_SON_TAY = self._COEFFICIENTS_DICT['slope_ST'][3]
        self.FLOW_ALPHA_HOA_BINH_DAM_SON_TAY = self._COEFFICIENTS_DICT["slope_ST"][0]
        self.FLOW_ALPHA_YEN_BAI_STATION_SON_TAY = self._COEFFICIENTS_DICT["slope_ST"][1]
        self.FLOW_ALPHA_VU_QUANG_STATION_SON_TAY = self._COEFFICIENTS_DICT["slope_ST"][2]
        self.FLOW_ALPHA_SON_TAY_HANOI = self._COEFFICIENTS_DICT["q_slope_HN"][0]

        self.LEVEL_LOSS1_HANOI = self._COEFFICIENTS_DICT["h_slope_HN"][1]
        self.LEVEL_LOSS2_HANOI = self._COEFFICIENTS_DICT["h_slope_HN"][2]
        self.LEVEL_LOSS3_HANOI = self._COEFFICIENTS_DICT["h_slope_HN"][3]
        self.LEVEL_CONSTANT_HANOI = self._COEFFICIENTS_DICT["h_slope_HN"][0]



        # Define the user types from the one in the Red River PDDL domain
        self._user_types = {
            "Day": UserType("Day"),
            "Node": UserType("node"),
        }

        self._user_types.update(
            {
                "Dam": UserType("dam", self._user_types["Node"]),
                "Navigability_node": UserType("navigability_node", self._user_types["Node"]),
                "Regular": UserType("regular", self._user_types["Node"]),
            }
        )

        # nodes
        self._problem.add_object(Object("hoa_binh_dam", self._user_types["Dam"]))
        self._problem.add_object(Object("vu_quang_station", self._user_types["Regular"]))
        self._problem.add_object(Object("yen_bai_station", self._user_types["Regular"]))
        self._problem.add_object(Object("son_tay", self._user_types["Node"]))
        self._problem.add_object(Object("hanoi", self._user_types["Navigability_node"]))
        self._problem.add_object(Object("input_hoa_binh", self._user_types["Regular"]))

        self._add_predicates()

        self._add_functions()

        self._add_actions()

    def _add_predicates(self):

        # fluent fot the active day
        self._problem.add_fluent(
            Fluent("active", BoolType(), d=self._user_types["Day"]),
            default_initial_value=False,
        )
        
        # control day
        # self._problem.add_fluent(
        #     Fluent("control", BoolType(), d=self._user_types["Day"]),
        #     default_initial_value=False,
        # )

        # Predicate to check the next day
        self._problem.add_fluent(
            Fluent(
                "next_step",
                BoolType(),
                d1=self._user_types["Day"],
                d2=self._user_types["Day"],
            ),
            default_initial_value=False,
        )

        self._problem.add_fluent(
            Fluent(
                "evaluated_network",
                BoolType()
                ),
            default_initial_value=False
        )

    def _add_functions(self):
        # Functions for the problem

        #TODO: All the flow alpha and beta are needed?
        self._problem.add_fluent(
            Fluent(
                "flow_beta",
                RealType(),
                n=self._user_types["Regular"],
                d=self._user_types["Day"],
            ),
            default_initial_value=0,
        )

        self._problem.add_fluent(
            Fluent("flow", RealType(), n=self._user_types["Node"]),
            default_initial_value=0,
        )

        self._problem.add_fluent(
            Fluent("release", RealType(), n=self._user_types["Dam"]),
            default_initial_value=0,
        )
        self._problem.add_fluent(
            Fluent("release_bottom", RealType(), n=self._user_types["Dam"]),
            default_initial_value=0,
        )
        self._problem.add_fluent(
            Fluent("release_spillways", RealType(), n=self._user_types["Dam"]),
            default_initial_value=0,
        )
        
        # Total release for the dam, used for the objective function
        self._problem.add_fluent(
            Fluent("total_release", RealType(), n=self._user_types["Dam"]),
            default_initial_value=0,
        )
        
        self._problem.add_fluent(
            Fluent("total_production", RealType(), n=self._user_types["Dam"]),
            default_initial_value=0,
        )
        
        self._problem.add_fluent(
            Fluent("hydropower_production", RealType(), n=self._user_types["Dam"]),
            default_initial_value=0,
        )
        
        # Energy demand for each day
        # self._problem.add_fluent(
        #     Fluent(
        #         "energy_demand",
        #         RealType(),
        #         d=self._user_types["Day"],
        #         ),
        #     default_initial_value=0
        # )
        
        # # Efficency of the dam
        # self._problem.add_fluent(
        #     Fluent(
        #         "efficiency_aprx",
        #         RealType(),
        #         ),
        #     default_initial_value=0
        #     )

        # min release from the turbine gate
        self._problem.add_fluent(
            Fluent(
                "min_release", 
                RealType(), 
                n=self._user_types["Dam"],
                d=self._user_types["Day"]
            ),
            default_initial_value=214,
        )
            
        self._problem.add_fluent(
            Fluent("storage", RealType(), n=self._user_types["Dam"]),
            default_initial_value=0,
        )

        self._problem.add_fluent(
            Fluent("efficiency", RealType(), n=self._user_types["Dam"]),
            default_initial_value=1,
        )

        self._problem.add_fluent(
            Fluent("maximum_turbine_release", RealType(), n=self._user_types["Dam"]),
            default_initial_value=0,
        )

        self._problem.add_fluent(
            Fluent("level", RealType(), n=self._user_types["Navigability_node"]),
            default_initial_value=0,
        )
        
        # Lagged flow for the problem
        self._problem.add_fluent(
            Fluent("lagged_flow", RealType(), n=self._user_types["Node"]),
            default_initial_value=0,
        )

        # Demands of the problem
        self._problem.add_fluent(
            Fluent(
                "agricultural_demand",
                RealType(),
                d=self._user_types["Day"],
            ),
            default_initial_value=0,
        )

        self._problem.add_fluent(
            Fluent(
                "max_bottom_release",
                RealType(),
                n=self._user_types["Dam"]
                ),
            default_initial_value=0
        )

        self._problem.add_fluent(
            Fluent(
                "max_spillways_release",
                RealType(),
                n=self._user_types["Dam"]
                ),
            default_initial_value=0
        )

        # Objective function
        self._problem.add_fluent(
            Fluent("objective", RealType()),
            default_initial_value=0,
        )

    def _add_actions(self):
        hoa_binh_dam: Object = self._problem.object("hoa_binh_dam")
        yen_bai_station: Object = self._problem.object("yen_bai_station")
        vu_quang_station: Object = self._problem.object("vu_quang_station")
        son_tay: Object = self._problem.object("son_tay")
        hanoi: Object = self._problem.object("hanoi")
        input_hoa_binh: Object = self._problem.object("input_hoa_binh")

        # Actions for the problem
        open_turbine_gate = self._define_open_turbine_action(hoa_binh_dam)
        self._problem.add_action(open_turbine_gate)

        open_bottom_gate = self._define_open_bottom_gates_action(hoa_binh_dam)
        self._problem.add_action(open_bottom_gate)

        open_spillway_gate = self._define_open_spillways_action(hoa_binh_dam)
        self._problem.add_action(open_spillway_gate)

        update_state_network = self._define_update_state_network(
            hoa_binh_dam,
            yen_bai_station,
            vu_quang_station,
            son_tay,
            hanoi,
        )
        self._problem.add_action(update_state_network)

        advance_day = self._define_advance_day_action(
            hoa_binh_dam,
            son_tay,
            yen_bai_station,
            vu_quang_station,
            input_hoa_binh,
            hanoi
        )
        self._problem.add_action(advance_day)

    # Main actions of the simplified problem

    # Action for the opening of the gates
    def _define_open_gate_action(self, action_name: str, gate_release: str, input_release=None, hoa_binh_dam=None, multiplier=1) -> InstantaneousAction:
        open_gate = InstantaneousAction(action_name, d=self._user_types["Day"])
        d = open_gate.parameter("d") 
        open_gate.add_precondition(Not(self._problem.fluent("evaluated_network")))
        if input_release is not None:
            open_gate.add_increase_effect(self._problem.fluent(gate_release)(hoa_binh_dam), input_release)
        # Add other preconditions and effects as needed
        # open_gate.add_increase_effect(
        #         self._problem.fluent("objective"),
        #         LAMBDA_R*input_release
        #         )
        
        open_gate.add_increase_effect(
            self._problem.fluent("total_release")(hoa_binh_dam),
            input_release
        )
        
        open_gate.add_increase_effect(
                self._problem.fluent("objective"),
                LAMBDA_R*input_release*multiplier
                )
        
        # # check if the current day is active
        # open_gate.add_precondition(
        #     self._problem.fluent("active")(d)
        # )
        
        # # check if the day is a control day
        # open_gate.add_precondition(
        #     self._problem.fluent("control")(d)
        # )

        return open_gate

    def _define_open_turbine_action(self, hoa_binh_dam):
        open_turbine_gate: InstantaneousAction = self._define_open_gate_action(
            "open_gate", 
            "release", 
            INPUT_TURBINE, 
            hoa_binh_dam
        )
        # Preconditions for the action: the release is less than the maximum release
        open_turbine_gate.add_precondition(
            LT(
                self._problem.fluent("release")(hoa_binh_dam),
                self._problem.fluent("maximum_turbine_release")(hoa_binh_dam),
            )
        )        
        return open_turbine_gate

    def _define_open_bottom_gates_action(self, hoa_binh_dam):
        open_bottom_gate: InstantaneousAction = self._define_open_gate_action(
            "open_bottom_gate", 
            "release_bottom", 
            INPUT_BOTTOM_RELEASE, 
            hoa_binh_dam, 
            BOTTOM_GATE_MULTIPLIER
        )
        open_bottom_gate.add_precondition(
                GE(
                    self._problem.fluent("release")(hoa_binh_dam),
                    self._problem.fluent("maximum_turbine_release")(hoa_binh_dam),
                )
            )
        #TODO: check if this is correct and maybe don't use raw numbers
        open_bottom_gate.add_precondition(
            LT(
                self._problem.fluent("release_bottom")(hoa_binh_dam),
                self._problem.fluent("max_bottom_release")(hoa_binh_dam),
            )
        )
        return open_bottom_gate

    def _define_open_spillways_action(self, hoa_binh_dam):

        open_spillway_gate: InstantaneousAction = self._define_open_gate_action(
            "open_spillway_gate", 
            "release_spillways", 
            INPUT_SPILLWAY_RELEASE, 
            hoa_binh_dam
        )
        #TODO: as before, check if this is correct and maybe don't use raw numbers
        # Preconditions for the action
        open_spillway_gate.add_precondition(
            LT(
                self._problem.fluent("release_spillways")(hoa_binh_dam),
                self._problem.fluent("max_spillways_release")(hoa_binh_dam),
            )
        )
        open_spillway_gate.add_precondition(
            GE(
                self._problem.fluent("release_bottom")(hoa_binh_dam),
                self._problem.fluent("max_bottom_release")(hoa_binh_dam)
            )
        )        
        return open_spillway_gate

    def _define_update_state_network(self, hoa_binh_dam, yen_bai_station, vu_quang_station, son_tay, hanoi):
        update_state_network: InstantaneousAction = InstantaneousAction(
            "update_state_network", d=self._user_types["Day"]
        )
        
        d: Parameter = update_state_network.parameter("d")
        input_hoa_binh = self._problem.object("input_hoa_binh")

        input_hoa_binh = self._problem.fluent("flow")(input_hoa_binh) + self._problem.fluent("flow_beta")(input_hoa_binh, d)

        update_state_network.add_precondition(self._problem.fluent("active")(d))
        update_state_network.add_precondition(Not(self._problem.fluent("evaluated_network")))
        
        # min release precondiction
        update_state_network.add_precondition(
            GE(
                self._problem.fluent("release")(hoa_binh_dam),
                self._problem.fluent("min_release")(hoa_binh_dam, d),
            )
        )

        # calculate the total outflow from the dam

        outflow_expression = (
            self._problem.fluent("release")(hoa_binh_dam)
            + self._problem.fluent("release_bottom")(hoa_binh_dam)
            + self._problem.fluent("release_spillways")(hoa_binh_dam)
        )

        # update_state_network = self._add_update_state_network_action_safety_preconditions(
        #     update_state_network, hoa_binh_dam, d, outflow_expression
        # )

        # Flow at Son Tay but using only the lagged flow
        flow_son_tay = (
            self.FLOW_ALPHA_HOA_BINH_DAM_SON_TAY
            * self._problem.fluent("lagged_flow")(hoa_binh_dam)
            + self.FLOW_ALPHA_YEN_BAI_STATION_SON_TAY
            * self._problem.fluent("lagged_flow")(yen_bai_station)
            + self.FLOW_ALPHA_VU_QUANG_STATION_SON_TAY
            * self._problem.fluent("lagged_flow")(vu_quang_station)
        )

        update_state_network = self._add_effect_flow_son_tay_level_hanoi(
            update_state_network, flow_son_tay, son_tay, hanoi
        )

        hydropower = self._compute_hydropower(outflow_expression, hoa_binh_dam, d)

        update_state_network.add_effect(
            self._problem.fluent("hydropower_production")(hoa_binh_dam), hydropower
        )
        
        update_state_network.add_decrease_effect(
            self._problem.fluent("storage")(hoa_binh_dam),
            outflow_expression * 0.0864,
        )

        update_state_network.add_effect(self._problem.fluent("evaluated_network"), True)

        return update_state_network


    def _add_update_state_network_action_safety_preconditions(
        self,
        visit_dam: InstantaneousAction,
        n1: Parameter,
        d: Parameter,
        outflow_expression: FNode = 0
    ) -> InstantaneousAction:
        
        # max_level_dam = self._problem.fluent("max_level_dam")(d)
        # max_storage_hoa_binh_dam = (max_level_dam - 60.79) / 5.79e-3
        
        # Checking if the storage is fine
        visit_dam.add_precondition(
            GT(
                self._problem.fluent("storage")(n1) - (outflow_expression * 0.0864),
                MIN_STORAGE_HOA_BINH_DAM,
            )
        )

        # for the maximum storage we use the one from the policy
        visit_dam.add_precondition(
            LT(
                self._problem.fluent("storage")(n1) - (outflow_expression * 0.0864),
                MAX_STORAGE_HOA_BINH_DAM,
            )
        )

        return visit_dam

    #TODO: Check if this is correct
    def _compute_hydropower(
        self,
        outflow_expression: Union[FNode, float],
        n1: Parameter,
        d: Parameter
    ):
        h_up = LEVEL_LOSS_DAM * self._problem.fluent(
            "storage"
        )(n1) + LEVEL_CONSTANT_HOA_BINH_DAM

        if isinstance(outflow_expression, FNode):
            power_function = NumberHelper.fluents_power_elevation
            release = self._problem.fluent("release")(n1)
        else:
            power_function = pow
            release = outflow_expression

        h_do = (
            3.6636e-12 * power_function(outflow_expression, 3)
            + 1.3637e-7 * power_function(outflow_expression, 2)
            + 2.0877e-3 * outflow_expression
            + 11.66
        )
        return self._problem.fluent("efficiency")(n1) * release * (h_up - h_do)
    
    def _add_effect_flow_son_tay_level_hanoi(
        self,
        visit_dam: InstantaneousAction,
        flow_son_tay: FNode,
        son_tay: Object,
        hanoi: Object,
    ):
        d = visit_dam.parameter("d")
        flow_exp_hanoi = (
            self.FLOW_ALPHA_SON_TAY_HANOI
            * (flow_son_tay + self.FLOW_GAMMA_SON_TAY)
        )
        visit_dam.add_effect(
            self._problem.fluent("flow")(son_tay), flow_son_tay
        )
        visit_dam.add_effect(
            self._problem.fluent("level")(hanoi),
            (
                self.LEVEL_CONSTANT_HANOI
                + self.LEVEL_LOSS3_HANOI
                * NumberHelper.fluents_power_elevation(flow_exp_hanoi, 3)
                + self.LEVEL_LOSS2_HANOI
                * NumberHelper.fluents_power_elevation(flow_exp_hanoi, 2)
                + self.LEVEL_LOSS1_HANOI * flow_exp_hanoi
            ),
        )

        return visit_dam

    def _define_advance_day_action(self,hoa_binh_dam, son_tay, yen_bai_station, vu_quang_station, input_hoa_binh, hanoi):
        advance_day = InstantaneousAction(
            "advance_day",
            d1=self._user_types["Day"],
            d2=self._user_types["Day"],
        )
        d1 = advance_day.parameter("d1")
        d2 = advance_day.parameter("d2")

        # Basic preconditions for the action
        advance_day.add_precondition(self._problem.fluent("active")(d1))
        advance_day.add_precondition(self._problem.fluent("next_step")(d1, d2))
        advance_day.add_precondition(self._problem.fluent("evaluated_network"))

        outflow_expression = (
            self._problem.fluent("release")(hoa_binh_dam)
            + self._problem.fluent("release_bottom")(hoa_binh_dam)
            + self._problem.fluent("release_spillways")(hoa_binh_dam)
        )
        
        # Check if the level of Hanoi is fine
        advance_day.add_precondition(
            MIN_LEVEL_HANOI
            < self._problem.fluent("level")(hanoi)
        )
        advance_day.add_precondition(
            MAX_LEVEL_HANOI
            > self._problem.fluent("level")(hanoi)
        )

        # Check if the demand is satisfied
        advance_day.add_precondition(
            (
                self._problem.fluent("agricultural_demand")(d1)
                + SWI_DEMAND
            )
            < (
                self._problem.fluent("flow")(son_tay)
                + self.FLOW_GAMMA_SON_TAY
            )
        )
        
        # check on the storage of the dam
        advance_day.add_precondition(
            LT(
                self._problem.fluent("storage")(hoa_binh_dam),
                MAX_STORAGE_HOA_BINH_DAM
            )
        )
        advance_day.add_precondition(
            GT(
                self._problem.fluent("storage")(hoa_binh_dam),
                MIN_STORAGE_HOA_BINH_DAM
            )
        )
        
        # advance_day.add_precondition(
        #     LT(
        #         self._problem.fluent("objective"),
        #         OBJECTIVE_THRESHOLD
        #     )
        # )
        
        # advance_day.add_precondition(
        #         self._problem.fluent("hydropower_production")(hoa_binh_dam) 
        #         > self._problem.fluent("energy_demand")(d1)
        #     )

        # Setting for the next day
        advance_day.add_effect(self._problem.fluent("active")(d1), False)
        advance_day.add_effect(self._problem.fluent("active")(d2), True)
        advance_day.add_effect(self._problem.fluent("evaluated_network"), False)
        advance_day.add_effect(self._problem.fluent("release")(hoa_binh_dam), 295)
        advance_day.add_effect(self._problem.fluent("release_bottom")(hoa_binh_dam), 0)
        advance_day.add_effect(
            self._problem.fluent("release_spillways")(hoa_binh_dam), 0
        )
        
        advance_day.add_increase_effect(
            self._problem.fluent("total_production")(hoa_binh_dam),
            self._problem.fluent("hydropower_production")(hoa_binh_dam)
        )

        self._define_evaluate_max_turbine_release_preconditions_and_effects(advance_day)

        # updating the storage of the dam for the next day
        advance_day.add_increase_effect(
            self._problem.fluent("storage")(hoa_binh_dam),
            (
                (
                    (
                        self._problem.fluent("flow")(input_hoa_binh)
                        + self._problem.fluent("flow_beta")(input_hoa_binh, d2)
                    )
                    * FLOW_ALPHA_INPUT_HOA_BINH_HOA_BIN_DAM
                )
                * 0.0864
            ),
        )

        # updaing tha maximun spillways releases for the next day
        advance_day.add_effect(
            self._problem.fluent("max_spillways_release")(hoa_binh_dam),
            6 * (
                    -0.00000000745
                    * self._problem.fluent("storage")(hoa_binh_dam)
                    * self._problem.fluent("storage")(hoa_binh_dam)
                    * self._problem.fluent("storage")(hoa_binh_dam)
                    + 0.0003182
                    * self._problem.fluent("storage")(hoa_binh_dam)
                    * self._problem.fluent("storage")(hoa_binh_dam)
                    - 3.1398 * self._problem.fluent("storage")(hoa_binh_dam)
                    + 8940.6
                ),
        )

        # updating the maximum bottom release for the next day
        advance_day.add_effect(
            self._problem.fluent("max_bottom_release")(hoa_binh_dam),
            12 * (
                    0.000000002831
                    * self._problem.fluent("storage")(hoa_binh_dam)
                    * self._problem.fluent("storage")(hoa_binh_dam)
                    * self._problem.fluent("storage")(hoa_binh_dam)
                    - 0.00006996
                    * self._problem.fluent("storage")(hoa_binh_dam)
                    * self._problem.fluent("storage")(hoa_binh_dam)
                    + 0.702 * self._problem.fluent("storage")(hoa_binh_dam)
                    - 920.44
                ),
        )



        # Assigning the lagged flow for the next day
        advance_day.add_effect(
            self._problem.fluent("lagged_flow")(hoa_binh_dam), outflow_expression
        )
        advance_day.add_effect(
            self._problem.fluent("lagged_flow")(yen_bai_station),
            (
                self._problem.fluent("flow")(yen_bai_station)
                + self._problem.fluent("flow_beta")(yen_bai_station, d1)
            ),
        )
        advance_day.add_effect(
            self._problem.fluent("lagged_flow")(vu_quang_station),
            (
                self._problem.fluent("flow")(vu_quang_station)
                + self._problem.fluent("flow_beta")(vu_quang_station, d1)
            ),
        )        
        # Setup the efficiency_aprx for the next day
        
        # Add a default assignment first
        # advance_day.add_effect(
        #     self._problem.fluent("efficiency_aprx"),
        #     EFFICIENCY_LOW,
        #     condition=LT(self._problem.fluent("storage")(hoa_binh_dam), LIV_EFFICIENCY_LOW)
        # )

        # advance_day.add_effect(
        #     self._problem.fluent("efficiency_aprx"),
        #     EFFICIENCY_MEDIUM,
        #     condition=And(
        #         GE(self._problem.fluent("storage")(hoa_binh_dam), LIV_EFFICIENCY_LOW),
        #         LT(self._problem.fluent("storage")(hoa_binh_dam), LIV_EFFICIENCY_MEDIUM)
        #     )
        # )

        # advance_day.add_effect(
        #     self._problem.fluent("efficiency_aprx"),
        #     EFFICIENCY_HIGH,
        #     condition=GE(self._problem.fluent("storage")(hoa_binh_dam), LIV_EFFICIENCY_MEDIUM)
        # )
        
        # if next day is a control day we reset the releases
        # advance_day.add_effect(
        #     self._problem.fluent("release")(hoa_binh_dam),
        #     295,
        #     condition=self._problem.fluent("control")(d2)
        # )
        # advance_day.add_effect(
        #     self._problem.fluent("release_bottom")(hoa_binh_dam),
        #     0,
        #     condition=self._problem.fluent("control")(d2)
        # )
        # advance_day.add_effect(
        #     self._problem.fluent("release_spillways")(hoa_binh_dam),
        #     0,
        #     condition=self._problem.fluent("control")(d2)
        # )
        
        
        return advance_day

    def _define_evaluate_max_turbine_release_preconditions_and_effects(
        self, action: InstantaneousAction
    ):
        hoabin = self.problem.object("hoa_binh_dam")

        action.add_effect(
            self._problem.fluent("maximum_turbine_release")(hoabin),
            self._problem.fluent("storage")(hoabin) * 0.12538 + 1603.1,
            LE(self._problem.fluent("storage")(hoabin), 4444.1),
        )
        action.add_effect(
            self._problem.fluent("maximum_turbine_release")(hoabin),
            self._problem.fluent("storage")(hoabin) * 0.06959 + 1851.6,
            And(
                GT(self._problem.fluent("storage")(hoabin), 4444.1),
                LE(self._problem.fluent("storage")(hoabin), 7306),
            ),
        )
        action.add_effect(
            self._problem.fluent("maximum_turbine_release")(hoabin),
            2360,
            GT(self._problem.fluent("storage")(hoabin), 7306),
        )

    # Function to add the time steps to the problem
    def _add_time_step(self, data, lower_bound, upper_bound):
        for i in range(lower_bound, upper_bound):
            if i < len(data):
                date_str = data.Date[i].strftime("%Y_%m_%d")
                self._problem.add_object(
                    Object(f"day_{date_str}", self._user_types["Day"])
                )
        return (
            list(self._problem.objects(self._user_types["Day"]))
        )

    def calcola_change_points(
        self,
        daily_data: pd.DataFrame, 
        starting_date: pd.Timestamp, 
        ending_date: pd.Timestamp, 
        signal_type: str = "afflussi_domanda",
        weighs: list = [0.4, 0.3, 0.1, 0.2],
        penalty: float = 5, 
        min_size: int = 0) -> list:
        """
        Calcola i change-points su un segnale derivato da afflussi e domanda.

        Args:
            daily_avg (pd.DataFrame): DataFrame contenente le colonne necessarie e la colonna 'Date' (datetime).
            signal_type (str): Tipo di segnale da usare. Opzioni: 'afflussi_domanda' o 'pesato'.
            penalty (float): Penalità da usare in ruptures.Pelt.
            min_size (int): Dimensione minima dei segmenti per ruptures.Pelt.

        Returns:
            list: Lista di datetime dei giorni di controllo (inclusi primo e ultimo).
        """
        import ruptures as rpt
        from sklearn.preprocessing import MinMaxScaler

        df = daily_data.copy()

        # Filtra i dati di interesse
        df = df[(df['Date'] >= starting_date) & (df['Date'] <= ending_date)]

        # Calcola il segnale desiderato
        if signal_type == "afflussi_domanda":
            df['signal'] = (df["Input_Hoa_Binh"] + df["Yen_Bai"] + df["Vu_Quang"]) - (df["Demand"] + 500)
        elif signal_type == "pesato":
            cols = ["Input_Hoa_Binh", "Yen_Bai", "Vu_Quang", "Demand"]
            scaler = MinMaxScaler()
            df_norm = pd.DataFrame(scaler.fit_transform(df[cols]), columns=cols)
            df['signal'] = sum(w * df_norm[col] for w, col in zip(weighs, cols))
        else:
            raise ValueError("signal_type deve essere 'afflussi_domanda' o 'pesato'.")

        # Change-point detection
        signal = df["signal"].values
        algo = rpt.Dynp(model="l2", min_size=1, jump=1).fit(signal)
        # n_bkp = int(np.ceil(len(signal) / 3))  # Numero di breakpoints da cercare
        n_bkp = 60
        print(f"Numero di breakpoints da cercare: {n_bkp}")
        change_points = algo.predict(n_bkps=n_bkp)[:-1]
        cp_dates = df.loc[df.index[change_points], "Date"].sort_values().tolist()

        # Aggiungi inizio e fine se non già presenti
        if df["Date"].min() not in cp_dates:
            cp_dates.insert(0, df["Date"].min())
        if df["Date"].max() not in cp_dates:
            cp_dates.append(df["Date"].max())
            
        # max_days = 3
        # final_days = [cp_dates[0]]

        # for i in range(1, len(cp_dates)):
        #     prev = final_days[-1]
        #     curr = cp_dates[i]

        #     delta = (curr - prev).days
        #     if delta <= max_days:
        #         final_days.append(curr)
        #     else:
        #         # Quanti controlli intermedi servono?
        #         n_insert = int(np.floor(delta / max_days))

        #         # Inserisci punti equispaziati tra prev e curr
        #         for j in range(1, n_insert + 1):
        #             new_day = prev + pd.Timedelta(days=j * delta // (n_insert + 1))
        #             final_days.append(new_day)

        #         final_days.append(curr)


        # cp_dates = final_days

        return cp_dates

    # def _define_control_days(self, time_steps, lower_bound, upper_bound, data):
    #     # days = np.linspace(lower_bound, upper_bound-1, n_control_days, dtype=int)
    #     control_days = self.calcola_change_points(
    #         data,
    #         starting_date=data['Date'].iloc[lower_bound],
    #         ending_date=data['Date'].iloc[upper_bound - 1],
    #         signal_type="afflussi_domanda",
    #         penalty=0.0001,
    #         min_size=0
    #     )
    #     # trova gli indici delle date
    #     indexes = data['Date'].searchsorted(control_days)
    #     for i in indexes:
    #         self._problem.set_initial_value(
    #             self._problem.fluent("control")(time_steps[i]), True
    #         )

    #     # for i in range(len(time_steps)):
    #     #     if i in days:
    #     #         self._problem.set_initial_value(
    #     #             self._problem.fluent("control")(time_steps[i]), True
    #     #         )
    
    def create_problem(
        self, data: pd.DataFrame, historical_data: pd.DataFrame, lower_bound, upper_bound, starting_date, ending_date, problem_out_dir, inverse: bool = False, n_control_days: int = 0
    ) -> Problem:
        
        self._problem_path = problem_out_dir

        # clone the original problem
        self._problem.name = f"SProblem_{starting_date.date()}_end_{ending_date.date()}"

        # add the time_steps and nodes
        time_steps = self._add_time_step(data, lower_bound, upper_bound)
        
        

        # add days predicates
        self._problem.set_initial_value(
            self._problem.fluent("active")(time_steps[0]), True
        )
        
        # set the min release for the first day
        self._problem.set_initial_value(
            self._problem.fluent("release")(
                self._problem.object("hoa_binh_dam")
            ),
            295,
        )

        self._define_time_step_sequence(len(data))

        # define the control days
        # if n_control_days == 0:
        #     n_control_days = len(time_steps)
            
        # self._define_control_days(time_steps, lower_bound, upper_bound, data)
        
        # add the flow constant
        time_steps = list(self._problem.objects(self._user_types["Day"]))

        # add penstocks max release
        storage = (
            1.72e2 * data["H_Up (m)"][lower_bound] - 10382.96
        )  # (data['H_Up (m)'][lower_bound]/V0)**eta+h0

        #TODO: add this function and check if its needed
        max_penstocks_release = self._compute_maximum_penstocks_release(storage)

        self._problem.set_initial_value(
            self._problem.fluent("maximum_turbine_release")(
                self._problem.object("hoa_binh_dam")
            ),
            max_penstocks_release,
        )

        # add demands functions
        for j in range(lower_bound, upper_bound):
            if j < len(data):
                self._problem.set_initial_value(
                    self._problem.fluent("agricultural_demand")(
                        time_steps[j]
                    ),
                    data.Demand[j],
                )
                
                # self._problem.set_initial_value(
                #     self._problem.fluent("energy_demand")(
                #         time_steps[j]
                #     ),
                #     data.Energy_demand[j],
                # )
                
                # Min flow for the dam
                self._problem.set_initial_value(
                    self._problem.fluent("min_release")(
                        self._problem.object("hoa_binh_dam"), time_steps[j]
                    ),
                    214,
                )

                self._problem.set_initial_value(
                    self._problem.fluent("flow_beta")(
                        self._problem.object("input_hoa_binh"), time_steps[j]
                    ),
                    data.Input_Hoa_Binh[j],
                )
                self._problem.set_initial_value(
                    self._problem.fluent("flow_beta")(
                        self._problem.object("yen_bai_station"), time_steps[j]
                    ),
                    data.Yen_Bai[j],
                )
                self._problem.set_initial_value(
                    self._problem.fluent("flow_beta")(
                        self._problem.object("vu_quang_station"), time_steps[j]
                    ),
                    data.Vu_Quang[j],
                )
            else:
                break

        initial_storage = 1.72e2 * data["H_Up (m)"][lower_bound] - 10382.96
        self._problem.set_initial_value(
            self._problem.fluent("storage")(self._problem.object("hoa_binh_dam")),
            initial_storage,
        )

        # add dams efficiency
        self._problem.set_initial_value(
            self._problem.fluent("efficiency")(self._problem.object("hoa_binh_dam")),
            0.2049,
        )
        
        # # add the starting efficiency_aprx
        # self._define_initial_aprx_efficiency(
        #     self._problem.fluent("storage")(self._problem.object("hoa_binh_dam")
        #     )
        # )

        # lagged flows
        self._problem.set_initial_value(
            self._problem.fluent("lagged_flow")(
                self._problem.object("yen_bai_station")
            ),
            historical_data['Yen_Bai'].iloc[-1]
        )
        self._problem.set_initial_value(
            self._problem.fluent("lagged_flow")(
                self._problem.object("vu_quang_station")
            ),
            historical_data['Vu_Quang'].iloc[-1]
        )
            
        self._problem.set_initial_value(
            self._problem.fluent("lagged_flow")(
                self._problem.object("hoa_binh_dam")
            ),
            historical_data['Qtu_(m3/s)'].iloc[-1] +
            historical_data['Qbot_(m3/s)'].iloc[-1] +
            historical_data['Qspill_(m3/s)'].iloc[-1],
        )

        # minimize objective function
        # self._problem.add_quality_metric(
        #     MinimizeActionCosts({
        #         self._problem.action("open_gate"): 147.5, 
        #         self._problem.action("open_bottom_gate"): 1833, 
        #         self._problem.action("open_spillway_gate"): 2350
        #     })
        # )
        
        
        # self._problem.add_quality_metric(
        #     MinimizeExpressionOnFinalState(self._problem.fluent("objective"))
        # )

        self._problem.set_initial_value(
            self._problem.fluent("max_bottom_release")(self._problem.object("hoa_binh_dam")),
                12 * (
                    0.000000002831
                    * initial_storage
                    * initial_storage
                    * initial_storage
                    - 0.00006996
                    * initial_storage
                    * initial_storage
                    + 0.702 * initial_storage
                    - 920.44
                ),
        )

        self._problem.set_initial_value(
            self._problem.fluent("max_spillways_release")(self._problem.object("hoa_binh_dam")),
                6 * (
                    -0.00000000745
                    * initial_storage
                    * initial_storage
                    * initial_storage
                    + 0.0003182
                    * initial_storage
                    * initial_storage
                    - 3.1398 * initial_storage
                    + 8940.6
                ),
            )

        # TODO: change this with a new separate folder
        # self._problem_path = os.path.join(
        #     self._problem_path,
        #     "simple",
        # )

        time_steps = list(self._problem.objects(self._user_types["Day"]))

        return self._problem

    def _define_initial_aprx_efficiency(self, starting_storage: float) -> float:
        # add the starting efficiency_aprx
        if starting_storage < LIV_EFFICIENCY_LOW:
            starting_value = EFFICIENCY_LOW
        elif starting_storage < LIV_EFFICIENCY_MEDIUM:
            starting_value = EFFICIENCY_MEDIUM
        else:
            starting_value = EFFICIENCY_HIGH
            
        self._problem.set_initial_value(
            self._problem.fluent("efficiency_aprx"),
            starting_value
        )
        
    def _define_time_step_sequence(self, data_length: int):
        time_steps = list(self._problem.objects(self._user_types["Day"]))
        for t1, t2 in zip(time_steps[:-1], time_steps[1:data_length]):
            self._problem.set_initial_value(
            self._problem.fluent("next_step")(t1, t2), True
        )

        # add goals
        self._problem.add_goal(self._problem.fluent("active")(time_steps[-1]))
        self._problem.add_goal(
            GT(
                self._problem.fluent("storage")(self._problem.object("hoa_binh_dam")),
                # min_final_dam_storage
                MIN_STORAGE_HOA_BINH_DAM
            )
        )
        self._problem.add_goal(
            LT(
                self._problem.fluent("storage")(self._problem.object("hoa_binh_dam")),
                # max_final_dam_storage
                MAX_STORAGE_HOA_BINH_DAM
            )
        )
        
        self._problem.add_goal(
            GT(
                self._problem.fluent("total_production")(
                    self._problem.object("hoa_binh_dam")
                ),
                MIN_TOTAL_PRODUCTION
            )
        )
        # condition used in the anytime mode
        # self._problem.add_goal(
        #     LT(
        #         self._problem.fluent("objective"),
        #         OBJECTIVE_THRESHOLD
        #     )
        # )

    #TODO: check if this is correct
    def _compute_maximum_penstocks_release(self, storage) -> float:
        # 0.12538s + 1603.1 if s <= 4441.4
        # 0.06959s + 1851.6 if 4441.4 < s <= 7306
        # 2360 otherwise
        if storage <= 4441.4:
            return 0.12538 * storage + 1603.1
        elif storage > 4441.4 and storage <= 7306:
            return 0.06959 * storage + 1851.6

        return 2360

    @property
    def name(self) -> str:
        return self._problem.name

    @property
    def problem_path(self) -> str:
        return self._problem_path

    @property
    def problem(self):
        return self._problem

    @property
    def problem(self):
        return self._problem

    @property
    def user_types(self):
        return self._user_types

    @problem_path.setter
    def problem_path(self, new_path):
        self._problem_path = new_path

class SimpleRedRiverProblems(object):
    """RedRiverProblems class build multiple RedRiverProblem"""

    _problem : SimpleProblemConstructor
    _n_days: int
    _data: pd.DataFrame
    _historical_data: pd.DataFrame
    _problem_data: pd.DataFrame

    def __init__(
        self,
        starting_date,
        ending_date,
        data_path: str = None,
        historical_data_path: str = None,
        problem_data_path: str = None,
        n_days: int = None,

    ):
        super(SimpleRedRiverProblems, self).__init__()
        self._starting_date = starting_date
        self._ending_date = ending_date
        self._n_days = n_days
        self._data_path = data_path
        self._historical_data_path = historical_data_path
        self._problem_data_path = problem_data_path
        self._historical_data = self._load_historical_data(self._historical_data_path, starting_date)
        self._problem_data = self._load_problems_data(self._problem_data_path)
        
    def _load_problems_data(self, data_path):
        data = pd.read_csv(data_path)
        data["Date"] = data.apply(lambda row: self._add_year_to_dates(row), axis=1)

        return data

    
    def _load_historical_data(self, hist_data_path, starting_data):
        data = pd.read_csv(hist_data_path)
        data["Date"] = data.apply(lambda row: self._add_year_to_dates(row), axis=1)
        # taking the data only before the starting date
        if starting_data < data['Date'].iloc[-1]:
            data = data[data['Date'] < starting_data]
        else:
            # Align starting_date with the last available date in the data
            starting_data = datetime(
                year=data['Date'].iloc[-1].year,
                month=starting_data.month,
                day=starting_data.day
            )
            if starting_data - pd.Timedelta(days=1) > data['Date'].iloc[-1]:
                starting_data = starting_data.replace(year=starting_data.year - 1)

        # Lagged flows
        data["lagged_flow_YB"] = data["Yen_Bai"].shift(+1)
        data["lagged_flow_VQ"] = data["Vu_Quang"].shift(+1)
        data["lagged_flow_YB"].fillna(data["lagged_flow_YB"].mean(), inplace=True)
        data["lagged_flow_VQ"].fillna(data["lagged_flow_VQ"].mean(), inplace=True)
        data[
            ["Lagged_Qtu_(m3/s)", "Lagged_Qbot_(m3/s)", "Lagged_Qspill_(m3/s)"]
        ] = data[["Qtu_(m3/s)", "Qbot_(m3/s)", "Qspill_(m3/s)"]].shift(+1)
        data["lagged_flow_ST"] = data["Q_Sơn Tây"].shift(-1)
        data["lagged_flow_HN"] = data["Q_Hà Nội"].shift(-1)

        print(data.tail())
        return data
        
    def create_problem(self, inverse: bool = False, n_control_days: int = 0, problem_out_dir: str = None):
        starting_date = self._starting_date
        ending_date = self._ending_date
        constructor_class = SimpleProblemConstructor
        self._create_daily_problems(
            problem_constructor_class=constructor_class,
            starting_date=starting_date,
            ending_date=ending_date,
            inverse=inverse,
            n_control_days=n_control_days,
            problem_out_dir=problem_out_dir
        )
        

    def _create_daily_problems(
        self,
        problem_constructor_class,
        starting_date,
        ending_date,
        inverse: bool = False,
        n_control_days: int = 0,
        problem_out_dir: str = None
    ) -> list:
        # print(data.columns)
        # interval_data = data[
        #     (data.Date >= starting_date) & (data.Date <= ending_date)
        # ].copy()
        coefficients_dict = coefficients_evaluation(starting_date=starting_date, data=self._historical_data)

        n_days = self._n_days
        for i in range(0, len(self._problem_data), n_days):
            problem_data = self._problem_data.iloc[i : i + n_days]
            historical_data = self._historical_data

            problem_data = problem_data.reset_index(drop=True)
            if len(problem_data) > 0:
                problem_constructor: SimpleProblemConstructor = problem_constructor_class(coefficients_dict=coefficients_dict)
                problem_constructor.create_problem(
                    problem_data, historical_data, 0, n_days, starting_date=starting_date, ending_date=ending_date, inverse=inverse, n_control_days=n_control_days, problem_out_dir=problem_out_dir
                )
                self._problem = problem_constructor
    
    def _add_year_to_dates(self, row):
            try:
                full_date_str = f"{row['Date']} {2024 + (row.name//365+1)}"
                return pd.to_datetime(full_date_str, format="%d %b %Y")
            except ValueError:
                return pd.to_datetime(row["Date"])

    @property
    def problem(self):
        return self._problem