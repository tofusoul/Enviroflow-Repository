"""
DAG execution engine for Enviroflow ELT pipeline.

Provides the core DAG execution logic with dependency resolution and error handling.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from rich.console import Console

from .task import Task, TaskStatus

console = Console()


@dataclass
class DAGEngine:
    """
    Execution engine for DAG-based pipelines.

    Handles dependency resolution, topological sorting, and task execution
    with proper error handling and reporting.
    """

    tasks: Dict[str, Task] = field(default_factory=dict)
    task_outputs: Dict[str, Any] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)
    config: Optional[Any] = field(default=None)

    def add_task(self, task: Task) -> None:
        """Add a task to the DAG."""
        if task.name in self.tasks:
            raise ValueError(f"Task '{task.name}' already exists in DAG")

        self.tasks[task.name] = task
        console.print(f"📝 Added task: [cyan]{task.name}[/cyan] - {task.description}")

    def add_tasks(self, tasks: List[Task]) -> None:
        """Add multiple tasks to the DAG."""
        for task in tasks:
            self.add_task(task)

    def validate(self) -> bool:
        """
        Validate the DAG for cycles and missing dependencies.

        Returns:
            True if DAG is valid, raises exception otherwise
        """
        # Check for cycles using DFS
        if self._has_cycles():
            raise ValueError("DAG contains cycles")

        # Check for missing dependencies
        missing_deps = self._find_missing_dependencies()
        if missing_deps:
            raise ValueError(f"Missing task dependencies: {missing_deps}")

        console.print("✅ DAG validation passed")
        return True

    def _has_cycles(self) -> bool:
        """Check for cycles in the DAG using DFS."""
        WHITE, GRAY, BLACK = 0, 1, 2
        colors = {task_name: WHITE for task_name in self.tasks}

        def dfs(task_name: str) -> bool:
            if colors[task_name] == GRAY:
                return True  # Back edge found, cycle detected
            if colors[task_name] == BLACK:
                return False  # Already processed

            colors[task_name] = GRAY
            task = self.tasks[task_name]

            for dep_task_name in task.dependencies:
                if dep_task_name in colors and dfs(dep_task_name):
                    return True

            colors[task_name] = BLACK
            return False

        for task_name in self.tasks:
            if colors[task_name] == WHITE:
                if dfs(task_name):
                    return True

        return False

    def _find_missing_dependencies(self) -> Set[str]:
        """Find task dependencies that don't exist in the DAG."""
        missing = set()

        for task in self.tasks.values():
            for dep_task_name in task.dependencies:
                if dep_task_name not in self.tasks:
                    missing.add(dep_task_name)

        return missing

    def _topological_sort(self) -> List[str]:
        """
        Perform topological sort to determine execution order.

        Returns:
            List of task names in execution order
        """
        # Calculate in-degrees
        in_degree = defaultdict(int)
        for task_name in self.tasks:
            in_degree[task_name] = 0

        for task in self.tasks.values():
            for dep in task.dependencies:
                in_degree[task.name] += 1

        # Use queue for BFS-based topological sort
        queue = deque(
            [task_name for task_name, degree in in_degree.items() if degree == 0]
        )
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            # Reduce in-degree for dependent tasks
            current_task = self.tasks[current]
            for other_task in self.tasks.values():
                if current in other_task.dependencies:
                    in_degree[other_task.name] -= 1
                    if in_degree[other_task.name] == 0:
                        queue.append(other_task.name)

        if len(result) != len(self.tasks):
            raise ValueError("Cannot perform topological sort - DAG contains cycles")

        return result

    def execute(self, task_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Execute the DAG or specific tasks.

        Args:
            task_names: Optional list of specific tasks to execute.
                       If None, executes all tasks in dependency order.

        Returns:
            Dictionary of all task outputs
        """
        console.print("🚀 [bold blue]Starting DAG execution...[/bold blue]")

        # Validate DAG before execution
        self.validate()

        # Determine execution order
        if task_names is None:
            self.execution_order = self._topological_sort()
            console.print(
                f"📋 Executing all tasks in order: {' → '.join(self.execution_order)}"
            )
        else:
            # Execute only specified tasks and their dependencies
            self.execution_order = self._get_execution_order_for_tasks(task_names)
            console.print(
                f"📋 Executing selected tasks: {' → '.join(self.execution_order)}"
            )

        # Execute tasks in order
        failed_tasks = []
        successful_tasks = []

        for task_name in self.execution_order:
            task = self.tasks[task_name]

            try:
                # Check if all dependencies are satisfied
                if not task.can_execute(set(successful_tasks)):
                    unsatisfied = task.dependencies - set(successful_tasks)
                    console.print(
                        f"⏸️  Skipping '{task_name}' - unsatisfied dependencies: {unsatisfied}"
                    )
                    task.status = TaskStatus.SKIPPED
                    continue

                # Execute the task
                task_result = task.execute(self.task_outputs, config=self.config)

                # Store outputs for dependent tasks
                self.task_outputs.update(task_result)
                successful_tasks.append(task_name)

            except Exception as e:
                console.print(f"❌ Task '{task_name}' failed: {e}")
                failed_tasks.append(task_name)

                # Decide whether to continue or stop
                if self._should_stop_on_failure(task_name):
                    console.print("🛑 Stopping execution due to critical task failure")
                    break

        # Report execution summary
        self._report_execution_summary(successful_tasks, failed_tasks)

        if failed_tasks:
            raise RuntimeError(f"DAG execution failed. Failed tasks: {failed_tasks}")

        return self.task_outputs

    def _get_execution_order_for_tasks(self, target_tasks: List[str]) -> List[str]:
        """
        Get execution order for specific tasks including their dependencies.

        Args:
            target_tasks: List of task names to execute

        Returns:
            List of task names in execution order (including dependencies)
        """
        # Find all dependencies recursively
        all_required_tasks = set()

        def add_dependencies(task_name: str) -> None:
            if task_name in all_required_tasks:
                return

            all_required_tasks.add(task_name)
            task = self.tasks[task_name]

            for dep in task.dependencies:
                add_dependencies(dep)

        # Add target tasks and their dependencies
        for task_name in target_tasks:
            if task_name not in self.tasks:
                raise ValueError(f"Task '{task_name}' not found in DAG")
            add_dependencies(task_name)

        # Get topological sort for all required tasks
        full_order = self._topological_sort()

        # Filter to only include required tasks in correct order
        return [
            task_name for task_name in full_order if task_name in all_required_tasks
        ]

    def _should_stop_on_failure(self, failed_task: str) -> bool:
        """
        Determine if execution should stop when a task fails.

        For now, we'll stop on any failure. This can be made configurable
        based on task criticality in the future.
        """
        return True

    def _report_execution_summary(
        self, successful_tasks: List[str], failed_tasks: List[str]
    ) -> None:
        """Report summary of DAG execution."""
        console.print("\n📊 [bold blue]Execution Summary:[/bold blue]")
        console.print(f"  ✅ Successful tasks: {len(successful_tasks)}")
        console.print(f"  ❌ Failed tasks: {len(failed_tasks)}")

        if successful_tasks:
            console.print("  🟢 Successful:")
            for task_name in successful_tasks:
                console.print(f"    • {task_name}")

        if failed_tasks:
            console.print("  🔴 Failed:")
            for task_name in failed_tasks:
                task = self.tasks[task_name]
                console.print(f"    • {task_name}: {task.error}")

    def get_task_status(self, task_name: str) -> TaskStatus:
        """Get the status of a specific task."""
        if task_name not in self.tasks:
            raise ValueError(f"Task '{task_name}' not found")
        return self.tasks[task_name].status

    def reset(self) -> None:
        """Reset all tasks to pending status and clear outputs."""
        for task in self.tasks.values():
            task.status = TaskStatus.PENDING
            task.result = None
            task.error = None
            task.retries = 0

        self.task_outputs.clear()
        self.execution_order.clear()

        console.print("🔄 DAG reset - all tasks set to pending")

    def visualize(self) -> None:
        """Print a simple text visualization of the DAG structure."""
        console.print("\n🔍 [bold blue]DAG Structure:[/bold blue]")

        for task_name in self._topological_sort():
            task = self.tasks[task_name]
            deps = list(task.dependencies)

            if deps:
                console.print(f"  {task_name} ← {', '.join(deps)}")
            else:
                console.print(f"  {task_name} (no dependencies)")
