# scritp to run enhsp and solve the problem
import os
import subprocess
import sys
import tempfile

import subprocess
import shlex
import os
import sys

def run_enhsp(
    domain_path: str,
    problem_path: str,
    output_path: str,
    enhsp_path: str = "ENHSP/enhsp.jar",
    planner_parameters: str | None = "-s gbfs -h hmrp") -> str:
    """
    Lancia ENHSP e salva il piano risultante nel file `output_path`.
    Restituisce lo stdout del planner.
    :param domain_path: percorso al file domain.pddl
    :param problem_path: percorso al file problem.pddl
    :param output_path: percorso dove salvare il piano risultante
    :param enhsp_path: percorso al jar di ENHSP (default: "ENHSP/enhsp.jar")
    :param planner_parameters: parametri extra per il planner (default: "-s gbfs -h hmrp")
    :return: stdout del planner
    """

    # 1. Assicura che la directory di destinazione esista
    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)

    # 2. Costruisci la lista di argomenti (niente shell=True)
    cmd = [
        "java", "-jar", enhsp_path,
        "-o", domain_path,
        "-f", problem_path,
        "-sp", output_path,  # salva il piano
    ]

    # 3. Aggiungi i parametri del planner se sono definiti
    if planner_parameters:
        cmd += shlex.split(planner_parameters)

    print("Eseguo:", " ".join(shlex.quote(c) for c in cmd))

    # 4. Esegui il comando e cattura output
    try:
        result = subprocess.run(cmd, check=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)
        return result.stdout

    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"ENHSP failed with exit code {e.returncode}\nSTDERR:\n{e.stderr}"
        ) from e


def run_enhsp_from_strings(
    domain_str: str,
    problem_str: str,
    enhsp_path: str = "ENHSP/enhsp.jar",
    planner_parameters: str | None = "-s gbfs -h hmrp"
) -> str:
    """
    Lancia ENHSP utilizzando contenuti PDDL in formato stringa.
    Restituisce il piano prodotto come stringa.
    
    :param domain_str: contenuto del domain PDDL
    :param problem_str: contenuto del problem PDDL
    :param enhsp_path: percorso al jar di ENHSP
    :param planner_parameters: parametri per il planner
    :return: piano risultante come stringa
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        domain_path = os.path.join(tmpdir, "domain.pddl")
        problem_path = os.path.join(tmpdir, "problem.pddl")
        plan_path = os.path.join(tmpdir, "plan.txt")

        # Scrive i file temporanei
        with open(domain_path, "w") as f:
            f.write(domain_str)
        with open(problem_path, "w") as f:
            f.write(problem_str)

        cmd = [
            "java", "-jar", enhsp_path,
            "-o", domain_path,
            "-f", problem_path,
            "-sp", plan_path,
        ]

        if planner_parameters:
            cmd += shlex.split(planner_parameters)

        print("Eseguo:", " ".join(shlex.quote(c) for c in cmd))

        try:
            result = subprocess.run(cmd, check=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True)

            # Legge e restituisce il contenuto del piano
            if os.path.exists(plan_path):
                with open(plan_path, "r") as f:
                    plan = f.read()
                return plan.strip()
            else:
                raise RuntimeError("ENHSP non ha generato un piano.")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"ENHSP failed with exit code {e.returncode}\nSTDERR:\n{e.stderr}"
            ) from e