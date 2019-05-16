#!/usr/bin/env python

# Note that this file must run with python2.7 to bootstrap conda.

import os

# TODO(gp): Not sure this is a good idea since it might create cyclic dependencies.
import helpers.dbg as dbg

# We cannot use system_interaction since it depends on python3, and this script is
# used to configure conda to use python3. So to break the cyclic dependency we inline
# the functions.
#import helpers.system_interaction as hsi


import subprocess

def _system_to_string(cmd):
    txt = subprocess.check_output(cmd)
    txt = [f for f in txt.split("\n") if f]
    dbg.dassert_eq(len(txt), 1)
    return txt[0]


_User_name = None

def _get_user_name():
    global _User_name
    if _User_name is None:
        _User_name = _system_to_string("whoami")
    return _User_name


_Server_name = None

def _get_server_name():
    global _Server_name
    if _Server_name is None:
        _Server_name = _system_to_string("uname -n")
    return _Server_name


def _get_conda_config():
    # TODO(*): Add your user and machine here.
    path = None
    conda_env_path = None
    if _get_user_name() == "saggese":
        path = "/Users/saggese/anaconda2/etc/profile.d/conda.sh"
        conda_env_path = "/Users/saggese/.conda/envs"
    elif _get_user_name() == "jenkins":
        path = "/data/shared/anaconda2/etc/profile.d/conda.sh"
        conda_env_path = "/data/jenkins/.conda/envs"
    #
    if path is None:
        raise RuntimeError("username='%s' servername='%s' did not set 'path'. "
                           "Add your information to this file." %
                           (_get_user_name(), _get_server_name()))
    path = os.path.abspath(path)
    dbg.dassert_exists(path)
    #
    if conda_env_path is None:
        raise RuntimeError(
            "username='%s' servername='%s' did not set 'conda_env_path'. "
            "Add your information to this file." % (_get_user_name(),
                                                    _get_server_name()))
    conda_env_path = os.path.abspath(conda_env_path)
    # Not necessarily the conda_env_path exists.
    return path, conda_env_path


def get_conda_config_path():
    path, conda_env_path = _get_conda_config()
    _ = conda_env_path
    return path


def get_conda_env_path():
    path, conda_env_path = _get_conda_config()
    _ = path
    return conda_env_path


def _main():
    path = get_conda_config_path()
    print(path)


if __name__ == '__main__':
    _main()
