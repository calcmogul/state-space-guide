#!/usr/bin/env python3

# Runs LTV unicycle simulation on decoupled model with nonlinear trajectory

# Avoid needing display if plots aren't being shown
import sys

if "--noninteractive" in sys.argv:
    import matplotlib as mpl

    mpl.use("svg")
    import bookutil.latex as latex

import control as ct
import frccontrol as fct
import math
import matplotlib.pyplot as plt
import numpy as np

from bookutil.drivetrain import drivetrain_decoupled, get_diff_vels
from bookutil.pose2d import Pose2d
from bookutil.systems import DrivetrainDecoupledVelocity


class LTVUnicycle:
    def __init__(self, q, r):
        self.Q = np.diag(1.0 / np.square(q))
        self.R = np.diag(1.0 / np.square(r))

    def make_model(self, v):
        A = np.zeros((3, 3))
        if abs(v) < 1e-9:
            v = 1e-9
        A[1, 2] = v
        B = np.array([[1, 0], [0, 0], [0, 1]])
        C = np.array([[0, 0, 1]])
        D = np.array([[0, 0]])

        return ct.StateSpace(A, B, C, D, remove_useless=False)

    def calculate(self, pose_desired, v_desired, omega_desired, pose, v):
        error = pose_desired.relative_to(pose)
        e = np.array([[error.x], [error.y], [error.theta]])

        sys = self.make_model(v)
        dsys = sys.sample(0.02)
        K = fct.lqr(dsys, self.Q, self.R)

        u = K @ e
        return v_desired + u[0, 0], omega_desired + u[1, 0]


class Drivetrain(DrivetrainDecoupledVelocity):
    def __init__(self, dt):
        """Drivetrain subsystem.
        Keyword arguments:
        dt -- time between model/controller updates
        """
        DrivetrainDecoupledVelocity.__init__(self, dt)

    def update_controller(self, next_r):
        u = self.K @ (self.r - self.x_hat)
        if self.f:
            rdot = (next_r - self.r) / self.dt
            uff = self.Kff @ (rdot - self.f(self.r, np.zeros(self.u.shape)))
        else:
            uff = self.Kff @ (next_r - self.sysd.A @ self.r)
        self.r = next_r
        self.u = u + uff
        u_cap = np.max(np.abs(self.u))
        if u_cap > 12.0:
            self.u = self.u / u_cap * 12.0


def main():
    dt = 0.02

    ltv_unicycle = LTVUnicycle([0.0625, 0.125, 2.5], [0.95, 0.95])
    drivetrain = Drivetrain(dt)
    print("ctrb cond =", np.linalg.cond(ct.ctrb(drivetrain.sysd.A, drivetrain.sysd.B)))

    data = np.genfromtxt("ramsete_traj.csv", delimiter=",")
    t = data[1:, 0].T
    xprof = data[1:, 1].T
    yprof = data[1:, 2].T
    thetaprof = data[1:, 3].T
    vprof = data[1:, 4].T
    omegaprof = data[1:, 5].T

    # Initial robot pose
    pose = Pose2d(xprof[0] + 0.5, yprof[0] + 0.5, np.pi / 4)
    desired_pose = Pose2d()

    vl = float("inf")
    vr = float("inf")

    x_rec = []
    y_rec = []
    theta_rec = []
    vl_rec = []
    vlref_rec = []
    vr_rec = []
    vrref_rec = []
    ul_rec = []
    ur_rec = []

    # Run LTV unicycle controller
    i = 0
    while i < len(t) - 1:
        desired_pose.x = xprof[i]
        desired_pose.y = yprof[i]
        desired_pose.theta = thetaprof[i]

        vc = (drivetrain.x[0, 0] + drivetrain.x[1, 0]) / 2.0
        vref, omegaref = ltv_unicycle.calculate(
            desired_pose, vprof[i], omegaprof[i], pose, vc
        )
        vlref, vrref = get_diff_vels(vref, omegaref, drivetrain.rb * 2.0)
        next_r = np.array([[vlref], [vrref]])
        drivetrain.update(next_r)
        vc = (drivetrain.x[0, 0] + drivetrain.x[1, 0]) / 2.0
        omega = (drivetrain.x[1, 0] - drivetrain.x[0, 0]) / (2.0 * drivetrain.rb)
        vl, vr = get_diff_vels(vc, omega, drivetrain.rb * 2.0)

        # Log data for plots
        vlref_rec.append(vlref)
        vrref_rec.append(vrref)
        x_rec.append(pose.x)
        y_rec.append(pose.y)
        theta_rec.append(pose.theta)
        vl_rec.append(vl)
        vr_rec.append(vr)
        ul_rec.append(drivetrain.u[0, 0])
        ur_rec.append(drivetrain.u[1, 0])

        # Update nonlinear observer
        pose.x += vc * math.cos(pose.theta) * dt
        pose.y += vc * math.sin(pose.theta) * dt
        pose.theta += omega * dt

        if i < len(t) - 1:
            i += 1

    plt.figure(1)
    plt.plot(x_rec, y_rec, label="LTV unicycle controller")
    plt.plot(xprof, yprof, label="Reference trajectory")
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")
    plt.legend()

    # Equalize aspect ratio
    xlim = plt.xlim()
    width = abs(xlim[0]) + abs(xlim[1])
    ylim = plt.ylim()
    height = abs(ylim[0]) + abs(ylim[1])
    if width > height:
        plt.ylim([-width / 2, width / 2])
    else:
        plt.xlim([-height / 2, height / 2])

    if "--noninteractive" in sys.argv:
        latex.savefig("ltv_unicycle_traj_xy")

    plt.figure(2)
    num_plots = 7
    plt.subplot(num_plots, 1, 1)
    plt.title("Time domain responses")
    plt.ylabel(
        "x position (m)",
        horizontalalignment="right",
        verticalalignment="center",
        rotation=45,
    )
    plt.plot(t[:-1], x_rec, label="Estimated state")
    plt.plot(t, xprof, label="Reference")
    plt.legend()
    plt.subplot(num_plots, 1, 2)
    plt.ylabel(
        "y position (m)",
        horizontalalignment="right",
        verticalalignment="center",
        rotation=45,
    )
    plt.plot(t[:-1], y_rec, label="Estimated state")
    plt.plot(t, yprof, label="Reference")
    plt.legend()
    plt.subplot(num_plots, 1, 3)
    plt.ylabel(
        "Theta (rad)",
        horizontalalignment="right",
        verticalalignment="center",
        rotation=45,
    )
    plt.plot(t[:-1], theta_rec, label="Estimated state")
    plt.plot(t, thetaprof, label="Reference")
    plt.legend()

    t = t[:-1]
    plt.subplot(num_plots, 1, 4)
    plt.ylabel(
        "Left velocity (m/s)",
        horizontalalignment="right",
        verticalalignment="center",
        rotation=45,
    )
    plt.plot(t, vl_rec, label="Estimated state")
    plt.plot(t, vlref_rec, label="Reference")
    plt.legend()
    plt.subplot(num_plots, 1, 5)
    plt.ylabel(
        "Right velocity (m/s)",
        horizontalalignment="right",
        verticalalignment="center",
        rotation=45,
    )
    plt.plot(t, vr_rec, label="Estimated state")
    plt.plot(t, vrref_rec, label="Reference")
    plt.legend()
    plt.subplot(num_plots, 1, 6)
    plt.ylabel(
        "Left voltage (V)",
        horizontalalignment="right",
        verticalalignment="center",
        rotation=45,
    )
    plt.plot(t, ul_rec, label="Control effort")
    plt.legend()
    plt.subplot(num_plots, 1, 7)
    plt.ylabel(
        "Right voltage (V)",
        horizontalalignment="right",
        verticalalignment="center",
        rotation=45,
    )
    plt.plot(t, ur_rec, label="Control effort")
    plt.legend()
    plt.xlabel("Time (s)")

    if "--noninteractive" in sys.argv:
        latex.savefig("ltv_unicycle_traj_response")
    else:
        plt.show()


if __name__ == "__main__":
    main()
