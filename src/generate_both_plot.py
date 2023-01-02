import matplotlib.pyplot as plt
import numpy as np
import os
import csv

t = []
c = []
r = []
f = []
fr = []
crash = []
vel = []
before = []
after = []

os.chdir('/home/heven/CoDeep_ws/src/yolov5_ros/src/csv/test')

with open('radar_test.csv', 'r') as csvfile:
    lines = csv.reader(csvfile, delimiter=',')
    for row in lines:
        t.append(float(row[0]))
        vel.append(float(row[1]))
        r.append(float(row[2]))
        # f.append(float(row[4]))
        # fr.append(float(row[5]))
        # vel.append(float(row[0]))

csvfile.close()

# with open('1d_kalman_velocity_test.csv', 'r') as csv2:
#     line = csv.reader(csv2, delimiter=',')
#     for r in line:
#         after.append(float(r[0]))

# print(after)

# print(c)

# fig = plt.figure(figsize=(30, 13))
fig, ax1 = plt.subplots(figsize=(30,13))
ax1.plot(t, r, color = "orange", label="Distance [m]")
ax1.legend(loc='upper left', fontsize=28)
ax1.set_xlabel('Time [s]', fontsize=20)
ax1.set_ylabel('Distance [m]', fontsize=20)
ax1.tick_params(axis='x', labelsize=20)
ax1.tick_params(axis='y', labelsize=20)
ax2 = ax1.twinx()
ax2.plot(t, vel, color = "green", label="Velocity [m/s]")
ax2.legend(loc='upper right', fontsize=28)
ax2.set_ylabel('Velocity [m/s]', fontsize=20)
ax2.tick_params(axis='x', labelsize=20)
ax2.tick_params(axis='y', labelsize=20)

# print(len(c))
# print(len(r))
# print(len(f))
time = np.array(t)
reference = 46.72 - 1.4 * time

# plt.plot(time, c, linestyle="--", color = "blue", linewidth = 3)
# plt.plot(time, r, linestyle="--", color = "orange", linewidth = 3)
# plt.plot(time, f, linestyle="-", color = "green", linewidth = 5)
# plt.plot(time, reference, linestyle="-", color = "red", linewidth = 3)
# plt.plot(time, fr, linestyle="--", color = "black", linewidth = 3)
# plt.plot(x, crash, linestyle = "-", color = "green", linewidth = 5)
# plt.plot(x, vel, linestyle="-", color = "green", linewidth = 5)
# plt.plot(x, before, linestyle="-", color = "black", linewidth = 3)
# plt.plot(x, after, linestyle="-", color = "green", linewidth = 5)
# plt.xlabel("Time [s]", fontsize=20)
# plt.ylabel("Distance [m]", fontsize=20)
# plt.ylabel("Velocity [m/s]", fontsize=20)
plt.xticks(fontsize=20)
plt.yticks(fontsize=20)

# plt.ylim([-2.5, 2.5])
# plt.hlines(float(-5/3.6), 0, 747, colors="red", linewidth=3)
# plt.legend(['Distance', 'Velocity'], fontsize= 28)
# plt.legend(["Velocity"], fontsize=28)
# plt.legend(['Crash Time'], fontsize= 28)
# plt.legend(["Before Kalman Filter", "After Kalman Filter"], fontsize=28)
# plt.legend(["Crash Time"], fontsize=28)

# ax1 = fig.add_subplot(1, 1, 1)
# ax1.plot(x, c, color = 'red', label='Camera')
# ax1.tick_params(axis='y', labelcolor="red")

# ax2 = fig.add_subplot(1, 1, 1)
# ax2.plot(x, r, color = "green", label='Radar')
# ax2.tick_params(axis='y', labelcolor="green")
# # ax2.legend(loc="upper right")

# ax3 = fig.add_subplot(1, 1, 1)
# ax3.plot(x, f, color = "blue", label='Fusion')
# ax3.tick_params(axis='y', labelcolor='blue')
# # ax3.legend(loc="upper right")

plt.show()