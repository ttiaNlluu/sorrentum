#!/usr/bin/env python

"""
Implement several Git workflows on multiple repos.

# Show the current state of the submodules:
  ```
  > dev_scripts/git/git_submodules.py
  ```
"""

import argparse
import logging
from typing import List

import helpers.dbg as dbg
import helpers.git as git
import helpers.parser as prsr
import helpers.system_interaction as si

_LOG = logging.getLogger(__name__)


def _pull(dir_names: List[str], short_hash: bool) -> None:
    _LOG.info("status=\n%s", git.report_submodule_status(dir_names, short_hash))
    for dir_name in dir_names:
        cmd = f"cd {dir_name} && git pull --autostash"
        si.system(cmd)
    _LOG.info("status=\n%s", git.report_submodule_status(dir_names, short_hash))


def _show(dir_names: List[str], short_hash: bool) -> None:
    print(git.report_submodule_status(dir_names, short_hash))


def _clean(dir_names: List[str]) -> None:
    for dir_name in dir_names:
        cmd = f"cd {dir_name} && git clean -fd"
        si.system(cmd)


def _roll_fwd(dir_names: List[str], auto_commit: bool, short_hash: bool) -> None:
    # Pull.
    _pull(dir_names, short_hash)
    # Add changes.
    for dir_name in dir_names:
        cmd = f"git add {dir_name}"
        si.system(cmd)
    # Commit.
    cmd = 'git commit -am "Move forward git submodules" && git push'
    if auto_commit:
        si.system(cmd)
    else:
        script_name = "./tmp_push.sh"
        si.create_executable_script(script_name, cmd)
        msg: List[str] = []
        msg.append("Run:")
        msg.append(f"> {cmd}")
        msg.append("or")
        msg.append(f"> {script_name}")
        msg_as_str = "\n".join(msg)
        print(msg_as_str)
    #
    _LOG.info("status=\n%s", git.report_submodule_status(dir_names, short_hash))


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--pull", action="store_true")
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--roll_fwd", action="store_true")
    parser.add_argument("--auto_commit", action="store_true")
    parser.add_argument("--long_hash", action="store_true")
    prsr.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    dbg.init_logger(verbosity=args.log_level, use_exec_path=False)
    #
    dir_names = git.get_repo_dirs()
    _LOG.info("dir_names=%s", dir_names)
    short_hash = not args.long_hash
    if args.pull:
        _pull(dir_names, short_hash)
    if args.show:
        _show(dir_names, short_hash)
    if args.roll_fwd:
        _roll_fwd(dir_names, args.auto_commit, short_hash)


if __name__ == "__main__":
    _main(_parse())
