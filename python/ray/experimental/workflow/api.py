import logging
import re
import types
from typing import Union, Optional, TYPE_CHECKING

import ray

from ray.experimental.workflow import execution
from ray.experimental.workflow.step_function import WorkflowStepFunction

if TYPE_CHECKING:
    from ray.experimental.workflow.storage import Storage
    from ray.experimental.workflow.common import Workflow

logger = logging.getLogger(__name__)


def _is_anonymous_namespace():
    namespace = ray.get_runtime_context().namespace
    regex = re.compile(
        r"^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?"
        r"[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z", re.I)
    match = regex.match(namespace)
    return bool(match)


def step(func: types.FunctionType) -> WorkflowStepFunction:
    """A decorator used for creating workflow steps.

    Examples:
        >>> @workflow.step
        ... def book_flight(origin: str, dest: str) -> Flight:
        ...    return Flight(...)

    Args:
        func: The function to turn into a workflow step.
    """
    if not isinstance(func, types.FunctionType):
        raise TypeError(
            "The @workflow.step decorator can only wrap a function.")
    return WorkflowStepFunction(func)


def run(entry_workflow: "Workflow",
        storage: "Optional[Union[str, Storage]]" = None,
        workflow_id: Optional[str] = None) -> ray.ObjectRef:
    """Run a workflow asynchronously.

    Examples:
        >>> @workflow.step
        ... def book_flight(origin: str, dest: str) -> Flight:
        ...    return Flight(...)

        >>> @workflow.step
        ... def book_hotel(location: str) -> Reservation:
        ...    return Reservation(...)

        >>> @workflow.step
        ... def finalize_trip(bookings: List[Any]) -> Trip:
        ...    return Trip(...)

        >>> flight1 = book_flight.step("OAK", "SAN")
        >>> flight2 = book_flight.step("SAN", "OAK")
        >>> hotel = book_hotel.step("SAN")
        >>> trip = finalize_trip.step([flight1, flight2, hotel])
        >>> ray.get(workflow.run(trip))

    Args:
        entry_workflow: The output step of the workflow to run. The return
            type of the workflow will be ObjectRef[T] if the output step is
            a workflow step returning type T.
        storage: The external storage URL or a custom storage class. If not
            specified, ``$(pwd)/workflow_data`` will be used.
        workflow_id: A unique identifier that can be used to resume the
            workflow. If not specified, a random id will be generated.

    Returns:
        An object reference that can be used to retrieve the workflow result.
    """
    assert ray.is_initialized()
    if _is_anonymous_namespace():
        raise ValueError("Must use a namespace in 'ray.init()' to access "
                         "workflows properly. Current namespace seems to "
                         "be anonymous.")
    return execution.run(entry_workflow, storage, workflow_id)


def resume(workflow_id: str,
           storage: "Optional[Union[str, Storage]]" = None) -> ray.ObjectRef:
    """Resume a workflow.

    Resume a workflow and retrieve its output. If the workflow was incomplete,
    it will be re-executed from its checkpointed outputs. If the workflow was
    complete, returns the result immediately.

    Examples:
        >>> res1 = workflow.run(trip, workflow_id="trip1")
        >>> res2 = workflow.resume("trip1")
        >>> assert ray.get(res1) == ray.get(res2)

    Args:
        workflow_id: The id of the workflow to resume.
        storage: The external storage URL or a custom storage class. If not
            specified, ``$(pwd)/workflow_data`` will be used.

    Returns:
        An object reference that can be used to retrieve the workflow result.
    """
    assert ray.is_initialized()
    if _is_anonymous_namespace():
        raise ValueError("Must use a namespace in 'ray.init()' to access "
                         "workflows properly. Current namespace seems to "
                         "be anonymous.")
    return execution.resume(workflow_id, storage)


def get_output(workflow_id: str) -> ray.ObjectRef:
    """Get the output of a running workflow.

    Args:
        workflow_id: The ID of the running workflow job.

    Examples:
        >>> res1 = workflow.run(trip, workflow_id="trip1")
        >>> # you could "get_output()" in another machine
        >>> res2 = workflow.get_output("trip1")
        >>> assert ray.get(res1) == ray.get(res2)

    Returns:
        An object reference that can be used to retrieve the workflow result.
    """
    assert ray.is_initialized()
    if _is_anonymous_namespace():
        raise ValueError("Must use a namespace in 'ray.init()' to access "
                         "workflows properly. Current namespace seems to "
                         "be anonymous.")
    return execution.get_output(workflow_id)


__all__ = ("step", "run", "get_output")
