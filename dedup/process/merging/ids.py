"""New record ids. Injected as a dependency so tests can use fixed ids."""
import uuid


def new_record_id():
    return str(uuid.uuid4())
