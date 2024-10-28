# BlueQuantum-Challenge
My Solutions based on Circuit Cutting to BlueQuantum's Challenge:

Task Details:

The goal is to "solve" as many of the 3 circuits (attached below) as possible. Each of the circuits prepares a state that has 1 bitstring with O(1) probability, while every other bitstring has a significantly (exponentially) smaller probability. Your task is to find the hidden bitstring for each of the 3 circuits.

Circuits are attached here as .qasm files.


# Solution:

The roadblock to finding the hidden string is the quantum circuits' size. The size of the 3 quantum circuits are 30, 42 and 60 qubits, respectively. Further, the depth of the circuits is > 10. Thus making it unfeasible to do the simulations in the quantum simulators. In my solution, I targeted to resolve the issue of large width using circuit cutting (& knitting). While circuit cutting can also be employed to reduce the depth, I haven't employed it since it has a huge overhead and increases errors. 

Qiskit and pennylane allow circuit cutting but can only be accurately employed in expectation value calculations. It is not suitable for sampling tasks or, in other words, finding the probability distribution of the states. Since I do not want to reconstruct the entire probability distribution but to find the state that corresponds to high probability, I used circuit cutting and the knitting of the states to find the output state. So, the assumption I took here is that even though circuit cutting could be used find the state of maximum probability even though we could not get the exact probability distribution.
