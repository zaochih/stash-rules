#!/usr/bin/env python3
"""检查手写规则里有哪些条目已经被某个 geosite 列表收录，生成 Markdown 报告。

只报告，不修改任何文件。没有可移除的条目时不生成报告文件。

注意：这里只判断“是否被该列表覆盖”，不判断规则顺序。
手写规则通常排在该列表之前，删除后命中的规则会变晚，中间的规则可能先截走这个域名。
"""
import argparse
import os
import sys
from pathlib import Path


def read_entries(path: Path):
    """yield (原始写法, 域名, 是否后缀匹配)。`+.x` / `.x` / `*.x` 视为后缀，其余为精确域名。"""
    for line in path.read_text().splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        for prefix in ("+.", "*.", "."):
            if line.startswith(prefix):
                yield line, line[len(prefix):], True
                break
        else:
            yield line, line, False


def read_geosite(path: Path):
    """读取 v2fly 官方工具导出的明文，返回 (后缀集合, 精确域名集合)。"""
    suffixes, fulls = set(), set()
    for line in path.read_text().splitlines():
        typ, _, rest = line.strip().partition(":")
        value = rest.partition(":@")[0]
        if typ == "domain":
            suffixes.add(value)
        elif typ == "full":
            fulls.add(value)
    return suffixes, fulls


def covered_by(domain: str, is_suffix: bool, suffixes: set[str], fulls: set[str]):
    """返回覆盖该条目的规则（字符串），没有则返回 None。"""
    parts = domain.split(".")
    for i in range(len(parts)):
        parent = ".".join(parts[i:])
        if parent in suffixes:
            return f"domain:{parent}"
    if not is_suffix and domain in fulls:
        return f"full:{domain}"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule-set", type=Path, default=Path("rule-set/can-be-direct"))
    ap.add_argument("--plain-dir", type=Path, required=True)
    ap.add_argument("--against", default="geolocation-cn")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    suffixes, fulls = read_geosite(args.plain_dir / f"{args.against}.txt")
    redundant = []
    for raw, domain, is_suffix in read_entries(args.rule_set):
        by = covered_by(domain, is_suffix, suffixes, fulls)
        if by:
            redundant.append((raw, by))

    args.out.unlink(missing_ok=True)
    if not redundant:
        print(f"{args.rule_set}: 没有被 {args.against} 收录的条目")
        return 0

    run_url = ""
    if os.environ.get("GITHUB_RUN_ID"):
        run_url = "{}/{}/actions/runs/{}".format(
            os.environ.get("GITHUB_SERVER_URL", "https://github.com"),
            os.environ["GITHUB_REPOSITORY"],
            os.environ["GITHUB_RUN_ID"],
        )
    lines = [
        f"`{args.rule_set}` 中有 {len(redundant)} 个条目已被上游 `{args.against}` 收录，可以考虑移除：",
        "",
        "| 条目 | 被哪条上游规则覆盖 |",
        "|---|---|",
        *[f"| `{raw}` | `{by}` |" for raw, by in redundant],
        "",
        "> **删除前请确认规则顺序。** 这里只检查了是否被收录，没有检查配置里的规则顺序。"
        f"手写规则通常排在 `{args.against}` 之前，删掉后这个域名会更晚才命中，中间的规则可能先截走它。",
        "",
        "处理完成（移除条目并推送）后，下一次构建会自动关闭这个 issue。",
    ]
    if run_url:
        lines += ["", f"由 [构建任务]({run_url}) 自动生成。"]
    args.out.write_text("\n".join(lines) + "\n")
    print(f"{args.rule_set}: {len(redundant)} 个条目已被 {args.against} 收录，已生成 {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
