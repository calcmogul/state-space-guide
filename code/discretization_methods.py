#!/usr/bin/env python3

import frccontrol as frccnt
import matplotlib.pyplot as plt
import numpy as np

from elevator import Elevator

plt.rc("text", usetex=True)


def generate_forward_euler(data, dt, sample_period):
    """Generates forward Euler approximation of data set.

    Keyword arguments:
    data -- array of velocity data
    dt -- dt of original data samples
    sample_period -- desired time between samples in approximation
    """
    y = []
    count = 0
    val = 0
    for i in range(len(data)):
        count += 1
        if count >= sample_period / dt:
            val += data[i] * sample_period
            count = 0
        y.append(val)
    return y


def generate_backward_euler(data, dt, sample_period):
    """Generates backward Euler approximation of data set.

    Keyword arguments:
    data -- array of velocity data
    dt -- dt of original data samples
    sample_period -- desired time between samples in approximation
    """
    y = []
    count = 0
    val = 0
    for i in range(len(data)):
        count += 1
        if count >= sample_period / dt:
            if i < len(data):
                val += data[i + 1] * sample_period
            count = 0
        y.append(val)
    return y


def generate_bilinear_transform(data, dt, sample_period):
    """Generates bilinear transform approximation of data set.

    Keyword arguments:
    data -- array of velocity data
    dt -- dt of original data samples
    sample_period -- desired time between samples in approximation
    """
    y = []
    count = 0
    val = 0
    for i in range(len(data)):
        count += 1
        if count >= sample_period / dt:
            if i < len(data):
                val += (data[i] + data[i + 1]) * sample_period / 2
            count = 0
        y.append(val)
    return y


def main():
    dt = 0.00505
    sample_period = 0.1
    elevator = Elevator(dt)

    # Set up graphing
    l0 = 0.1
    l1 = l0 + 5.0
    l2 = l1 + 0.1
    l3 = l2 + 1.0
    t = np.linspace(0, l3, l3 / dt)

    refs = []

    # Generate references for simulation
    for i in range(len(t)):
        if t[i] < l0:
            r = np.matrix([[0.0], [0.0]])
        elif t[i] < l1:
            r = np.matrix([[1.524], [0.0]])
        else:
            r = np.matrix([[0.0], [0.0]])
        refs.append(r)

    state_rec, ref_rec, u_rec = elevator.generate_time_responses(t, refs)
    pos = elevator.extract_row(state_rec, 0)
    vel = elevator.extract_row(state_rec, 1)

    plt.figure(1)
    plt.plot(t, pos, label="Continuous")
    y = generate_forward_euler(vel, dt, sample_period)
    plt.plot(t, y, label="Forward Euler (T={}s)".format(sample_period))
    y = generate_backward_euler(vel, dt, sample_period)
    plt.plot(t, y, label="Backward Euler (T={}s)".format(sample_period))
    y = generate_bilinear_transform(vel, dt, sample_period)
    plt.plot(t, y, label="Bilinear transform (T={}s)".format(sample_period))
    plt.legend()
    plt.savefig("discretization_methods.svg")


if __name__ == "__main__":
    main()
