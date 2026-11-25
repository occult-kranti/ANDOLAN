"""List direct fork names using a bounded GitHub GraphQL cursor walk.

Requires an authenticated gh CLI. An output segment is portable. Supply
--after with its end_cursor to start the next segment at the previous boundary.
"""
import argparse
import json
from pathlib import Path
import subprocess

QUERY = """query($after:String) {
  repository(owner:"morluto",name:"rea") {
    forks(first:100,after:$after) {
      nodes { nameWithOwner } pageInfo { endCursor hasNextPage }
    }
  }
}"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="fresh segment JSON")
    parser.add_argument("--pages", type=int, default=5)
    parser.add_argument("--after", help="end_cursor from a previous GitHub page")
    args = parser.parse_args()
    if args.output.exists() or args.pages < 1:
        parser.error("use a fresh output path and positive page budget")
    cursor = args.after
    names = []
    pages = []
    for _ in range(args.pages):
        command = ["gh", "api", "graphql", "-f", "query=" + QUERY]
        if cursor:
            command += ["-f", "after=" + cursor]
        response = json.loads(subprocess.check_output(command, timeout=45))
        forks = response["data"]["repository"]["forks"]
        next_cursor = forks["pageInfo"]["endCursor"]
        more = forks["pageInfo"]["hasNextPage"]
        if more and (not next_cursor or cursor == next_cursor):
            raise ValueError("GitHub returned a nonadvancing fork cursor")
        rows = [n["nameWithOwner"] for n in forks["nodes"]]
        pages.append({"end_cursor": next_cursor, "row_count": len(rows)})
        names += rows
        cursor = next_cursor
        if not more:
            break
    result = {"query": QUERY, "start_cursor": args.after, "end_cursor": cursor,
              "has_next_page": more, "pages": pages, "names": names}
    with args.output.open("x") as out:
        json.dump(result, out, indent=2)
        out.write("\n")


if __name__ == "__main__":
    main()
