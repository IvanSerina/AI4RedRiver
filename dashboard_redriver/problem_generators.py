import pandas as pd
import warnings
import os
from simple_problem_constructor import (
    SimpleRedRiverProblems,
    SimpleProblemConstructor
)
from string_helper import StringHelper
from unified_planning.io import PDDLWriter

class ProblemGenerator:
    def __init__(self, historical_data_path: str, problem_data_path: str):
        self.historical_data = historical_data_path
        self.problem_data_path = problem_data_path

    def save_problem(self, problem: SimpleProblemConstructor, problem_output_path=None):
        warnings.filterwarnings('ignore', category=UserWarning)
        writer = PDDLWriter(problem.problem)
        os.makedirs(problem.problem_path, exist_ok=True)
        #file_path = os.path.join(problem.problem_path, f'Problem_{problem.name}.pddl')
        file_path = os.path.join(problem.problem_path, 'problem.pddl')
        writer.write_problem(file_path)
        StringHelper.replace_regex_in_text_file(file_path, r'\(:domain\s+problem_[\d_]+-domain\)', '(:domain red_river_domain)')
        StringHelper.replace_scientific_notation_decimal(file_path)

    def save_simple_domain(self, problem: SimpleProblemConstructor, domain_output_dir=None):
        # set the domain folder based on the inverse flag
        os.makedirs(domain_output_dir, exist_ok=True)

        #file_path = os.path.join(domain_output_dir, f'Domain_{problem.name}.pddl')
        file_path = os.path.join(domain_output_dir, 'domain.pddl')
        warnings.filterwarnings('ignore', category=UserWarning)
        writer = PDDLWriter(problem.problem)
        writer.write_domain(file_path)
        StringHelper.replace_scientific_notation_decimal(file_path)


    def create_simple_problem(self, starting_date=None, ending_date=None, domain_output_dir=None, problem_output_dir=None):
        n_days = (ending_date - starting_date).days + 1
        problems_generator = SimpleRedRiverProblems(
            starting_date=starting_date,
            ending_date=ending_date,
            n_days=n_days, 
            historical_data_path=self.historical_data,
            problem_data_path=self.problem_data_path,
            )
        
        problems_generator.create_problem(problem_out_dir=problem_output_dir)
        problem = problems_generator.problem
        self.save_problem(problem, problem_output_dir)
        self.save_simple_domain(problem, domain_output_dir)      