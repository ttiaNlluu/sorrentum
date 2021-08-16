"""
See helpers/cache/README.md for implementation details.

Import as:

import helpers.cache as hcache
"""

# TODO(gp): For code application, we might want to delete memory cache.
#  lru_cache doesn't survive different activations

import copy
import functools
import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast

import joblib
import joblib.func_inspect as jfunci
import joblib.memory as jmemor

import helpers.dbg as dbg
import helpers.git as git
import helpers.introspection as hintro
import helpers.io_ as hio
import helpers.system_interaction as hsyste

_LOG = logging.getLogger(__name__)

# TODO(gp): Do not commit this.
_LOG.debug = _LOG.info

# We try to keep aligned the interfaces of the global cache (i.e., the cache for all
# the functions) and the function-specific caches by:
# - using the same names for functions and variables, letting the fact that it's a
#   static method or a class method distinguish whether it's global or
#   function-specific


# #############################################################################


_IS_CACHE_ENABLED: bool = True


def set_caching(val: bool) -> None:
    """
    Enable or disable all caching, i.e., global, tagged global, function-
    specific.
    """
    global _IS_CACHE_ENABLED
    _LOG.warning("Setting caching to %s -> %s", _IS_CACHE_ENABLED, val)
    _IS_CACHE_ENABLED = val


def is_caching_enabled() -> bool:
    """
    Check if cache is enabled.

    :return: whether the cache is enabled or not
    """
    return _IS_CACHE_ENABLED


def get_global_cache_info() -> str:
    """
    Report information on global cache.
    """
    cache_types = _get_cache_types()
    txt = []
    txt.append("# cache_types=%s" % str(cache_types))
    for cache_type in cache_types:
        path = _get_cache_path(cache_type, tag=tag)
        cache_info = get_cache_size_info(path, cache_type)
        txt.append(cache_info)
    txt = "\n".join(txt)
    return txt

# #############################################################################
# Global cache interface
# #############################################################################


def _get_cache_types() -> List[str]:
    """
    Return the types (aka levels) of the cache.
    """
    return ["mem", "disk"]


def _dassert_is_valid_cache_type(cache_type: str) -> None:
    """
    Assert that `cache_type` is a valid cache type.
    """
    dbg.dassert_in(cache_type, _get_cache_types())


def _get_cache_name(cache_type: str, tag: Optional[str] = None) -> str:
    """
    Get the canonical cache name for a type of cache and tag.

    E.g., `tmp.cache.mem.tag`

    :param cache_type: type of a cache
    :param tag: optional unique tag of the cache
    :return: name of the folder for a cache
    """
    _dassert_is_valid_cache_type(cache_type)
    cache_name = f"tmp.cache.{cache_type}"
    if tag is not None:
        cache_name += f".{tag}"
    return cache_name


def _get_cache_path(cache_type: str, tag: Optional[str] = None) -> str:
    """
    Get path to the directory storing the cache.

    For a memory cache, the path is in a predefined RAM disk.
    For a disk cache, the path is on the file system relative to Git root.

    :return: the file system path to the cache
    """
    _dassert_is_valid_cache_type(cache_type)
    # Get the cache name.
    cache_name = _get_cache_name(cache_type, tag)
    # Get the enclosing directory path.
    if cache_type == "mem":
        tmpfs_path = "/tmp" if hsyste.get_os_name() == "Darwin" else "/mnt/tmpfs"
        root_path = tmpfs_path
    elif cache_type == "disk":
        root_path = git.get_client_root(super_module=True)
    # Compute path.
    file_name = os.path.join(root_path, cache_name)
    file_name = os.path.abspath(file_name)
    return file_name


# TODO(gp): -> ?
def get_cache_size_info(path: str, cache_type: str) -> str:
    if path is None:
        txt = "'%s' cache in '%s' doesn't exist yet" % (cache_type, path)
    else:
        size_in_bytes = hsyste.du(path)
        size_as_str = hintro.format_size(size_in_bytes)
        txt = "'%s' cache in '%s' has size=%s" % (cache_type, path, size_as_str)
    return txt


# This is the global memory cache.
_MEMORY_CACHE: Optional[joblib.Memory] = None


# This is the global disk cache.
_DISK_CACHE: Optional[joblib.Memory] = None


def _create_cache_backend(
    cache_type: str, tag: Optional[str] = None
) -> joblib.Memory:
    """
    Create a Joblib memory object storing a cache.

    :return: cache backend object
    """
    _dassert_is_valid_cache_type(cache_type)
    file_name = _get_cache_path(cache_type, tag)
    cache_backend = joblib.Memory(file_name, verbose=0, compress=1)
    return cache_backend


# TODO(gp): -> get_cache?
def get_global_cache(cache_type: str, tag: Optional[str] = None) -> joblib.Memory:
    """
    Get global cache by cache type.

    :return: caching backend
    """
    _dassert_is_valid_cache_type(cache_type)
    global _MEMORY_CACHE
    global _DISK_CACHE
    if tag is None:
        if cache_type == "mem":
            # Create global memory cache if it doesn't exist.
            if _MEMORY_CACHE is None:
                _MEMORY_CACHE = _create_cache_backend(cache_type)
            global_cache = _MEMORY_CACHE
        elif cache_type == "disk":
            # Create global disk cache if it doesn't exist.
            if _DISK_CACHE is None:
                _DISK_CACHE = _create_cache_backend(cache_type)
            global_cache = _DISK_CACHE
    else:
        # Build a one-off cache using tag.
        global_cache = _create_cache_backend(cache_type, tag)
    return global_cache


def set_global_cache(cache_type: str, cache_backend: joblib.Memory) -> None:
    """
    Set global cache by cache type.

    :param cache_type: type of a cache
    :param cache_backend: caching backend
    """
    _dassert_is_valid_cache_type(cache_type)
    global _MEMORY_CACHE
    global _DISK_CACHE
    if cache_type == "mem":
        _MEMORY_CACHE = cache_backend
    elif cache_type == "disk":
        _DISK_CACHE = cache_backend


def clear_global_cache(
    cache_type: str, tag: Optional[str] = None, destroy: bool = False
) -> None:
    """
    Reset the global cache by cache type.

    :param cache_type: type of a cache. `None` to clear all the caches.
    :param tag: optional unique tag of the cache, empty by default
    :param destroy: remove physical directory
    """
    if cache_type == "all":
        for cache_type_tmp in _get_cache_types():
            clear_global_cache(cache_type_tmp, tag=tag, destroy=destroy)
        return
    _dassert_is_valid_cache_type(cache_type)
    # Clear and / or destroy the cache `cache_type` with the given `tag`.
    cache_path = _get_cache_path(cache_type, tag)
    info_before = get_cache_size_info(cache_path, cache_type)
    _LOG.warning("Resetting %s cache '%s'", cache_type, cache_path)
    if destroy:
        _LOG.warning("Destroying ...")
        hio.delete_dir(cache_path)
    else:
        cache_backend = get_global_cache(cache_type, tag)
        cache_backend.clear(warn=True)
    # Report stats before and after.
    info_after = get_cache_size_info(cache_path, cache_type)
    _LOG.info("# Info: %s -> %s", info_before, info_after)


# #############################################################################


# TODO(gp): -> _Cached
class Cached:
    # pylint: disable=protected-access
    """
    Implement a cache in memory and disk for a function.

    If the function value was not cached either in memory or on disk, the function
    `f()` is executed and the value is stored in both caches for future calls.

    This class uses 2 levels of caching:
    - memory cache: useful for caching across multiple executions of a function in
      a process or in notebooks without resetting the state
    - disk cache: useful for retrieving the state among different executions of a
      process or when a notebook is reset
    """

    # TODO(gp): Either allow users to initialize `mem_cache_path` here or with
    #  `set_cache_path()` but not both code paths. It's unclear which option is
    #  better. On the one side `set_cache_path()` is more explicit, but it can't be
    #  changed. On the other side the wrapper needs to be initialized in one shot.
    def __init__(
        self,
        func: Callable,
        *,
        use_mem_cache: bool = True,
        use_disk_cache: bool = True,
        set_verbose_mode: bool = False,
        tag: Optional[str] = None,
        mem_cache_path: Optional[str] = None,
        disk_cache_path: Optional[str] = None,
    ):
        """
        Constructor.

        :param func: function to cache
        :param use_mem_cache, use_disk_cache: whether we allow memory and disk caching
        :param set_verbose_mode: print high-level information about the cache
            behavior, e.g.,
            - whether a function was cached or not
            - from which level the data was retrieved
            - the execution time
            - the amount of data retrieved
        :param tag: a tag added to the global cache path to make it specific (e.g.,
            when running unit tests we want to use a different cache)
        :param disk_cache_path: path of the function-specific cache
        """
        dbg.dassert(callable(func), "obj '%s' is not callable", str(func))
        # Make the class have the same attributes (e.g., `__name__`, `__doc__`,
        # `__dict__`) as the called function.
        functools.update_wrapper(self, func)
        # Save interface parameters.
        self._func = func
        self._use_mem_cache = use_mem_cache
        self._use_disk_cache = use_disk_cache
        # TODO(gp): -> _is_verbose_mode
        self._set_verbose_mode = set_verbose_mode
        self._tag = tag
        self._mem_cache_path = mem_cache_path
        self._disk_cache_path = disk_cache_path
        #
        self._reset_cache_tracing()
        # Create the memory and disk cache objects.
        # TODO(gp): We might simplify the code by using a dict instead of 2 variables.
        self._memory_cache = None
        self._memory_cached_func = None
        self._create_cache("mem")
        #
        self._disk_cache = None
        self._disk_cached_func = None
        self._create_cache("disk")
        # Store whether a function-specific cache is enabled. This variable is meaningful
        # only if there is a function-specific cache (see `has_function_specific_cache()`).
        # TODO(gp): -> is_function_specific_cache_enabled
        self._is_cache_enabled = True

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute the wrapped function using the caches, if needed.

        :return: object returned by the wrapped function
        """
        perf_counter_start: float
        if self._set_verbose_mode:
            perf_counter_start = time.perf_counter()
        # Execute the cached function.
        if not is_caching_enabled():
            # No caching is allowed: execute the function.
            _LOG.warning("All caching is disabled")
            self._last_used_disk_cache = self._last_used_mem_cache = False
            obj = self._func(*args, **kwargs)
        else:
            # Caching is allowed.
            self._reset_cache_tracing()
            obj = self._execute_func(*args, **kwargs)
            _LOG.debug(
                "%s: executed from '%s'",
                self._func.__name__,
                self.get_last_cache_accessed(),
            )
            # TODO(gp): Not sure making a deep copy is a good idea. In the end,
            #  the client should not modify a cached value.
            obj = copy.deepcopy(obj)
        # Print caching info.
        if self._set_verbose_mode:
            # Get time.
            elapsed_time = time.perf_counter() - perf_counter_start
            # Get memory.
            obj_size = hintro.get_size_in_bytes(obj)
            obj_size_as_str = hintro.format_size(obj_size)
            _LOG.info(
                "  --> Cache data for '%s' was retrieved from '%s' cache "
                "(size=%s time=%.2f s)",
                self._func.__name__,
                self.get_last_cache_accessed(),
                obj_size_as_str,
                elapsed_time,
            )
        return obj

    # TODO(gp): -> get_caching_info()
    def get_info(self) -> str:
        """
        Return info about the caching properties for this function.
        """
        txt = []
        txt.append("is global cache enabled=%s" % is_caching_enabled())
        #
        has_func_cache = self.has_function_specific_cache()
        txt.append("has function-specific cache=%s" % has_func_cache)
        if has_func_cache:
            # Function-specific cache: print the paths of the local cache.
            for cache_type in _get_cache_types():
                txt.append(
                    "local %s cache path=%s"
                    % (cache_type, self._get_cache_path(cache_type)),
                )
        else:
            # Global cache.
            for cache_type in _get_cache_types():
                txt.append(
                    "global %s cache path=%s"
                    % (cache_type, _get_cache_path(cache_type))
                )
        # TODO(gp): Finish this.
        txt = "\n".join(txt)
        return txt

    def get_last_cache_accessed(self) -> str:
        """
        Get the cache used in the latest call of the wrapped function.

        :return: type of cache used in the last call
        """
        if self._last_used_mem_cache:
            # If the memory cache was used, then the disk cache should not been used.
            # dbg.dassert(not self._last_used_disk_cache)
            ret = "mem"
        elif self._last_used_disk_cache:
            # dbg.dassert(not self._last_used_mem_cache)
            ret = "disk"
        else:
            ret = "no_cache"
        return ret

    # ///////////////////////////////////////////////////////////////////////////
    # Function-specific cache.
    # ///////////////////////////////////////////////////////////////////////////

    # TODO(gp): In the end, only disk cache makes sense for function-specific cache.
    #  The memory one is always in memory.

    def has_function_specific_cache(self) -> bool:
        """
        Return whether this function has a function-specific cache or uses the
        global cache.
        """
        has_func_cache = any(
            self._get_cache_path(cache_type) is not None
            for cache_type in _get_cache_types()
        )
        return has_func_cache

    def clear_cache(
        self, cache_type: str, destroy: bool = False
    ) -> None:
        """
        Clear a function-specific cache by type.

        :param cache_type: type of a cache to clear, or `None` to clear all caches
        """
        dbg.dassert(
            self.has_function_specific_cache(),
            "This function has no function-specific cache",
        )
        if cache_type == "all":
            for cache_type_tmp in _get_cache_types():
                self.clear_cache(cache_type_tmp, destroy=destroy)
            return
        #
        cache_path = self._get_cache_path(cache_type)
        dbg.dassert_is_not(cache_path, None)
        cache_path = cast(str, cache_path)
        # Collect info before.
        info_before = get_cache_size_info(cache_path, cache_type)
        # Clear / destroy the cache.
        _LOG.warning(
            "Resetting '%s' cache for function '%s' in dir '%s'",
            cache_type,
            self._func.__name__,
            cache_path,
        )
        if destroy:
            _LOG.warning("Destroying cache...")
            hio.delete_dir(cache_path)
        else:
            cache_backend = self._get_cache(cache_type)
            cache_backend.clear()
        # Print stats.
        info_after = get_cache_size_info(cache_path, cache_type)
        _LOG.info("# Info: %s -> %s", info_before, info_after)

    def set_cache_path(self, cache_type: str, cache_path: Optional[str]) -> None:
        """
        Set the path for the function-specific cache for a cache type.

        :param cache_type: type of a cache
        :param cache_path: cache directory or None for global cache
            - If `None` is passed then use global cache.
        """
        _dassert_is_valid_cache_type(cache_type)
        if cache_type == "mem":
            self._mem_cache_path = cache_path
        elif cache_type == "disk":
            self._disk_cache_path = cache_path
        else:
            raise ValueError("Invalid cache_type='%s'" % cache_type)
        self._create_cache(cache_type)

    def _get_cache_path(self, cache_type: str) -> Optional[str]:
        """
        Get the cache directory for a cache type, `None` if global cache is
        used.

        :param cache_type: type of a cache
        :return: directory for specific cache or None if global cache is used
        """
        _LOG.debug("cache_type=%s", cache_type)
        _dassert_is_valid_cache_type(cache_type)
        if cache_type == "mem":
            ret = self._mem_cache_path
        elif cache_type == "disk":
            ret = self._disk_cache_path
        else:
            raise ValueError("Invalid cache_type='%s'" % cache_type)
        _LOG.debug("ret=%s", ret)
        return ret

    # ///////////////////////////////////////////////////////////////////////////

    def _create_cache(self, cache_type: str) -> None:
        """
        Initialize Joblib object storing a cache.

        :param cache_type: type of a cache
        """
        _LOG.debug("Create cache for cache_type='%s'", cache_type)
        _dassert_is_valid_cache_type(cache_type)
        # TODO(gp): Use a dict self._cache[cache_type] instead of duplicating all
        #  the vars.
        if cache_type == "mem":
            if self._mem_cache_path:
                # Create a function-specific cache.
                # TODO(gp): -> _mem_cache
                self._memory_cache = joblib.Memory(
                    self._mem_cache_path, verbose=0, compress=1
                )
            else:
                # Use the global cache.
                self._memory_cache = get_global_cache(cache_type, self._tag)
            # TODO(gp): -> _mem_cached_func
            self._memory_cached_func = self._memory_cache.cache(self._func)
        elif cache_type == "disk":
            if self._disk_cache_path:
                # Create a function-specific cache.
                memory_kwargs = {
                    "verbose":0, "compress": True,
                }
                if self._disk_cache_path.startswith("s3://"):
                    import helpers.s3 as hs3
                    aws_profile = hs3.get_aws_profile()
                    s3fs = get_s3fs(aws_profile)
                    bucket = hs3.extract_bucket_from_path(self._disk_cache_path)
                    memory_kwargs.update({
                        "backend": "s3",
                        "backend_options": {"s3fs": s3fs,
                                            "bucket": bucket}})
                self._disk_cache = joblib.Memory(
                    self._disk_cache_path, **memory_kwargs)
            else:
                # Use the global cache.
                self._disk_cache = get_global_cache(cache_type, self._tag)
            self._disk_cached_func = self._disk_cache.cache(self._func)
        else:
            raise ValueError("Invalid cache_type='%s'" % cache_type)

    def _get_identifiers(
        self, cache_type: str, *args: Any, **kwargs: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Get digests for current function and arguments to be used in cache.

        :param cache_type: type of a cache
        :param args: original arguments of the call
        :param kwargs: original kw-arguments of the call
        :return: digests of the function and current arguments
        """
        cache_backend = self._get_cache(cache_type)
        func_id, args_id = cache_backend._get_output_identifiers(*args, **kwargs)
        return func_id, args_id

    def _get_cache(self, cache_type: str) -> joblib.MemorizedResult:
        """
        Get the instance of a cache by type.

        :param cache_type: type of a cache
        :return: instance of the cache from joblib
        """
        _dassert_is_valid_cache_type(cache_type)
        if cache_type == "mem":
            cache_backend = self._memory_cached_func
        elif cache_type == "disk":
            cache_backend = self._disk_cached_func
        return cache_backend

    def _has_cached_version(
        self, cache_type: str, func_id: str, args_id: str
    ) -> bool:
        """
        Check if a cache contains an entry for a corresponding function and
        arguments digests, and that function source has not changed.

        :param cache_type: type of a cache
        :param func_id: digest of the function obtained from _get_identifiers
        :param args_id: digest of arguments obtained from _get_identifiers
        :return: whether there is an entry in a cache
        """
        cache_backend = self._get_cache(cache_type)
        has_cached_version = cache_backend.store_backend.contains_item(
            [func_id, args_id]
        )
        if has_cached_version:
            # We must check that the source of the function is the same.
            # Otherwise, cache tracing will not be correct.
            # First, try faster check via joblib hash.
            if self._func in jmemor._FUNCTION_HASHES:
                func_hash = cache_backend._hash_func()
                if func_hash == jmemor._FUNCTION_HASHES[self._func]:
                    return True
            # Otherwise, check the the source of the function is still the same.
            func_code, _, _ = jmemor.get_func_code(self._func)
            old_func_code_cache = (
                cache_backend.store_backend.get_cached_func_code([func_id])
            )
            old_func_code, _ = jmemor.extract_first_line(old_func_code_cache)
            if func_code == old_func_code:
                return True
        return False

    def _store_cached_version(
        self, cache_type: str, func_id: str, args_id: str, obj: Any
    ) -> None:
        """
        Store returned value from the intrinsic function in the cache.

        :param cache_type: type of a cache
        :param func_id: digest of the function obtained from _get_identifiers
        :param args_id: digest of arguments obtained from _get_identifiers
        :param obj: return value of the intrinsic function
        """
        cache_backend = self._get_cache(cache_type)
        # Write out function code to the cache.
        func_code, _, first_line = jfunci.get_func_code(cache_backend.func)
        cache_backend._write_func_code(func_code, first_line)
        # Store the returned value into the cache.
        cache_backend.store_backend.dump_item([func_id, args_id], obj)

    # ///////////////////////////////////////////////////////////////////////////

    def _reset_cache_tracing(self) -> None:
        """
        Reset the values used to track which cache we are hitting when
        executing the cached function.
        """
        # The reset values depend on which caches are enabled.
        self._last_used_disk_cache = self._use_disk_cache
        self._last_used_mem_cache = self._use_mem_cache

    def _execute_func_from_disk_cache(self, *args: Any, **kwargs: Any) -> Any:
        func_id, args_id = self._get_identifiers("disk", *args, **kwargs)
        if not self._has_cached_version("disk", func_id, args_id):
            # If we get here, we didn't hit neither memory nor the disk cache.
            self._last_used_disk_cache = False
            _LOG.debug(
                "%s(args=%s kwargs=%s): execute the intrinsic function",
                self._func.__name__,
                args,
                kwargs,
            )
        obj = self._disk_cached_func(*args, **kwargs)
        return obj

    def _execute_func_from_mem_cache(self, *args: Any, **kwargs: Any) -> Any:
        func_id, args_id = self._get_identifiers("mem", *args, **kwargs)
        _LOG.debug(
            "%s: use_mem_cache=%s use_disk_cache=%s",
            self._func.__name__,
            self._use_mem_cache,
            self._use_disk_cache,
        )
        if self._has_cached_version("mem", func_id, args_id):
            obj = self._memory_cached_func(*args, **kwargs)
        else:
            # If we get here, we know that we didn't hit the memory cache,
            # but we don't know about the disk cache.
            self._last_used_mem_cache = False
            #
            if self._use_disk_cache:
                _LOG.debug(
                    "%s(args=%s kwargs=%s): trying to read from disk",
                    self._func.__name__,
                    args,
                    kwargs,
                )
                obj = self._execute_func_from_disk_cache(*args, **kwargs)
            else:
                _LOG.warning("Skipping disk cache")
                obj = self._memory_cached_func(*args, **kwargs)
            self._store_cached_version("mem", func_id, args_id, obj)
        return obj

    def _execute_func(self, *args: Any, **kwargs: Any) -> Any:
        _LOG.debug(
            "%s: use_mem_cache=%s use_disk_cache=%s",
            self._func.__name__,
            self._use_mem_cache,
            self._use_disk_cache,
        )
        if self._use_mem_cache:
            _LOG.debug(
                "%s(args=%s kwargs=%s): trying to read from memory",
                self._func.__name__,
                args,
                kwargs,
            )
            obj = self._execute_func_from_mem_cache(*args, **kwargs)
        else:
            _LOG.warning("Skipping memory cache")
            if self._use_disk_cache:
                obj = self._execute_func_from_disk_cache(*args, **kwargs)
            else:
                _LOG.warning("Skipping disk cache")
                obj = self._func(*args, **kwargs)
        return obj


# #############################################################################
# Decorator
# #############################################################################


def cache(
    use_mem_cache: bool = True,
    use_disk_cache: bool = True,
    set_verbose_mode: bool = False,
    tag: Optional[str] = None,
    mem_cache_path: Optional[str] = None,
    disk_cache_path: Optional[str] = None,
) -> Union[Callable, Cached]:
    """
    Decorate a function with a cache.

    The parameters are the same as `hcache.Cached`.

    Usage examples:
    ```
    import helpers.cache as hcache

    @hcache.cache()
    def add(x: int, y: int) -> int:
        return x + y

    @hcache.cache(use_mem_cache=False)
    def add(x: int, y: int) -> int:
        return x + y
    ```
    """

    def wrapper(func: Callable) -> Cached:
        return Cached(
            func,
            use_mem_cache=use_mem_cache,
            use_disk_cache=use_disk_cache,
            set_verbose_mode=set_verbose_mode,
            mem_cache_path=mem_cache_path,
            disk_cache_path=disk_cache_path,
            tag=tag,
        )

    return wrapper
