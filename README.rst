Quickstart
----------

First, run ``PostgreSQL``, set enviroment variables and create database. For example using ``docker``.

.. code-block:: bash

    export POSTGRES_DBNAME=rwdb
    export POSTGRES_PORT=5432
    export POSTGRES_USER=postgres
    export POSTGRES_PASSWORD=postgres
    docker run --name pgdb --rm -e POSTGRES_USER="$POSTGRES_USER" -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" postgres
    export POSTGRES_HOST=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' pgdb)
    createdb --host=$POSTGRES_HOST --port=$POSTGRES_PORT --username=$POSTGRES_USER $POSTGRES_DBNAME

Then run the following commands to bootstrap your environment with ``poetry``.

.. code-block:: bash

    git clone https://github.com/nikelwolf/fastapi-realworld-example-app
    cd fastapi-realworld-example-app
    poetry instal
    poetry shell

Then create ``.env`` file in project root and set enviroment variables for application.

.. code-block:: bash

    touch .env
    echo PROJECT_NAME="FastAPI RealWorld Application Example" >> .env
    echo DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DBNAME >> .env
    echo SECRET_KEY=$(openssl rand -hex 32) >> .env
    echo ALLOWED_HOSTS='"127.0.0.1", "localhost"' >> .env

To run the web application in degub use::

    uvicorn app.main:app --debug


TODO
----

1) Implement project
2) Remove unnecessary dependencies from FastAPI
3) Deployment with ``Dockerfile`` and ``docker-compose``
4) Add tests
