import os
import shlex
from typing import Callable, Optional, Union
from warnings import warn

import pytest

from tests.support.compare_rdf import compare_rdf
from tests.support.dirutils import make_and_clear_directory
from tests.support.test_environment import TestEnvironment, create_test_environment_fixture


# Module-level constants for pytest-based tests
TEST_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "output"))
TEMP_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "temp"))


def create_click_test_fixtures(env_instance: TestEnvironment, testdir: str, click_ep, prog_name: str):
    """
    Factory function to create pytest fixtures for Click-based command line testing.
    
    Usage:
        env = TestEnvironment(__file__)
        testdir = "my_tests"
        click_ep = my_click_entry_point
        prog_name = "my_prog"
        
        click_fixtures = create_click_test_fixtures(env, testdir, click_ep, prog_name)
        click_env = click_fixtures['click_env']
        do_test = click_fixtures['do_test']
    
    Args:
        env_instance: TestEnvironment instance
        testdir: subdirectory within outdir
        click_ep: entry point for particular function
        prog_name: executable name
    
    Returns:
        Dictionary containing pytest fixtures
    """
    
    @pytest.fixture(scope="class")
    def click_env():
        """Click test environment fixture."""
        if env_instance:
            env_instance.make_testing_directory(env_instance.tempdir, clear=True)
        yield {
            'env': env_instance,
            'testdir': testdir,
            'click_ep': click_ep,
            'prog_name': prog_name,
            'test_base_dir': TEST_BASE_DIR,
            'temp_base_dir': TEMP_BASE_DIR,
        }
        
        # Cleanup - equivalent to tearDownClass
        if env_instance:
            msg = str(env_instance)
            env_instance.clear_log()
            if msg and env_instance.report_errors:
                print(msg)
    
    @pytest.fixture
    def do_test(click_env):
        """Fixture providing the do_test functionality."""
        def _do_test(
            args: Union[str, list[str]],
            testFileOrDirectory: Optional[str] = None,
            *,
            expected_error: type(Exception) = None,
            filtr: Optional[Callable[[str], str]] = None,
            is_directory: bool = False,
            add_yaml: bool = True,
            comparator: Callable[[str, str], Optional[str]] = None,
        ) -> None:
            """Execute a command test (pytest version)"""
            return _do_click_test(
                click_env, args, testFileOrDirectory,
                expected_error=expected_error,
                filtr=filtr,
                is_directory=is_directory,
                add_yaml=add_yaml,
                comparator=comparator
            )
        return _do_test
    
    return {
        'click_env': click_env,
        'do_test': do_test,
    }


def _do_click_test(
    click_env_data: dict,
    args: Union[str, list[str]],
    testFileOrDirectory: Optional[str] = None,
    *,
    expected_error: type(Exception) = None,
    filtr: Optional[Callable[[str], str]] = None,
    is_directory: bool = False,
    add_yaml: bool = True,
    comparator: Callable[[str, str], Optional[str]] = None,
) -> None:
    """Execute a command test (helper function)"""
    env = click_env_data['env']
    testdir = click_env_data['testdir']
    click_ep = click_env_data['click_ep']
    prog_name = click_env_data['prog_name']
    
    assert testFileOrDirectory
    arg_list = shlex.split(args) if isinstance(args, str) else args

    if is_directory and (filtr or comparator):
        warn("filtr and comparator parameters aren't implemented for directory generation")

    if add_yaml and (not arg_list or arg_list[0] != "--help"):
        raise NotImplementedError("This is an artifact from elsewhere")
        # arg_list.insert(0, env.meta_yaml)
        # arg_list += ["--importmap", env.import_map, "--log_level", DEFAULT_LOG_LEVEL_TEXT]

    target = os.path.join(testdir, testFileOrDirectory)
    _temp_file_path(env, testdir, testdir, is_dir=True)

    def do_gen():
        if is_directory:
            env.generate_directory(
                target,
                lambda target_dir: click_ep(
                    arg_list + ["-d", target_dir], prog_name=prog_name, standalone_mode=False
                ),
            )
        else:
            env.generate_single_file(
                target,
                lambda: click_ep(arg_list, prog_name=prog_name, standalone_mode=False),
                filtr=filtr,
                comparator=comparator,
            )

    if expected_error:
        with pytest.raises(expected_error):
            do_gen()
        return
    else:
        do_gen()


# Helper functions (formerly instance methods)
def _source_file_path(env: TestEnvironment, *path: str) -> str:
    """Return the full file name of path in the input directory"""
    return env.input_path(*path)


def _expected_file_path(env: TestEnvironment, testdir: str, *path: str) -> str:
    """Return the fill file path of the script subdirectory in the output directory"""
    return env.expected_path(testdir, *path)


def _temp_file_path(env: TestEnvironment, testdir: str, *path: str, is_dir: bool = False) -> str:
    """Create subdirectory in the temp directory to hold path"""
    full_path = env.temp_file_path(testdir, *path)
    env.make_testing_directory(full_path if is_dir else os.path.dirname(full_path))
    return full_path


def _temp_directory(env: TestEnvironment, base: str) -> str:
    """
    Create a temporary directory and return the path
    
    :param env: TestEnvironment instance
    :param base: base directory name
    :return: directory path
    """
    env.make_testing_directory(env.tempdir, clear=True)
    new_directory = os.path.join(TEMP_BASE_DIR, base)
    make_and_clear_directory(new_directory)
    return new_directory


# Static comparison functions (unchanged)
def jsonld_comparator(expected_data: str, actual_data: str) -> str:
    """Compare expected data in json-ld format to actual data in json-ld format"""
    return compare_rdf(expected_data, actual_data, "json-ld")


def n3_comparator(expected_data: str, actual_data: str) -> str:
    """compare expected_data in n3 format to actual_data in n3 format"""
    return compare_rdf(expected_data, actual_data, "n3")


def rdf_comparator(expected_data: str, actual_data: str, fmt: Optional[str] = "turtle") -> str:
    """compare expected_data to actual_data using basic RDF comparator method"""
    return compare_rdf(expected_data, actual_data, fmt=fmt)


def always_pass_comparator(expected_data: str, new_data: str) -> Optional[str]:
    """
    No-op comparator -- everyone passes!

    :param expected_data:
    :param new_data:
    :return:
    """
    return None


def closein_comparison(expected_txt: str, actual_txt: str) -> None:
    """Assist with testing comparison -- zero in on the first difference in a big string

    @param expected_txt:
    @param actual_txt:
    """
    window = 30
    view = 120

    nw = nt = actual_txt.strip()
    ow = ot = expected_txt.strip()
    if ot != nt:
        offset = 0
        while nt and ot and nt[:window] == ot[:window]:
            offset += window
            nt = nt[window:]
            ot = ot[window:]
        offset = max(offset - view, 0)
        print("   - - EXPECTED - -")
        print(ow[offset : offset + view + view])
        print("\n   - - ACTUAL - -")
        print(nw[offset : offset + view + view])


# Legacy compatibility class - deprecated, use fixtures instead
class ClickTestCase:
    """
    DEPRECATED: Use create_click_test_fixtures() instead.
    
    Legacy compatibility for ClickTestCase. This is kept for backward compatibility
    but new tests should use the create_click_test_fixtures() function instead.
    
    Migration guide:
    
    Old unittest style:
        class MyTest(ClickTestCase):
            env = TestEnvironment(__file__)
            testdir = "mytests"
            click_ep = my_entry_point
            prog_name = "myprog"
            
            def test_something(self):
                self.do_test("args", "output.txt")
    
    New pytest style:
        env = TestEnvironment(__file__)
        click_fixtures = create_click_test_fixtures(env, "mytests", my_entry_point, "myprog")
        click_env = click_fixtures['click_env']
        do_test = click_fixtures['do_test']
        
        class TestMy:
            def test_something(self, do_test):
                do_test("args", "output.txt")
    """
    
    def __init__(self):
        import warnings
        warnings.warn(
            "ClickTestCase is deprecated. Use create_click_test_fixtures() instead.",
            DeprecationWarning,
            stacklevel=2
        )



# Helper functions for easy migration from ClickTestCase
def get_click_test_helpers(env: TestEnvironment, testdir: str):
    """Get helper functions for tests migrating from ClickTestCase."""
    return {
        'source_file_path': lambda *path: _source_file_path(env, *path),
        'expected_file_path': lambda *path: _expected_file_path(env, testdir, *path),
        'temp_file_path': lambda *path, is_dir=False: _temp_file_path(env, testdir, *path, is_dir=is_dir),
        'temp_directory': lambda base: _temp_directory(env, base),
    }
