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


qc = qiskit.qasm2.load('circuit_1_30q_fixed.qasm', include_path=('.',), include_input_directory='append', custom_instructions=qiskit.qasm2.LEGACY_CUSTOM_INSTRUCTIONS, custom_classical=(), strict=False)
qc.remove_final_measurements() # Removing final measurements
print(qc.draw(fold=-1))

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


subcircuits,subobservables,bases = cutting_circuits(qc,2)

num_samples = 10

subexperiments, coefficients = generate_cutting_experiments(
    circuits=subcircuits, observables=subobservables, num_samples=num_samples
)

backend = AerSimulator()

pass_manager = generate_preset_pass_manager(optimization_level=1, backend=backend)
isa_subexperiments = {
    label: pass_manager.run(partition_subexpts)
    for label, partition_subexpts in subexperiments.items()
}

with Batch(backend=backend) as batch:
    sampler = SamplerV2(mode=batch)
    jobs = {
        label: sampler.run(subsystem_subexpts, shots=2**12).result()
        for label, subsystem_subexpts in isa_subexperiments.items()
    }

print('State of Maximum Probability:', knitting_results(jobs))