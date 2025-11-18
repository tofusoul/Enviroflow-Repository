"""
Task definition and execution for DAG system.

Provides the base Task class and related types for defining pipeline operations.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union

import polars as pl
from rich.console import Console

console = Console()

# Type definitions
TaskResult = TypeVar("TaskResult")
TaskInputs = Dict[str, Any]
TaskOutputs = Dict[str, Any]


class TaskStatus(Enum):
    """Status of task execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """
    A single task in the DAG with inputs, outputs, and execution logic.

    Tasks are the fundamental building blocks of the pipeline DAG.
    Each task defines:
    - Required inputs (dependencies on other tasks' outputs)
    - Expected outputs (what this task produces)
    - Execution function that transforms inputs to outputs
    """

    # Task identification
    name: str
    description: str = ""

    # Task execution
    func: Optional[Callable[..., Any]] = field(default=None)

    # Dependencies and outputs
    inputs: Dict[str, str] = field(
        default_factory=dict
    )  # {param_name: dependency_task.output_name}
    outputs: List[str] = field(
        default_factory=list
    )  # [output_name1, output_name2, ...]

    # Execution state
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[Exception] = None

    # Task configuration
    retries: int = 0
    max_retries: int = 2

    def __post_init__(self) -> None:
        """Validate task configuration after initialization."""
        if self.func is None:
            raise ValueError(f"Task '{self.name}' must have a function")

        # Auto-detect outputs from function annotations if not provided
        if not self.outputs:
            self.outputs = self._detect_outputs_from_function()

    def _detect_outputs_from_function(self) -> List[str]:
        """
        Attempt to detect output names from function signature or return annotation.

        For now, we'll use a simple convention: if the function returns a dict,
        the keys are the output names. Otherwise, use the task name as output.
        """
        if hasattr(self.func, "__annotations__"):
            return_annotation = self.func.__annotations__.get("return")
            if return_annotation is not None:
                # For complex return types, we'll use the task name as default
                # This can be enhanced based on actual usage patterns
                pass

        # Default: task name as single output
        return [self.name]

    @property
    def dependencies(self) -> Set[str]:
        """Get set of task names this task depends on."""
        return {dep.split(".")[0] for dep in self.inputs.values()}

    def can_execute(self, completed_tasks: Set[str]) -> bool:
        """Check if this task can execute given completed tasks."""
        return self.dependencies.issubset(completed_tasks)

    def execute(
        self, task_outputs: Dict[str, Any], config: Optional[Any] = None
    ) -> TaskOutputs:
        """
        Execute the task with provided inputs from previous tasks.

        Args:
            task_outputs: Dictionary mapping task_name.output_name to values
            config: Optional configuration object to pass to task functions

        Returns:
            Dictionary of outputs produced by this task
        """
        if self.status == TaskStatus.SUCCESS:
            console.print(f"⏭️  Task '{self.name}' already completed, skipping")
            return self._format_outputs(self.result)

        console.print(f"🚀 Executing task: [bold cyan]{self.name}[/bold cyan]")

        try:
            self.status = TaskStatus.RUNNING

            # Execute the function
            if self.func is None:
                raise ValueError(f"Task '{self.name}' has no function to execute")

            # Prepare inputs for the function
            func_inputs = self._prepare_function_inputs(task_outputs, config)

            # Execute the function
            result = self.func(**func_inputs)

            # Store result and mark as successful
            self.result = result
            self.status = TaskStatus.SUCCESS

            console.print(
                f"✅ Task '[bold green]{self.name}[/bold green]' completed successfully"
            )

            return self._format_outputs(result)

        except Exception as e:
            self.error = e
            self.retries += 1

            if self.retries <= self.max_retries:
                console.print(
                    f"⚠️  Task '{self.name}' failed, retrying ({self.retries}/{self.max_retries})"
                )
                self.status = TaskStatus.PENDING
                return self.execute(task_outputs, config)  # Retry
            else:
                self.status = TaskStatus.FAILED
                console.print(f"❌ Task '[bold red]{self.name}[/bold red]' failed: {e}")
                raise e

    def _prepare_function_inputs(
        self, task_outputs: Dict[str, Any], config: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Prepare function inputs from task dependencies."""
        func_inputs = {}

        if self.func is None:
            return func_inputs

        # Get function signature to understand expected parameters
        sig = inspect.signature(self.func)

        for param_name, param in sig.parameters.items():
            if param_name == "config" and config is not None:
                # Pass config parameter if function expects it
                func_inputs[param_name] = config
            elif param_name in self.inputs:
                # This parameter comes from another task's output
                dependency_key = self.inputs[param_name]
                if dependency_key in task_outputs:
                    func_inputs[param_name] = task_outputs[dependency_key]
                else:
                    raise ValueError(
                        f"Missing dependency '{dependency_key}' for task '{self.name}'"
                    )
            # If parameter not in inputs, it might be optional or provided differently
            elif param.default is not inspect.Parameter.empty:
                # Has default value, can be omitted
                continue
            else:
                # Required parameter without dependency mapping
                # This might be a configuration parameter or error
                console.print(
                    f"⚠️  Parameter '{param_name}' for task '{self.name}' has no dependency mapping"
                )

        return func_inputs

    def _format_outputs(self, result: Any) -> TaskOutputs:
        """Format task result into named outputs."""
        formatted_outputs = {}

        if isinstance(result, dict):
            # Result is already a dictionary of named outputs
            for output_name in self.outputs:
                if output_name in result:
                    formatted_outputs[f"{self.name}.{output_name}"] = result[
                        output_name
                    ]
        else:
            # Single output, use first output name
            if self.outputs:
                formatted_outputs[f"{self.name}.{self.outputs[0]}"] = result
            else:
                formatted_outputs[f"{self.name}"] = result

        return formatted_outputs


def create_file_task(
    name: str,
    file_path: Union[str, Path],
    description: str = "",
    outputs: Optional[List[str]] = None,
) -> Task:
    """
    Create a task that reads a file and returns its contents.

    Convenience function for common file reading operations.
    """

    def read_file() -> pl.DataFrame:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if path.suffix == ".parquet":
            return pl.read_parquet(path)
        elif path.suffix == ".csv":
            return pl.read_csv(path)
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")

    return Task(
        name=name,
        description=description or f"Read {file_path}",
        func=read_file,
        outputs=outputs or [name],
    )


def create_save_task(
    name: str, file_path: Union[str, Path], input_task: str, description: str = ""
) -> Task:
    """
    Create a task that saves data to a file.

    Convenience function for common file saving operations.
    """

    def save_file(data: pl.DataFrame) -> Path:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.suffix == ".parquet":
            data.write_parquet(path)
        elif path.suffix == ".csv":
            data.write_csv(path)
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")

        console.print(f"💾 Saved {len(data)} records to {path}")
        return path

    return Task(
        name=name,
        description=description or f"Save to {file_path}",
        func=save_file,
        inputs={
            "data": f"{input_task}.{input_task}"
        },  # Assume output name matches task name
        outputs=["file_path"],
    )
