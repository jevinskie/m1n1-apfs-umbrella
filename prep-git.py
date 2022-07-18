#!/usr/bin/env python3

import os
import pathlib
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from typing import Any, Callable, Union


class Path(type(pathlib.Path())):
    @contextmanager
    def chdir(self):
        orig_dir = Path().absolute()
        try:
            os.chdir(self)
            yield
        finally:
            os.chdir(orig_dir)


ROOT_DIR = Path(__file__).parent

upstream_submodules = {
    "musl": {
        "url": "https://github.com/bminor/musl",
        "branch": "master",
    },
}


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


def gen_cmd(bin_name: str) -> Callable[..., subprocess.CompletedProcess]:
    bin_path = shutil.which(bin_name)
    assert bin_path is not None
    return lambda *args, **kwargs: run_cmd(bin_path, *args, **kwargs)


GIT = gen_cmd("git")


SUBMOD_CONFIG_PAT = re.compile('\[submodule\s+"(.*?)"]')
SUBMOD_PATH_PAT = re.compile("\s+path\s+= (.*)")
SUBMOD_URL_PAT = re.compile("\s+url\s+= (.*)")
SUBMOD_BRANCH_PAT = re.compile("\s+branch\s+= (.*)")


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
                submods[current_mod]["path"] = Path(path_match.group(1))
            url_match = SUBMOD_URL_PAT.match(line)
            if url_match:
                submods[current_mod]["url"] = url_match.group(1)
            branch_match = SUBMOD_BRANCH_PAT.match(line)
            if branch_match:
                submods[current_mod]["branch"] = branch_match.group(1)
        return submods


def config_module(mod_path, upstream_url, upstream_branch):
    with mod_path.chdir():
        if any([l.startswith("upstream\t") for l in GIT("remote", "-v").out.splitlines()]):
            return
        GIT("remote", "add", "upstream", upstream_url)
        GIT("fetch", "--all")


def fetch_module(mod_path):
    with mod_path.chdir():
        GIT("fetch", "--all")


def main():
    os.chdir(ROOT_DIR)
    submods = parse_submodules()
    print(submods)
    for mod in submods.values():
        path = mod["path"]
        remote_cfg = upstream_submodules[str(path)]
        config_module(path, remote_cfg["url"], remote_cfg["branch"])


if __name__ == "__main__":
    main()
