import time
from functools import wraps
from typing import Any, Callable, Type

import docker.errors
import psycopg2
from docker import APIClient


def do_with_retry(
    catching_exc: Type[Exception], reraised_exc: Type[Exception], error_msg: str
) -> Callable:  # pragma: no cover
    def outer_wrapper(call: Callable) -> Callable:
        @wraps(call)
        def inner_wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = 0.001
            for i in range(15):
                try:
                    return call(*args, **kwargs)
                except catching_exc:
                    time.sleep(delay)
                    delay *= 2
            else:  # pragma: no cover
                raise reraised_exc(error_msg)

        return inner_wrapper

    return outer_wrapper


@do_with_retry(docker.errors.APIError, RuntimeError, "cannot pull postgres image")
def pull_image(client: APIClient, image: str) -> None:  # pragma: no cover
    client.pull(image)


@do_with_retry(psycopg2.Error, RuntimeError, "cannot start postgres server")
def ping_postgres(dsn: str) -> None:  # pragma: no cover
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION hstore;")
    cur.close()
    conn.close()
