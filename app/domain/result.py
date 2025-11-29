"""
Result type for explicit error handling
Provides a type-safe way to return either success or error values
"""

from typing import TypeVar, Generic, Union, Callable, Optional
from dataclasses import dataclass


T = TypeVar('T')  # Success type
E = TypeVar('E')  # Error type


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value

    def unwrap_or(self, default: T) -> T:
        return self.value

    def unwrap_err(self) -> None:
        raise ValueError("Called unwrap_err on Ok value")

    def map(self, fn: Callable[[T], 'U']) -> 'Ok[U]':
        return Ok(fn(self.value))

    def map_err(self, fn: Callable[[E], 'F']) -> 'Ok[T]':
        return self


@dataclass(frozen=True)
class Err(Generic[E]):
    error: E

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> None:
        raise ValueError(f"Called unwrap on Err value: {self.error}")

    def unwrap_or(self, default: T) -> T:
        return default

    def unwrap_err(self) -> E:
        return self.error

    def map(self, fn: Callable[[T], 'U']) -> 'Err[E]':
        return self

    def map_err(self, fn: Callable[[E], 'F']) -> 'Err[F]':
        return Err(fn(self.error))


# Union type for convenience
Result = Union[Ok[T], Err[E]]


# Helper functions for pattern matching
def match_result(result: Result[T, E],
                 ok_fn: Callable[[T], 'R'],
                 err_fn: Callable[[E], 'R']) -> 'R':
    if isinstance(result, Ok):
        return ok_fn(result.value)
    else:
        return err_fn(result.error)
