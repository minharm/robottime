import math
from typing import Dict, List, Tuple

def calculate_axis_move_time(dist: float, spec: Dict[str, float]) -> float:
    """
    dist: mm
    spec: {"acc": mm/s^2, "dec": mm/s^2, "vel": mm/s}
    """
    if dist <= 0:
        return 0.0

    acc = float(spec["acc"])
    dec = float(spec["dec"])
    vel = float(spec["vel"])

    if acc <= 0 or dec <= 0 or vel <= 0:
        raise ValueError("acc, dec, vel must be > 0")

    # 최고속도 도달 시 필요한 거리
    d_acc = (vel ** 2) / (2 * acc)
    d_dec = (vel ** 2) / (2 * dec)
    d_total = d_acc + d_dec

    # 1) 사다리꼴 프로파일: 최고속도 도달 가능
    if dist >= d_total:
        t_acc = vel / acc
        t_dec = vel / dec
        d_const = dist - d_total
        t_const = d_const / vel
        return t_acc + t_const + t_dec

    # 2) 삼각 프로파일: 최고속도 도달 불가
    # peak velocity를 다시 계산
    v_peak = math.sqrt((2 * dist * acc * dec) / (acc + dec))
    t_acc = v_peak / acc
    t_dec = v_peak / dec
    return t_acc + t_dec


def calculate_step_time(dist: float, delay: float, spec: Dict[str, float]) -> Tuple[float, float]:
    move_time = calculate_axis_move_time(dist, spec)
    total_time = move_time + max(delay, 0)
    return move_time, total_time


def calculate_sequence(rows: List[Dict], specs: Dict) -> Dict:
    """
    rows 예시:
    [
      {"name":"금형진입", "axis":"Z", "dist":500, "delay":0.1, "is_takeout":True, "group":1},
      {"name":"횡이동", "axis":"X", "dist":800, "delay":0.0, "is_takeout":True, "group":1},
      {"name":"취출대기", "axis":"X", "dist":0, "delay":0.2, "is_takeout":True, "group":2},
    ]

    group이 같으면 동시이동으로 계산:
    그룹 내 총시간 = max(각 row의 step_time)
    """
    results = []
    grouped = {}

    for i, row in enumerate(rows):
        axis = row["axis"]
        if axis not in specs:
            raise KeyError(f"축 사양 없음: {axis}")

        move_t, step_t = calculate_step_time(row["dist"], row["delay"], specs[axis])

        item = {
            "idx": i + 1,
            "name": row["name"],
            "axis": axis,
            "dist": row["dist"],
            "delay": row["delay"],
            "is_takeout": row["is_takeout"],
            "group": row.get("group", i + 1),
            "move_time": move_t,
            "step_time": step_t,
        }
        results.append(item)

        g = item["group"]
        grouped.setdefault(g, []).append(item)

    total_time = 0.0
    takeout_time = 0.0
    group_summary = []

    for g in sorted(grouped.keys()):
        items = grouped[g]
        group_time = max(x["step_time"] for x in items)
        takeout_group_time = max((x["step_time"] for x in items if x["is_takeout"]), default=0.0)

        total_time += group_time
        takeout_time += takeout_group_time

        group_summary.append({
            "group": g,
            "count": len(items),
            "group_time": group_time,
            "takeout_group_time": takeout_group_time
        })

    return {
        "rows": results,
        "groups": group_summary,
        "takeout_time": takeout_time,
        "total_time": total_time
    }
