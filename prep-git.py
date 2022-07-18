#!/usr/bin/env python3

import configparser
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable


def run_cmd(*args, log: bool = True):
    args = (*args,)
    if log:
        print(f"+ {' '.join(map(str, args))}", file=sys.stderr)
    r = subprocess.run(list(map(str, args)), capture_output=True)
    if r.returncode != 0:
        sys.stderr.buffer.write(r.stdout)
        sys.stderr.buffer.write(r.stderr)
        raise subprocess.CalledProcessError(r.returncode, args, r.stdout, r.stderr)
    try:
        r.out = r.stdout.decode()
    except UnicodeDecodeError:
        pass
    return r


def gen_cmd(bin_name: str) -> Callable:
    bin_path = shutil.which(bin_name)
    assert bin_path is not None
    return lambda *args, **kwargs: run_cmd(bin_path, *args, **kwargs)


GIT = gen_cmd("git")


SUBMOD_CONFIG_PAT = re.compile('\[submodule\s+"(.*?)"]')
SUBMOD_PATH_PAT = re.compile("\s+path = (.*)")
SUBMOD_URL_PAT = re.compile("\s+url = (.*)")


def parse_submodules():
    with open(".gitmodules") as f:
        submods = {}
        current_mod = None
        for line in f:
            line = line.rstrip("\n")
            cfg_match = SUBMOD_CONFIG_PAT.match(line)
            if cfg_match:
                current_mod = cfg_match.group(1)
                submods[current_mod] = {}
            path_match = SUBMOD_PATH_PAT.match(line)
            if path_match:
                submods[current_mod]["path"] = path_match.group(1)
            url_match = SUBMOD_URL_PAT.match(line)
            if url_match:
                submods[current_mod]["url"] = url_match.group(1)
        return submods


def main():
    os.chdir(Path(__file__).parent)
    submods = parse_submodules()
    print(submods)


if __name__ == "__main__":
    main()
