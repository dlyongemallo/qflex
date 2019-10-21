# Lint as: python3
"""
Provides utils for qFlex.
"""

import numpy as np
import cirq
import re


def ComputeSchmidtRank(gate):

    if len(gate.qubits) == 1:
        return 1
    if len(gate.qubits) > 2:
        raise AssertionError("Not yet implemented.")

    V, S, W = np.linalg.svd(
        np.reshape(
            np.einsum('abcd->acbd', np.reshape(cirq.unitary(gate),
                                               [2, 2, 2, 2])), [4, 4]))

    return sum(S != 0)


def GetGridQubits(grid_stream):

    grid = [[y
             for y in x.strip()
             if y == '0' or y == '1']
            for x in grid_stream.readlines()
            if len(x) and x[0] != '#']

    # Get the number of rows
    grid_I = len(grid)

    # Check that the number of columns is consistent
    if len(set(len(x) for x in grid)) != 1:
        raise AssertionError("Number of columns in grid are not consistent.")

    # Get the number of columns
    grid_J = len(grid[0])

    # Return cirq.GridQubit
    return {
        I * grid_J + J: cirq.GridQubit(I, J)
        for I in range(grid_I) for J in range(grid_J) if grid[I][J] == '1'
    }


def GetGate(line, qubits):

    # Get map from gate name to cirq
    gates_map = {}
    gates_map['h'] = cirq.H
    gates_map['x'] = cirq.X
    gates_map['z'] = cirq.Z
    gates_map['t'] = cirq.Z**(0.25)
    gates_map['x_1_2'] = cirq.X**(0.5)
    gates_map['y_1_2'] = cirq.Y**(0.5)
    gates_map['h_1_2'] = cirq.H**(0.5)
    gates_map['cz'] = cirq.CZ
    gates_map['cx'] = cirq.CNOT
    gates_map['rz'] = cirq.Rz

    # Remove last cr
    line = line.strip()

    # Remove everything after '#'
    line = re.sub(r"#.*", r"", line)

    # Remove any special character
    line = re.sub(r"[^)(\s\ta-zA-Z0-9_.,-]", r"", line)

    # Convert tabs to spaces
    line = re.sub(r"[\t]", " ", line)

    # Remove multiple spaces
    line = re.sub(r"[\s]{2,}", r" ", line)

    # Remove last space
    line = re.sub(r"\s+$", r"", line)

    # Remove any space between a non-space char and '('
    line = re.sub(r"[\s]+[(]", r"(", line)

    # Remove spaces between parentheses
    line = re.sub(r"\s+(?=[^()]*\))", r"", line)

    # After stripping, line should follow the format
    # 0 gate(p1,p2,...) q1 q2 ...

    # Only one open parenthesis is allowed, followed by one closed
    if line.count('(') == 1:
        if line.count(')') != 1:
            raise AssertionError('ERROR: Open parenthesis is not matched.')
    elif line.count('(') > 1:
        raise AssertionError('ERROR: Too many open parentheses.')
    elif line.count(')') != 0:
        raise AssertionError('ERROR: Too many close parentheses.')

    line = line.split()
    cycle = int(line[0])
    gate_qubits = [int(x) for x in line[2:]]
    if line[1].count('('):
        gate_name, params = line[1].split('(')
        params = [float(x) for x in params.replace(')', '').split(',')]
    else:
        gate_name = line[1]
        params = None

    if not gate_name in gates_map:
        raise AssertionError(
            "ERROR: Gate {} not supported yet.".format(gate_name))

    if params == None:
        return gates_map[gate_name](*[qubits[q] for q in gate_qubits])
    else:
        return gates_map[gate_name](*params)(*[qubits[q] for q in gate_qubits])


def GetCircuit(circuit_stream, qubits):

    circuit = cirq.Circuit()
    circuit.append(
        gate for gate in (GetGate(line, qubits)
                          for line in circuit_stream
                          if len(line) and len(line.strip().split()) > 1))
    return circuit
