import os
import shutil
from pathlib import Path
import csv
import re
import time
import subprocess
import pandas as pd
import numpy as np
from datetime import datetime
from output_scrapper import OutputScrapper
from hydropower_conversion import convert_hydropower_to_release


def update_pddl_values(file_path: str, time_steps: list, new_values: list):
    """
    The function `update_pddl_values` updates PDDL values in a file based on specified time steps and
    new values.
    
    :param file_path: The `file_path` parameter in the `update_pddl_values` function is the path to the
    PDDL (Planning Domain Definition Language) file that you want to update with new values for specific
    time steps. This function reads the content of the file, finds the lines corresponding to the given
    time steps
    :type file_path: str
    :param time_steps: Time steps are specific points in time that are used as references in a process
    or system. In the context of the provided function `update_pddl_values`, time_steps refer to the
    time steps at which you want to update values in a PDDL (Planning Domain Definition Language) file.
    These time steps
    :type time_steps: list
    :param new_values: The `new_values` parameter should be a list containing the new values that you
    want to update in the PDDL file corresponding to the time steps provided. Each value in the
    `new_values` list should correspond to the time step at the same index position in the `time_steps`
    list
    :type new_values: list
    """
    if len(list(time_steps)) != len(new_values):
        raise ValueError("The number of time_steps and new_values must be the same.")

    with open(file_path, 'r', encoding="utf-8") as file:
        content = file.read()

    for time_step, new_value in zip(time_steps, new_values):
        # Regular expression to find the line with the given time_step
        # Example: (= (release Day_2001_09_30) 0)
        pattern = re.compile(rf'\(= \(release {time_step}\) \d+\.?\d*\)')
        new_line = f'(= (release {time_step}) {new_value})'

        # Replace the old line with the new line
        content = pattern.sub(new_line, content)
    
    with open(file_path, 'w', encoding="utf-8") as file:
        file.write(content)

def extract_dates_from_pddl(file_path):
    try:
        with open(file_path, 'r', encoding="utf-8") as file:
            content = file.read()
            
            # Extract start date (active in init section)
            start_match = re.search(r'\(active\s+day_(\d{4})_(\d{2})_(\d{2})\)', content)
            
            # Extract end date (active in goal section)
            end_match = re.search(r'\(:goal\s+\(and\s+\(active\s+day_(\d{4})_(\d{2})_(\d{2})\)', content)
                        
            if start_match:
                start_year, start_month, start_day = start_match.groups()
                start_date = datetime(int(start_year), int(start_month), int(start_day)).date()
            else:
                start_date = None
                
            if end_match:
                end_year, end_month, end_day = end_match.groups()
                end_date = datetime(int(end_year), int(end_month), int(end_day)).date()
            else:
                end_date = None
            
            return start_date, end_date
    except Exception as e:
        return f"Error: {str(e)}", None


def increase_problem_fluent_value(problem_pddl, fluent_name, increment_value):
    """
    Aumenta il valore di un fluente nel file del problema PDDL.
    
    Args:
        problem_pddl (str): Percorso del file del problema PDDL.
        fluent_name (str): Nome del fluente da modificare.
        increment_value (float): Valore da aggiungere al valore attuale del fluente.
        
    Returns:
        tuple: (valore_vecchio, valore_nuovo) i valori prima e dopo l'incremento.
    """
    # Leggi il contenuto del file
    with open(problem_pddl, "r") as f:
        contenuto = f.read()

    # Espressione regolare per trovare il fluent_name e catturare il valore attuale
    pattern = rf"\(= \({fluent_name}\) ([-+]?[0-9]*\.?[0-9]+)\)"
    
    # Trova il valore attuale
    match = re.search(pattern, contenuto)
    if not match:
        print(f"Fluente '{fluent_name}' non trovato nel file.")
        return None, None
        
    valore_attuale = float(match.group(1))
    
    # Calcola il nuovo valore
    nuovo_valore = valore_attuale + increment_value
    
    # Nuovo valore da sostituire
    nuova_riga = f"(= ({fluent_name}) {nuovo_valore})"

    # Sostituisci il valore nel file
    nuovo_contenuto = re.sub(pattern, nuova_riga, contenuto)

    # Sovrascrivi il file con la versione aggiornata
    with open(problem_pddl, "w") as f:
        f.write(nuovo_contenuto)


def increase_fluent(problem_file, fluent_name, new_value):
    """
    Aumenta tutti i valori di un fluente specificato nel file del problema PDDL.
    Modifica direttamente il file originale senza creare copie.
    
    Args:
        problem_file (str): Percorso del file del problema PDDL.
        fluent_name (str): Nome del fluente da aumentare.
        new_value (float): Nuovo valore da assegnare al fluente.
    Returns:
        float: La somma totale dei valori del fluente aggiornati.
    """
    increase_problem_fluent_value(problem_file, fluent_name, new_value)

def increment_min_release(enhsp_path, 
                          domain_file,
                          problem_file,
                          output_dir,
                          historical_path,
                          validator_path,
                          gb=10,
                          search="gbfs",
                          heuristic="blind",
                          max_time=180,
                          start_pct=0.05,
                          end_pct=0.01,
                          max_iterations=None
                          ):
    """
    Esegue ENHSP in modalità anytime, salva ogni piano trovato in file .plan
    e raccoglie i dati di sintesi in un file CSV.

    Args:
        enhsp_path (str): Percorso dell'eseguibile ENHSP.
        domain_file (str): File del dominio PDDL.
        problem_file (str): File del problema PDDL.
        output_dir (str): Directory dove salvare i piani e il CSV.
        historical_path (str): Percorso del file CSV con i dati storici.
        gb (int): Memoria heap per la JVM (GB).
        search (str): Algoritmo di ricerca.
        heuristic (str): Euristica.
        max_time (int): Tempo massimo in secondi.
        start_pct (float): Percentuale iniziale incremento.
        end_pct (float): Percentuale finale incremento.
        max_iterations (int|None): Numero massimo di iterazioni.
    """

    # === PREPARAZIONE PERCORSI ===
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    plans_dir = output_dir / "plans"
    plans_dir.mkdir(exist_ok=True)

    problems_dir = output_dir / "problems"
    problems_dir.mkdir(exist_ok=True)

    working_dir = output_dir / "working_files"
    working_dir.mkdir(exist_ok=True)

    domain_file = Path(domain_file).resolve()
    problem_file = Path(problem_file).resolve()
    enhsp_path = Path(enhsp_path).resolve()
    historical_path = Path(historical_path).resolve()

    working_domain_file = working_dir / domain_file.name
    working_problem_file = working_dir / problem_file.name
    shutil.copy2(domain_file, working_domain_file)
    shutil.copy2(problem_file, working_problem_file)

    # === DATE E DATI STORICI ===
    starting_date, end_date = extract_dates_from_pddl(str(working_problem_file))
    starting_date = pd.to_datetime(starting_date)
    end_date = pd.to_datetime(end_date)

    historical_df = pd.read_csv(historical_path)
    historical_df["Date"] = pd.to_datetime(historical_df["Date"])
    historical_df = historical_df[
        (historical_df["Date"] >= starting_date)
        & (historical_df["Date"] <= end_date)
    ]
    if historical_df.shape[0] == 0:
        raise ValueError(
            "Filtered historical_df in increment_min_release has 0 rows!"
        )
    historical_df["water_for_energy"] = convert_hydropower_to_release(
        historical_df["Energy_demand"]
    )

    csv_filename = output_dir / "summary.csv"
    fieldnames = [
        "Plan_File",
        "Plan_Length",
        "Metric_Search",
        "Planning_Time",
        "Heuristic_Time",
        "Search_Time",
        "Expanded_Nodes",
        "States_Evaluated",
        "Dead_Ends",
        "Duplicates",
        # Validation fields
        "total_release_turbine",
        "total_release_spillways",
        "total_production",
        "bottom_gate_openings",
        "max_storage",
        "total_release",
        "total_release_bottom",
        "spillway_openings",
        "turbine_release_openings",
        "min_storage",
    ]

    if not csv_filename.exists():
        with csv_filename.open("w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

    summary_patterns = {
        "Plan_Length": re.compile(r"Plan-Length:\s*(\d+)"),
        "Metric_Search": re.compile(r"Metric \(Search\):\s*([-+]?[0-9]*\.?[0-9]+)"),
        "Planning_Time": re.compile(r"Planning Time \(msec\):\s*(\d+)"),
        "Heuristic_Time": re.compile(r"Heuristic Time \(msec\):\s*(\d+)"),
        "Search_Time": re.compile(r"Search Time \(msec\):\s*(\d+)"),
        "Expanded_Nodes": re.compile(r"Expanded Nodes:\s*(\d+)"),
        "States_Evaluated": re.compile(r"States Evaluated:\s*(\d+)"),
        "Dead_Ends": re.compile(r"Number of Dead-Ends detected:\s*(\d+)"),
        "Duplicates": re.compile(r"Number of Duplicates detected:\s*(\d+)"),
    }

    starting_time = time.time()
    pct = np.linspace(start_pct, end_pct, num=(end_date - starting_date).days + 1)

    # copia iniziale del problema
    shutil.copy2(working_problem_file, problems_dir / "problem_0.pddl")

    plan_count = 0
    diffs = []
    n_iterations = 0
    has_time = True

    while has_time:
        # calcolo tempo già trascorso e residuo
        elapsed = time.time() - starting_time
        remaining = max_time - elapsed
        if remaining <= 0:
            break

        plan_filename = plans_dir / f"plan_{plan_count}.plan"
        
        # === COSTRUZIONE COMANDO ENHSP ===
        command = [
            "java",
            f"-Xmx{gb}g",
            "-jar",
            str(enhsp_path),
            "-o",
            str(working_domain_file),
            "-f",
            str(working_problem_file),
            "-s",
            search,
            "-h",
            heuristic,
            "-ha",
            "false",
            "-sp",
            str(plan_filename),
        ]

        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        output_scrapper = OutputScrapper(validator_path=validator_path)

        # aspetta il processo fino al tempo residuo; se scade, kill e interrompi
        try:
            stdout, _ = process.communicate(timeout=remaining)
        except subprocess.TimeoutExpired as e:
            try:
                process.kill()
            except Exception:
                pass
            try:
                process.wait(timeout=5)
            except Exception:
                pass
            # terminare l'esecuzione principale perché il tempo è esaurito
            has_time = False
            break

        # se communicate è andato a buon fine, stdout è stringa (text=True)
        if stdout is None:
            stdout = ""

        # estrai i dati riassuntivi dall'output
        summary_data = {"Plan_File": plan_filename.name}
        for key, pattern in summary_patterns.items():
            m = pattern.search(stdout)
            summary_data[key] = m.group(1) if m else ""

        # se il file piano non esiste o è vuoto, segnalo e interrompo
        if not plan_filename.exists() or plan_filename.stat().st_size == 0:
            has_time = False
            break

        # VALIDAZIONE (come prima)
        validation_summary = output_scrapper.get_summary(
            domain_path=str(working_domain_file),
            problem_path=str(working_problem_file),
            plan_path=str(plan_filename),
            initial_date=starting_date.strftime("%Y-%m-%d"),
        )
        daily_df = output_scrapper.read_output(
            domain_path=str(working_domain_file),
            problem_path=str(working_problem_file),
            plan_path=str(plan_filename),
            initial_date=starting_date.strftime("%Y-%m-%d"),
        )
        
        summary_data.update(validation_summary)
        with csv_filename.open("a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(summary_data)

        plan_count += 1
        new_problem_file = problems_dir / f"problem_{plan_count}.pddl"

        if not diffs:
            diffs = [
                historical_df["water_for_energy"].iloc[i] - daily_df["release"].iloc[i]
                for i in range(len(daily_df))
            ]

        daily_df["date"] = pd.to_datetime(daily_df["date"])

        valid = True
        while valid:
            elapsed = time.time() - starting_time
            if elapsed > max_time:
                has_time = False
                break

            remaining = max_time - elapsed
            
            for i in range(len(daily_df)):
                production = daily_df["production"].iloc[i]
                demand = historical_df["Energy_demand"].iloc[i]
                if production < demand and diffs[i] > 0:
                    delta = round(diffs[i] * pct[i], 2)
                    date_str = daily_df["date"].iloc[i].strftime("%Y_%m_%d")
                    fluent = f"min_release hoa_binh_dam day_{date_str}"
                    increase_fluent(str(working_problem_file), fluent, delta)

            if not output_scrapper.validate_plan(
                str(working_domain_file), str(working_problem_file), str(plan_filename)
            ):
                valid = False

        shutil.copy2(working_problem_file, new_problem_file)

        if time.time() - starting_time > max_time:
            has_time = False
            break

        n_iterations += 1
        if max_iterations is not None and n_iterations >= max_iterations:
            has_time = False
            break