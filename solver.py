from typing import TypedDict

from ortools.sat.python import cp_model


class Mode(TypedDict):
    duration: int
    demands: list[int]


class Zone(TypedDict):
    modes: list[Mode]
    priority: int


class Item(TypedDict):
    zone: int
    start: int
    mode: int


def make_schedule(
    zones: list[Zone],
    num_time_slots: int,
    capacities: list[int]
) -> list[Item] | None:
    start_times: list[cp_model.IntVar] = []
    table: list[list[cp_model.IntVar]] = []
    interval_groups: list[list[cp_model.IntervalVar]] = []
    finish_times: list[cp_model.IntVar] = []
    model = cp_model.CpModel()
    for zone in zones:
        start = model.NewIntVar(0, num_time_slots - 1, '')
        start_times.append(start)
        literals: list[cp_model.IntVar] = []
        intervals: list[cp_model.IntervalVar] = []
        for mode in zone['modes']:
            literal = model.NewBoolVar('')
            literals.append(literal)
            interval = model.NewOptionalFixedSizeIntervalVar(
                start, mode['duration'], literal, '')
            intervals.append(interval)
        table.append(literals)
        interval_groups.append(intervals)
        active = model.NewBoolVar('')
        model.Add(cp_model.LinearExpr.Sum(literals) == active)
        finish = model.NewIntVar(0, num_time_slots, '')
        finish_times.append(finish)
        duration = cp_model.LinearExpr.WeightedSum(
            literals, [mode['duration'] for mode in zone['modes']])
        model.Add(finish == start + duration).OnlyEnforceIf(active)
        model.Add(finish == 0).OnlyEnforceIf(active.Not())
    for i, capacity in enumerate(capacities):
        intervals: list[cp_model.IntervalVar] = []
        demands: list[int] = []
        for j, zone in enumerate(zones):
            for k, mode in enumerate(zone['modes']):
                if (demand := mode['demands'][i]):
                    intervals.append(interval_groups[j][k])
                    demands.append(demand)
        model.AddCumulative(intervals, demands, capacity)
    objective = cp_model.LinearExpr.WeightedSum(
        finish_times, [zone['priority'] for zone in zones])
    model.Maximize(objective)
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print(f'status: {solver.StatusName(status)} ({solver.WallTime():.3f}s)')
    if status == cp_model.OPTIMAL:
        result: list[Item] = []
        for i, literals in enumerate(table):
            start = solver.Value(start_times[i])
            for j, literal in enumerate(literals):
                if solver.BooleanValue(literal):
                    result.append(Item(zone=i, start=start, mode=j))
                    break
        return result
    return None
