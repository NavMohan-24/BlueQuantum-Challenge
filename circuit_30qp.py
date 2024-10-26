import numpy as np
import string

import qiskit.qasm2
from qiskit.circuit.library import TwoLocal
from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit.quantum_info import SparsePauliOp

from qiskit_addon_cutting import partition_problem
from qiskit_addon_cutting import generate_cutting_experiments

from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import SamplerV2, Batch
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


qc = qiskit.qasm2.load('circuit_1_30q_fixed.qasm', include_path=('.',), include_input_directory='append', custom_instructions=qiskit.qasm2.LEGACY_CUSTOM_INSTRUCTIONS, custom_classical=(), strict=False)
qc.remove_final_measurements() # Removing final measurements
#print(qc.draw(fold=-1))

print('Circuit Creation Successful...')

def cutting_circuits(qc,num_cuts):

    num_qubits = qc.num_qubits
    observable = SparsePauliOp(["Z"*num_qubits])

    labels  = list(string.ascii_uppercase[:num_cuts])
    partition_string = ''.join([label*(num_qubits//num_cuts) for label in labels])

    partitioned_problem = partition_problem(
    circuit=qc, partition_labels=partition_string,observables=observable.paulis)

    subcircuits = partitioned_problem.subcircuits
    subobservables = partitioned_problem.subobservables
    bases = partitioned_problem.bases

    return(subcircuits,subobservables,bases)

def knitting_results(job_dict): 

    final_state = ''

    for results in job_dict.values():
        trials = 0
        final_counts = {}
        for result in results:
            counts = result.data.observable_measurements.get_counts()
            trials += sum(list(counts.values()))
            for keys in counts.keys():
                final_counts[keys] = final_counts.get(keys, 0)+counts[keys]
        
        final_state+=max(final_counts,key=final_counts.get)
    
    return(final_state)

# Generate subcircuits and observables
subcircuits, subobservables, bases = cutting_circuits(qc, 2)
num_samples = 10

subexperiments, coefficients = generate_cutting_experiments(
    circuits=subcircuits, observables=subobservables, num_samples=num_samples
)


# Backend and pass manager setup
backend = AerSimulator()
pass_manager = generate_preset_pass_manager(optimization_level=1, backend=backend)

# Prepare subexperiments with pass manager
isa_subexperiments = {
    label: pass_manager.run(partition_subexpts)
    for label, partition_subexpts in subexperiments.items()
}
print('Circuit Cutting Completed...')
# Function to run a batch of subexperiments on a thread
def run_subexperiment(label, sub_experiment):
    with Batch(backend=backend) as batch:
        sampler = SamplerV2(mode=batch)
        job = sampler.run(sub_experiment, shots=2**12).result()
        return label, job
    
print('Circuit Simulation Started ...')

# Using ThreadPoolExecutor for parallel processing
start_time = time.time()
job_results = {}
with ThreadPoolExecutor() as executor:
    future_jobs = {executor.submit(run_subexperiment, label, sub_experiment): label
                   for label, sub_experiment in isa_subexperiments.items()}

    for future in as_completed(future_jobs):
        label = future_jobs[future]
        try:
            result_label, job_result = future.result()
            job_results[result_label] = job_result
        except Exception as exc:
            print(f"Experiment {label} generated an exception: {exc}")
            
end_time = time.time()
print('Circuit Simulation Completed')

# Print the final state with maximum probability
print('State of Maximum Probability:', knitting_results(job_results))
execution_time = end_time - start_time
print(f'Total Execution Time: {execution_time:.2f} seconds')