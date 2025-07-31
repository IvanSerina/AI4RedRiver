(define (domain sproblem_2077_09_30_end_2078_05_31-domain)
  (:requirements :strips :typing :negative-preconditions :numeric-fluents :conditional-effects)
  (:types
    node day - object
    dam regular navigability_node - node
  )
  (:constants
    hoa_binh_dam - dam
    son_tay - node
    yen_bai_station input_hoa_binh vu_quang_station - regular
    hanoi - navigability_node
  )
  (:predicates
    (active ?d - day)
    (next_step ?d1 - day ?d2 - day)
    (evaluated_network)
  )
  (:functions
    (flow_beta ?n - regular ?d - day)
    (flow ?n_0 - node)
    (release ?n_1 - dam)
    (release_bottom ?n_1 - dam)
    (release_spillways ?n_1 - dam)
    (total_release ?n_1 - dam)
    (hydropower_production ?n_1 - dam)
    (storage ?n_1 - dam)
    (efficiency ?n_1 - dam)
    (maximum_turbine_release ?n_1 - dam)
    (level ?n_2 - navigability_node)
    (max_level_dam ?d - day)
    (min_level_dam ?d - day)
    (lagged_flow ?n_0 - node)
    (agricultural_demand ?d - day)
    (max_bottom_release ?n_1 - dam)
    (max_spillways_release ?n_1 - dam)
    (objective)
  )
  (:action open_gate
    :parameters ()
    :precondition (and (not (evaluated_network)) (< (release hoa_binh_dam) (maximum_turbine_release hoa_binh_dam)))
    :effect (and (increase (release hoa_binh_dam) 147.5) (increase (total_release hoa_binh_dam) 147.5) (increase (objective) 147.5))
  )
  (:action open_bottom_gate
    :parameters ()
    :precondition (and (not (evaluated_network)) (<= (maximum_turbine_release hoa_binh_dam) (release hoa_binh_dam)) (< (release_bottom hoa_binh_dam) (max_bottom_release hoa_binh_dam)))
    :effect (and (increase (release_bottom hoa_binh_dam) 1833) (increase (total_release hoa_binh_dam) 1833) (increase (objective) 5499))
  )
  (:action open_spillway_gate
    :parameters ()
    :precondition (and (not (evaluated_network)) (< (release_spillways hoa_binh_dam) (max_spillways_release hoa_binh_dam)) (<= (max_bottom_release hoa_binh_dam) (release_bottom hoa_binh_dam)))
    :effect (and (increase (release_spillways hoa_binh_dam) 2350) (increase (total_release hoa_binh_dam) 2350) (increase (objective) 2350))
  )
  (:action update_state_network
    :parameters ( ?d - day)
    :precondition (and (active ?d) (not (evaluated_network)) (< 3317.789292 (- (storage hoa_binh_dam) (* 0.0864 (+ (release_spillways hoa_binh_dam) (+ (release_bottom hoa_binh_dam) (release hoa_binh_dam)))))) (< (- (storage hoa_binh_dam) (* 0.0864 (+ (release_spillways hoa_binh_dam) (+ (release_bottom hoa_binh_dam) (release hoa_binh_dam))))) 9708.117444))
    :effect (and (assign
        (flow son_tay)
        (+ (* 0.9505596543 (lagged_flow vu_quang_station)) (+ (lagged_flow yen_bai_station) (* 0.887092249 (lagged_flow hoa_binh_dam))))) (assign
        (level hanoi)
        (+ 1.324336612 (+ (* 0.001242272726 (+ 0.9512619061 (+ (* 0.9505596543 (lagged_flow vu_quang_station)) (+ (lagged_flow yen_bai_station) (* 0.887092249 (lagged_flow hoa_binh_dam)))))) (+ (* -0.00000005869498050000 (* (+ 0.9512619061 (+ (* 0.9505596543 (lagged_flow vu_quang_station)) (+ (lagged_flow yen_bai_station) (* 0.887092249 (lagged_flow hoa_binh_dam))))) (+ 0.9512619061 (+ (* 0.9505596543 (lagged_flow vu_quang_station)) (+ (lagged_flow yen_bai_station) (* 0.887092249 (lagged_flow hoa_binh_dam))))))) (* 0.00000000000110631367 (* (+ 0.9512619061 (+ (* 0.9505596543 (lagged_flow vu_quang_station)) (+ (lagged_flow yen_bai_station) (* 0.887092249 (lagged_flow hoa_binh_dam))))) (* (+ 0.9512619061 (+ (* 0.9505596543 (lagged_flow vu_quang_station)) (+ (lagged_flow yen_bai_station) (* 0.887092249 (lagged_flow hoa_binh_dam))))) (+ 0.9512619061 (+ (* 0.9505596543 (lagged_flow vu_quang_station)) (+ (lagged_flow yen_bai_station) (* 0.887092249 (lagged_flow hoa_binh_dam)))))))))))) (assign
        (hydropower_production hoa_binh_dam)
        (* (- (+ 60.79 (* 0.00579 (storage hoa_binh_dam))) (+ 11.66 (+ (* 0.0020877 (+ (release_spillways hoa_binh_dam) (+ (release_bottom hoa_binh_dam) (release hoa_binh_dam)))) (+ (* 0.00000013637000000000 (* (+ (release_spillways hoa_binh_dam) (+ (release_bottom hoa_binh_dam) (release hoa_binh_dam))) (+ (release_spillways hoa_binh_dam) (+ (release_bottom hoa_binh_dam) (release hoa_binh_dam))))) (* 0.00000000000366360000 (* (+ (release_spillways hoa_binh_dam) (+ (release_bottom hoa_binh_dam) (release hoa_binh_dam))) (* (+ (release_spillways hoa_binh_dam) (+ (release_bottom hoa_binh_dam) (release hoa_binh_dam))) (+ (release_spillways hoa_binh_dam) (+ (release_bottom hoa_binh_dam) (release hoa_binh_dam)))))))))) (* (release hoa_binh_dam) (efficiency hoa_binh_dam)))) (decrease
        (storage hoa_binh_dam)
        (* 0.0864 (+ (release_spillways hoa_binh_dam) (+ (release_bottom hoa_binh_dam) (release hoa_binh_dam))))) (evaluated_network))
  )
  (:action advance_day
    :parameters ( ?d1 - day ?d2 - day)
    :precondition (and (active ?d1) (next_step ?d1 ?d2) (evaluated_network) (< 1.4 (level hanoi)) (< (level hanoi) 11.5) (< (+ 500 (agricultural_demand ?d1)) (+ 0.9512619061 (flow son_tay))))
    :effect (and (not (active ?d1)) (active ?d2) (not (evaluated_network)) (assign (release hoa_binh_dam) 295) (assign (release_bottom hoa_binh_dam) 0) (assign (release_spillways hoa_binh_dam) 0) (when
        (<= (storage hoa_binh_dam) 4444.1)
        (assign
          (maximum_turbine_release hoa_binh_dam)
          (+ 1603.1 (* 0.12538 (storage hoa_binh_dam))))) (when
        (and (< 4444.1 (storage hoa_binh_dam)) (<= (storage hoa_binh_dam) 7306))
        (assign
          (maximum_turbine_release hoa_binh_dam)
          (+ 1851.6 (* 0.06959 (storage hoa_binh_dam))))) (when
        (< 7306 (storage hoa_binh_dam))
        (assign
          (maximum_turbine_release hoa_binh_dam)
          2360)) (increase
        (storage hoa_binh_dam)
        (* 0.0864 (+ (flow_beta input_hoa_binh ?d2) (flow input_hoa_binh)))) (assign
        (max_spillways_release hoa_binh_dam)
        (* 6 (+ 8940.6 (- (+ (* 0.0003182 (* (storage hoa_binh_dam) (storage hoa_binh_dam))) (* -0.00000000745000000000 (* (storage hoa_binh_dam) (* (storage hoa_binh_dam) (storage hoa_binh_dam))))) (* 3.1398 (storage hoa_binh_dam)))))) (assign
        (max_bottom_release hoa_binh_dam)
        (* 12 (- (+ (* 0.702 (storage hoa_binh_dam)) (- (* 0.00000000283100000000 (* (storage hoa_binh_dam) (* (storage hoa_binh_dam) (storage hoa_binh_dam)))) (* 0.00006996000000000000 (* (storage hoa_binh_dam) (storage hoa_binh_dam))))) 920.44))) (assign
        (lagged_flow hoa_binh_dam)
        (+ (release_spillways hoa_binh_dam) (+ (release_bottom hoa_binh_dam) (release hoa_binh_dam)))) (assign
        (lagged_flow yen_bai_station)
        (+ (flow_beta yen_bai_station ?d1) (flow yen_bai_station))) (assign
        (lagged_flow vu_quang_station)
        (+ (flow_beta vu_quang_station ?d1) (flow vu_quang_station))) (increase (objective) 1))
  )
)