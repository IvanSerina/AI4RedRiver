import re
import datetime
import csv
import pandas as pd
import pkg_resources
import subprocess
from typing import Dict, List


class OutputScrapper:
    
    VAL_PATH = None
    # Costanti per migliorare la leggibilità
    INITIAL_VALUES = {
        'tot_release': 295,
        'release': 295,
        'release_bottom': 0,
        'release_spillways': 0,
        'production': 0,
        'son_tay_flow': 0,
        'ha_noi_level': 0,
        'storage': 0
    }
    
    # Precompilazione delle espressioni regolari per migliorare le prestazioni
    DATE_PATTERN = re.compile(r'\d{4}_\d{2}_\d{2}')
    ALL_RELEASE_PATTERN = re.compile(r'by (\d+)')
    PRODUCTION_PATTERN = re.compile(r'by (\d*\.?\d+) assignment')
    STORAGE_PATTERN = re.compile(r'\((\d*\.?\d+)\) by (\d*\.?\d+) (increase|decrease)')
    RELEASE_PATTERN = re.compile(r'\((\d*\.?\d+)\) by (\d*\.?\d+) (increase|decrease)')
    RELEASE_BOTTOM_PATTERN = re.compile(r'\((\d*\.?\d+)\) by (\d*\.?\d+) (increase|decrease)')
    RELEASE_SPILLWAYS_PATTERN = re.compile(r'\((\d*\.?\d+)\) by (\d*\.?\d+) (increase|decrease)')
    SIMULATION_RELEASE_PATTERN = re.compile(r'\((\d*\.?\d+)\) by (\d*\.?\d+) assignment')
        
    def __init__(self, release: float = 147.5, release_bottom: float = 1833, release_spillways: float = 2350, validator_path: str = None):
        self.RELEASE = release
        self.RELEASE_BOTTOM = release_bottom
        self.RELEASE_SPILLWAYS = release_spillways
        self.VAL_PATH = validator_path
        pass


    def _read_release_data(self, file_path: str) -> List[str]:
        """Legge il file di input e restituisce le righe come una lista."""
        with open(file_path, 'r') as file:
            return file.readlines()

    def _initialize_day(self, data: Dict, date: datetime.date) -> None:
        """Inizializza i dati per un nuovo giorno."""
        if date not in data:
            data[date] = self.INITIAL_VALUES.copy()

    def _update_value(self, data: Dict, date: datetime.date, key: str, value: float) -> None:
        """Aggiorna il valore per un dato giorno e una data metrica."""
        if date in data:
            data[date][key] += value

    def _parse_release_data_simulation(self, data: List[str], initial_date: datetime.date) -> Dict[datetime.date, Dict[str, float]]:
        """Elabora i dati di input e restituisce un dizionario con i valori giornalieri."""
        daily_data = {}
        current_date = initial_date

        # Inizializza i dati per il giorno iniziale
        self._initialize_day(daily_data, current_date)

        for line in data:
            # Aggiorna la data corrente se viene trovata una nuova riga "Adding (active day_"
            if "Adding (active day_" in line:
                date_match = self.DATE_PATTERN.search(line)
                if date_match:
                    current_date = datetime.datetime.strptime(date_match.group(), '%Y_%m_%d').date()
                    self._initialize_day(daily_data, current_date)
                        
            if "Updating (release_hoa_binh_dam)" in line:
                release_match = self.SIMULATION_RELEASE_PATTERN.search(line)
                if release_match:
                    self._update_value(daily_data, current_date, 'release', float(release_match.group(2))-self.INITIAL_VALUES['release'])
                    self._update_value(daily_data, current_date, 'tot_release', float(release_match.group(2))-self.INITIAL_VALUES['release'])

            # Aggiorna i dati di produzione
            if "Updating (hydropower_production hoa_binh_dam)" in line:
                production_match = self.PRODUCTION_PATTERN.search(line)
                if production_match:
                    production = float(production_match.group(1))
                    self._update_value(daily_data, current_date, 'production', production)

            # Aggiorna i dati di flusso a Son Tay
            if "Updating (flow son_tay)" in line:
                flow_match = self.PRODUCTION_PATTERN.search(line)
                if flow_match:
                    flow = float(flow_match.group(1))
                    self._update_value(daily_data, current_date, 'son_tay_flow', flow)

            # Aggiorna i dati di livello a Hanoi
            if "Updating (level hanoi)" in line:
                level_match = self.PRODUCTION_PATTERN.search(line)
                if level_match:
                    level = float(level_match.group(1))
                    self._update_value(daily_data, current_date, 'ha_noi_level', level)

            # Aggiorna i dati di storage
            if "Updating (storage hoa_binh_dam)" in line:
                storage_match = self.STORAGE_PATTERN.search(line)
                if storage_match:
                    if storage_match.group(3) == "decrease":
                        current_storage = float(storage_match.group(1))
                        difference = float(storage_match.group(2))     
                        self._update_value(daily_data, current_date, 'storage', current_storage - difference)
        
        # Convert the nested dictionary to a DataFrame
        rows = []
        for date, metrics in daily_data.items():
            row_data = {'date': date}
            row_data.update(metrics)
            rows.append(row_data)
        
        df = pd.DataFrame(rows)
        df['date'] = pd.to_datetime(df['date'])
        # Sort by date for better readability
        if not df.empty and 'date' in df.columns:
            df = df.sort_values(by='date')
        
        return df
    
    
    def _parse_release_data(self, data: List[str], initial_date: datetime.date) -> Dict[datetime.date, Dict[str, float]]:
        """Elabora i dati di input e restituisce un dizionario con i valori giornalieri."""
        daily_data = {}
        current_date = initial_date

        # Inizializza i dati per il giorno iniziale
        self._initialize_day(daily_data, current_date)

        for line in data:
            # Aggiorna la data corrente se viene trovata una nuova riga "Adding (active day_"
            if "Adding (active day_" in line:
                date_match = self.DATE_PATTERN.search(line)
                if date_match:
                    current_date = datetime.datetime.strptime(date_match.group(), '%Y_%m_%d').date()
                    self._initialize_day(daily_data, current_date)
                        
            if "Updating (release hoa_binh_dam)" in line:
                if "increase" in line:
                    release_match = self.RELEASE_PATTERN.search(line)
                    if release_match:
                        self._update_value(daily_data, current_date, 'release', self.RELEASE)
                        self._update_value(daily_data, current_date, 'tot_release', self.RELEASE)


            if "Updating (release_bottom hoa_binh_dam)" in line:
                if "increase" in line:
                    release_match = self.RELEASE_BOTTOM_PATTERN.search(line)
                    if release_match:
                        self._update_value(daily_data, current_date, 'release_bottom', self.RELEASE_BOTTOM)
                        self._update_value(daily_data, current_date, 'tot_release', self.RELEASE_BOTTOM)
                        
            if "Updating (release_spillways hoa_binh_dam)" in line:
                if "increase" in line:
                    release_match = self.RELEASE_SPILLWAYS_PATTERN.search(line)
                    if release_match:
                        self._update_value(daily_data, current_date, 'release_spillways', self.RELEASE_SPILLWAYS)
                        self._update_value(daily_data, current_date, 'tot_release', self.RELEASE_SPILLWAYS)

            # Aggiorna i dati di produzione
            if "Updating (hydropower_production hoa_binh_dam)" in line:
                production_match = self.PRODUCTION_PATTERN.search(line)
                if production_match:
                    production = float(production_match.group(1))
                    self._update_value(daily_data, current_date, 'production', production)

            # Aggiorna i dati di flusso a Son Tay
            if "Updating (flow son_tay)" in line:
                flow_match = self.PRODUCTION_PATTERN.search(line)
                if flow_match:
                    flow = float(flow_match.group(1))
                    self._update_value(daily_data, current_date, 'son_tay_flow', flow)

            # Aggiorna i dati di livello a Hanoi
            if "Updating (level hanoi)" in line:
                level_match = self.PRODUCTION_PATTERN.search(line)
                if level_match:
                    level = float(level_match.group(1))
                    self._update_value(daily_data, current_date, 'ha_noi_level', level)

            # Aggiorna i dati di storage
            if "Updating (storage hoa_binh_dam)" in line:
                storage_match = self.STORAGE_PATTERN.search(line)
                if storage_match:
                    if storage_match.group(3) == "decrease":
                        current_storage = float(storage_match.group(1))
                        difference = float(storage_match.group(2))     
                        self._update_value(daily_data, current_date, 'storage', current_storage - difference)

        # Convert the nested dictionary to a DataFrame
        rows = []
        for date, metrics in daily_data.items():
            row_data = {'date': date}
            row_data.update(metrics)
            rows.append(row_data)
        
        df = pd.DataFrame(rows)
        df['date'] = pd.to_datetime(df['date'])
        # Sort by date for better readability
        if not df.empty and 'date' in df.columns:
            df = df.sort_values(by='date')
        
        # obtain the height of the Hoa Binh dam from the storage
        df['hoa_binh_height'] = 5.79e-03 *df['storage']+60.79
        
        # cumulative release and production
        df['cumulative_tot_release'] = df['tot_release'].cumsum()
        df['cumulative_production'] = df['production'].cumsum()
        
        df = df.iloc[:-1]
        
        return df

    
    def _log_daily_release(self, daily_data: Dict[datetime.date, Dict[str, float]], log_file_path: str) -> None:
        """Salva i dati giornalieri in un file CSV."""
        with open(log_file_path, 'w', newline='') as csvfile:
            fieldnames = ['day', 'tot_release', 'release', 'release_bottom', 'release_spillways','production', 'son_tay_flow', 'ha_noi_level', 'storage']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for date, metrics in daily_data.items():
                row = {'day': date, **metrics}
                writer.writerow(row)
    
    def get_objective_value(self, domain_path, problem_path, plan_path):
        """
        Extract the final objective value from plan validation output.
        
        Args:
            domain_path (str): Path to the domain PDDL file
            problem_path (str): Path to the problem PDDL file
            plan_path (str): Path to the plan file
            
        Returns:
            float: The final value of the objective function, or None if not found
        """
        output = self._validate_plan(domain_path, problem_path, plan_path)
        
        # Define regex pattern to find the final value line
        # This handles both positive and negative numbers with optional decimal points
        match = re.search(r"Final value:\s+(\d+\.\d+)", output)

        if match:
            return float(match.group(1))
        else:
            # If the pattern isn't found, return None
            return None

    def _validate_plan(self, domain_path, problem_path, plan_path, silent=True):
        try:
            # Use DEVNULL for stderr if silent mode is requested
            stderr_output = subprocess.DEVNULL if silent else subprocess.PIPE
            
            process = subprocess.Popen(
            [self.VAL_PATH, "-v",  domain_path, problem_path, plan_path],
            stdout=subprocess.PIPE,
            stderr=stderr_output
            )
            stdout, stderr = process.communicate()
            output = stdout.decode('utf-8')
            if stderr and not silent:
                output += stderr.decode('utf-8')
            return output
        except subprocess.CalledProcessError as e:
            return output
        
        
    def read_output(self, domain_path, problem_path, plan_path, initial_date, output_path = None, simulation = False):
        output = self._validate_plan(domain_path, problem_path, plan_path)
        if simulation:
            daily_data = self._parse_release_data_simulation(output.splitlines(), initial_date)
        else:
            daily_data = self._parse_release_data(output.splitlines(), initial_date)
        if output_path:
            self._log_daily_release(daily_data=daily_data, log_file_path=output_path)
        return daily_data
    
    def get_summary(self, domain_path, problem_path, plan_path, initial_date, output_path = None, simulation = False):
        """
        Generate a summary of the plan validation including cumulative releases
        and energy production, plus counts of operations.
        
        Args:
            daily_data: Dictionary containing the daily data. If None, the last processed data will be used.
            
        Returns:
            dict: Summary statistics of the plan validation
        """
        
        daily_data = self.read_output(domain_path, problem_path, plan_path, initial_date, output_path, simulation)
        if daily_data is None:
            # If no data is provided, try to use the last processed data
            if not hasattr(self, '_last_daily_data'):
                raise ValueError("No data available. Run read_output first or provide daily_data.")
            daily_data = self._last_daily_data
        
        # Initialize summary dictionary
        summary = {
            'total_release_turbine': 0,
            'total_release_bottom': 0,
            'total_release_spillways': 0,
            'total_production': 0,
            'bottom_gate_openings': 0,
            'spillway_openings': 0,
            'turbine_release_openings': 0,
            # 'max_son_tay_flow': 0,
            # 'max_ha_noi_level': 0,
            'min_storage': float('inf'),
            'max_storage': 0,
            'total_release': 0,
        }
        
        # Process daily data to generate summary statistics
        for i in range(len(daily_data)):
            # Accumulate releases and production
            summary['total_release_turbine'] += daily_data['release'].iloc[i]
            summary['total_release_bottom'] += daily_data['release_bottom'].iloc[i]
            summary['total_release_spillways'] += daily_data['release_spillways'].iloc[i]
            summary['total_production'] += daily_data['production'].iloc[i]
            
            summary['total_release'] += summary['total_release_turbine'] + summary['total_release_bottom'] + summary['total_release_spillways']
                
            summary['turbine_release_openings'] = summary['total_release']/self.RELEASE
            summary['bottom_gate_openings'] = summary['total_release_bottom']/self.RELEASE_BOTTOM
            summary['spillway_openings'] = summary['total_release_spillways']/self.RELEASE_SPILLWAYS
                
            # # Track maximum flows and levels
            # summary['max_son_tay_flow'] = max(summary['max_son_tay_flow'], metrics['son_tay_flow'])
            # summary['max_ha_noi_level'] = max(summary['max_ha_noi_level'], metrics['ha_noi_level'])
            
            # Track storage extremes
            if daily_data['storage'].iloc[i] != 0:  # Only consider non-zero storage values
                summary['min_storage'] = min(summary['min_storage'], daily_data['storage'].iloc[i])
                summary['max_storage'] = max(summary['max_storage'], daily_data['storage'].iloc[i])
                
        
        # If no storage data was found, reset min_storage
        if summary['min_storage'] == float('inf'):
            summary['min_storage'] = 0
        
        return summary
        
        
    def validate_plan(self, domain_path, problem_path, plan_path):
        """
        Validate a plan using the Validator tool and return the output.
        
        Args:
            domain_path (str): Path to the domain PDDL file
            problem_path (str): Path to the problem PDDL file
            plan_path (str): Path to the plan file
            
        Returns:
            str: The output of the validation process
        """
        output = self._validate_plan(domain_path, problem_path, plan_path)
        if "Successful plans" in output:
            return True
        else:
            return False