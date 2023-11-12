import random as rnd

import pandas as pd
import streamlit as st

from matplotlib.axes import Axes
import matplotlib.pyplot as plt

import solver

rnd.seed(0)
resource_names = ['cleaners', 'tractors']
capacities = [10, 1]

st.title(':snowflake: A-100')

left, right = st.columns(2)

num_zones = 6
priorities = [rnd.randint(1, 10) for _ in range(num_zones)]
column_names = [*(f'# {name}' for name in resource_names), 'x 30min']
pool = (
    pd.DataFrame([
        [5, 0, 4],
        [2, 1, 2]
    ], columns=column_names),
    pd.DataFrame([
        [3, 0, 3],
        [1, 1, 2]
    ], columns=column_names),
    pd.DataFrame([
        [4, 0, 4],
        [2, 1, 2]
    ], columns=column_names)
)
tables = [pool[i % len(pool)] for i in range(num_zones)]
zone_names = [f'Zone {i + 1}' for i in range(num_zones)]
with left:
    tabs = left.tabs(zone_names)
    for i, tab in enumerate(tabs):
        priorities[i] = tab.number_input(
            f'Priority:', min_value=0, value=priorities[i], key=f'{i}:priority')
        tab.text('Modes:')
        tables[i] = tab.data_editor(
            tables[i], num_rows='dynamic', key=f'{i}:tables')


with right:
    for i, name in enumerate(resource_names):
        capacities[i] = st.number_input(f'Total number of {name}:', min_value=0,
                                        value=capacities[i])


def draw_box(
    ax: Axes,
    x: int,
    y: int,
    w: int,
    h: int,
    label: str = '',
    **kwargs
) -> None:
    ax.fill(
        [x, x + w, x + w, x, x],
        [y, y, y + h, y + h, y],
        **kwargs
    )
    ax.text(x + w / 2, y + h / 2, label,
            ha='center', va='center', fontsize=8, c='white')


num_hours = 7
num_time_slots = 2 * num_hours

if right.button('Schedule'):
    st.divider()
    zones: list[solver.Zone] = []
    for i, table in enumerate(tables):
        modes: list[solver.Mode] = []
        for _, row in table.iterrows():
            try:
                duration = int(row['x 30min'])
                demands = [int(demand) for demand in row[:-1]]
            except:
                continue
            modes.append(solver.Mode(duration=duration, demands=demands))
        zones.append(solver.Zone(modes=modes, priority=priorities[i]))
    items = solver.make_schedule(zones, num_time_slots, capacities)

    min_start = min((item['start'] for item in items), default=num_time_slots)
    workload = [[0] * len(resource_names)
                for _ in range(num_time_slots - min_start)]
    ax: Axes = plt.gca()
    for i, item in enumerate(items):
        zone_index = item['zone']
        mode_index = item['mode']
        mode = zones[zone_index]['modes'][mode_index]
        label = f'{zone_names[zone_index]}\n'
        label += '\n'.join(f'{resource_names[j]}: {demand}'
                           for j, demand in enumerate(mode['demands']))
        x = item['start']
        y = 3 * i
        w = mode['duration']
        draw_box(ax, x=x, y=y, w=w, h=2, label=label,
                 c=(0, 104 / 255, 201 / 255))
        for j, demand in enumerate(mode['demands']):
            for k in range(x, x + mode['duration']):
                workload[k - min_start][j] += demand
    ax.get_yaxis().set_visible(False)
    ticks = range(min_start, num_time_slots + 1)
    labels = [
        f'{11 + tick // 2}:00' if tick % 2 == 0 else f'{11 + tick // 2}:30'
        for tick in ticks
    ]
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels)

    with st.expander('Gantt chart', expanded=False):
        st.pyplot(ax.figure)

    with st.expander('Workload', expanded=False):
        index = [labels[i - 1] + ' - ' + labels[i]
                 for i in range(1, len(labels))]
        st.bar_chart(pd.DataFrame(
            workload, index=index, columns=resource_names))
