"""보드가 보낸 실행 구간 트레이스를 간트 차트로 그린다.

사용법
  python plot_trace.py --port COM5          # 시리얼에서 한 번 받아 그리기
  python plot_trace.py --file trace.txt     # 저장해 둔 로그에서 그리기
  python plot_trace.py --port COM5 --save trace.txt

필요 패키지: pip install matplotlib pyserial
"""
import argparse
from collections import defaultdict


def extract_trace(lines):
    """TRACE_BEGIN ~ TRACE_END 사이의 마지막 블록을 (task, start, end) 목록으로."""
    block, current = None, None
    for line in lines:
        line = line.strip()
        if line == "TRACE_BEGIN":
            current = []
        elif line == "TRACE_END" and current is not None:
            block, current = current, None
        elif current is not None and line and not line.startswith("task,"):
            task, s, e = line.split(",")
            current.append((task, int(s), int(e)))
    if block is None:
        raise SystemExit("TRACE_BEGIN/TRACE_END 블록을 찾지 못했습니다.")
    return block


def read_serial(port, baud, timeout_s):
    import serial  # pyserial

    lines, capturing = [], False
    with serial.Serial(port, baud, timeout=timeout_s) as ser:
        while True:
            raw = ser.readline()
            if not raw:
                raise SystemExit(f"{timeout_s}초 동안 데이터가 없습니다. 포트와 보드 상태를 확인하세요.")
            line = raw.decode(errors="ignore").rstrip()
            if line.startswith("#"):
                print(line)
            if line == "TRACE_BEGIN":
                capturing, lines = True, []
            if capturing:
                lines.append(line)
            if capturing and line == "TRACE_END":
                return lines


def summarize(segs):
    by_task = defaultdict(list)
    for task, s, e in segs:
        by_task[task].append(e - s)
    print(f"구간 수: {len(segs)}")
    for task in sorted(by_task):
        d = by_task[task]
        print(f"  {task}: {len(d)}번 실행, 평균 {sum(d) / len(d):.0f}us, "
              f"최대 {max(d)}us, 총 {sum(d) / 1000:.1f}ms")


def plot(segs):
    import matplotlib.pyplot as plt

    tasks = sorted({t for t, _, _ in segs})
    fig, ax = plt.subplots(figsize=(12, 1 + 0.8 * len(tasks)))
    for row, task in enumerate(tasks):
        bars = [(s / 1000, (e - s) / 1000) for t, s, e in segs if t == task]
        ax.broken_barh(bars, (row - 0.35, 0.7))
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels(tasks)
    ax.set_xlabel("time (ms)")
    ax.set_title("FreeRTOS task execution timeline")
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.show()


def main():
    p = argparse.ArgumentParser()
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--port")
    src.add_argument("--file")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--timeout", type=float, default=15)
    p.add_argument("--save", help="받은 로그를 파일로 저장")
    p.add_argument("--no-plot", action="store_true")
    args = p.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            lines = f.read().splitlines()
    else:
        lines = read_serial(args.port, args.baud, args.timeout)
        if args.save:
            with open(args.save, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")

    segs = extract_trace(lines)
    summarize(segs)
    if not args.no_plot:
        plot(segs)


if __name__ == "__main__":
    main()
