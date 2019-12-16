import logging
import os

import pytest

import helpers.env as env
import helpers.git as git
import helpers.list as hlist
import helpers.printing as prnt
import helpers.s3 as hs3
import helpers.system_interaction as si
import helpers.unit_test as ut
import helpers.user_credentials as usc

_LOG = logging.getLogger(__name__)

# #############################################################################
# env.py
# #############################################################################


class Test_env1(ut.TestCase):
    def test_get_system_signature1(self):
        txt = env.get_system_signature()
        _LOG.debug(txt)


# #############################################################################
# git.py
# #############################################################################


class Test_git1(ut.TestCase):
    """
    Unfortunately we can't check the outcome of some of these functions since we
    don't know in which dir we are running. Thus we test that the function
    completes and visually inspect the outcome, if needed.
    TODO(gp): If we have Jenkins on AM side we could test for the outcome at
     least in that set-up.
    """

    @staticmethod
    def _helper(func_call):
        act = eval(func_call)
        _LOG.debug("%s=%s", func_call, act)

    def test_get_git_name1(self):
        func_call = "git.get_repo_symbolic_name(super_module=True)"
        self._helper(func_call)

    def test_is_inside_submodule1(self):
        func_call = "git.is_inside_submodule()"
        self._helper(func_call)

    def test_get_client_root1(self):
        func_call = "git.get_client_root(super_module=True)"
        self._helper(func_call)

    def test_get_client_root2(self):
        func_call = "git.get_client_root(super_module=False)"
        self._helper(func_call)

    def test_get_path_from_git_root1(self):
        file_name = "helpers/test/test_helpers.py"
        act = git.get_path_from_git_root(file_name, super_module=False)
        _LOG.debug("get_path_from_git_root()=%s", act)

    def test_get_repo_symbolic_name1(self):
        func_call = "git.get_repo_symbolic_name(super_module=True)"
        self._helper(func_call)

    def test_get_repo_symbolic_name2(self):
        func_call = "git.get_repo_symbolic_name(super_module=False)"
        self._helper(func_call)

    def test_get_modified_files1(self):
        func_call = "git.get_modified_files()"
        self._helper(func_call)

    def test_get_previous_committed_files1(self):
        func_call = "git.get_previous_committed_files()"
        self._helper(func_call)

    def test_git_log1(self):
        func_call = "git.git_log()"
        self._helper(func_call)

    def test_git_log2(self):
        func_call = "git.git_log(my_commits=True)"
        self._helper(func_call)

    def test_git_all_repo_symbolic_names1(self):
        func_call = "git.get_all_repo_symbolic_names()"
        self._helper(func_call)

    def test_git_all_repo_symbolic_names2(self):
        all_repo_sym_names = git.get_all_repo_symbolic_names()
        for repo_sym_name in all_repo_sym_names:
            repo_github_name = git.get_repo_github_name(repo_sym_name)
            _LOG.debug(
                ut.to_string("repo_sym_name")
                + " -> "
                + ut.to_string("repo_github_name")
            )
            git.get_repo_prefix(repo_github_name)
            _LOG.debug(
                ut.to_string("repo_sym_name")
                + " -> "
                + ut.to_string("repo_sym_name_tmpA")
            )

    def test_get_amp_abs_path1(self):
        amp_dir = git.get_amp_abs_path()
        # Check.
        self.assertTrue(os.path.exists(amp_dir))
        if si.get_user_name() != "jenkins":
            # Jenkins checks out amp repo in directories with different names,
            # e.g., amp.dev.build_clean_env.run_slow_coverage_tests.
            self.assert_equal(os.path.basename(amp_dir), "amp")

    def test_get_branch_name(self):
        _ = git.get_branch_name()

    @pytest.mark.skipif('si.get_user_name() == "jenkins"', reason="#781")
    @pytest.mark.skipif(
        'git.get_repo_symbolic_name(super_module=False) == "alphamatic/amp"'
    )
    def test_get_submodule_hash(self):
        _ = git.get_submodule_hash("amp")

    def test_get_hash_head(self):
        _ = git.get_hash_head(".")


# #############################################################################
# list.py
# #############################################################################


class Test_list_1(ut.TestCase):
    def test_find_duplicates1(self):
        list_ = "a b c d".split()
        list_out = hlist.find_duplicates(list_)
        self.assertEqual(list_out, [])

    def test_find_duplicates2(self):
        list_ = "a b c a d e f f".split()
        list_out = hlist.find_duplicates(list_)
        self.assertEqual(set(list_out), set("a f".split()))

    def test_remove_duplicates1(self):
        list_ = "a b c d".split()
        list_out = hlist.remove_duplicates(list_)
        self.assertEqual(list_out, "a b c d".split())

    def test_remove_duplicates2(self):
        list_ = "a b c a d e f f".split()
        list_out = hlist.remove_duplicates(list_)
        self.assertEqual(list_out, "a b c d e f".split())

    def test_remove_duplicates3(self):
        list_ = "a b c a d e f f".split()
        list_ = list(reversed(list_))
        list_out = hlist.remove_duplicates(list_)
        self.assertEqual(list_out, "f e d a c b".split())


# #############################################################################
# numba.py
# #############################################################################


class Test_numba_1(ut.TestCase):
    def test1(self):
        # TODO(gp): Implement this.
        pass


# #############################################################################
# numba.py
# #############################################################################


class Test_printing1(ut.TestCase):
    def test_color_highlight1(self):
        for c in prnt.COLOR_MAP:
            _LOG.debug(prnt.color_highlight(c, c))


# #############################################################################
# s3.py
# #############################################################################


class Test_s3_1(ut.TestCase):
    def test_get_path1(self):
        file_path = (
            "s3://default00-bucket/kibot/All_Futures_Continuous_Contracts_daily"
        )
        bucket_name, file_path = hs3.parse_path(file_path)
        self.assertEqual(bucket_name, "default00-bucket")
        self.assertEqual(
            file_path, "kibot/All_Futures_Continuous_Contracts_daily"
        )

    @pytest.mark.slow
    def test_ls1(self):
        file_path = os.path.join(
            hs3.get_path(), "kibot/All_Futures_Continuous_Contracts_daily"
        )
        file_names = hs3.ls(file_path)
        # We rely on the fact that Kibot data is not changing.
        self.assertEqual(len(file_names), 252)


# #############################################################################
# unit_test.py
# #############################################################################

class Test_unit_test1(ut.TestCase):
    @pytest.mark.amp
    def test_purify_txt_from_client1(self):
        super_module_path = git.get_client_root(super_module=True)
        # TODO(gp): We should remove the current path.
        txt = r"""
************* Module input [pylint]
$SUPER_MODULE/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py: Your code has been rated at -10.00/10 (previous run: -10.00/10, +0.00) [pylint]
$SUPER_MODULE/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3:20: W605 invalid escape sequence '\s' [flake8]
$SUPER_MODULE/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3:9: F821 undefined name 're' [flake8]
cmd line='$SUPER_MODULE/dev_scripts/linter.py -f $SUPER_MODULE/amp/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py --linter_log $SUPER_MODULE/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/linter.log'
dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3: [E0602(undefined-variable), ] Undefined variable 're' [pylint]
dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3: [W1401(anomalous-backslash-in-string), ] Anomalous backslash in string: '\s'. String constant might be missing an r prefix. [pylint]
dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3: error: Name 're' is not defined [mypy]
"""
        txt = txt.replace("$SUPER_MODULE", super_module_path)
        exp = r"""
************* Module input [pylint]
$GIT_ROOT/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py: Your code has been rated at -10.00/10 (previous run: -10.00/10, +0.00) [pylint]
$GIT_ROOT/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3:20: W605 invalid escape sequence '\s' [flake8]
$GIT_ROOT/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3:9: F821 undefined name 're' [flake8]
cmd line='$GIT_ROOT/dev_scripts/linter.py -f $GIT_ROOT/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py --linter_log $GIT_ROOT/dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/linter.log'
dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3: [E0602(undefined-variable), ] Undefined variable 're' [pylint]
dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3: [W1401(anomalous-backslash-in-string), ] Anomalous backslash in string: '\s'. String constant might be missing an r prefix. [pylint]
dev_scripts/test/Test_linter_py1.test_linter1/tmp.scratch/input.py:3: error: Name 're' is not defined [mypy]
"""
        act = ut.purify_txt_from_client(txt)
        self.assert_equal(act, exp)


# #############################################################################
# user_credentials.py
# #############################################################################


class Test_user_credentials1(ut.TestCase):
    def test_get_credentials1(self):
        data = usc.get_credentials()
        _LOG.debug("data=%s", data)
