from typing import Union

from unified_planning.model.walkers import StateEvaluator
from unified_planning.shortcuts import *

class NumberHelper(object):
    
    @staticmethod
    def fraction_to_float(number: Union[int, Fraction]) -> Union[int, float]:
        if isinstance(number, Fraction):
            if number.denominator == 1:
                return number.numerator
            return float(number)
        return number
    
    @staticmethod
    def get_numeric_value_from_state(
        expression: FNode, state: State, se : StateEvaluator
    ) -> Union[int, float]:
        exp_value: Union[int, Fraction] = se.evaluate(
            expression, state
        ).constant_value()
        return NumberHelper.fraction_to_float(exp_value)
     
    @staticmethod
    def fluents_power_elevation(expression : FNode, power : int):
        power_expression : FNode = expression
        if power == 0:
            return 1
        elif power != 1:
            power_expression = expression*NumberHelper.fluents_power_elevation(expression,power-1)
        else:
            return expression

        return power_expression