.. image:: ./.github/assets/logo.png

|

.. image:: https://github.com/nsidnev/fastapi-realworld-example-app/workflows/API%20spec/badge.svg
   :target: https://github.com/nsidnev/fastapi-realworld-example-app

.. image:: https://github.com/nsidnev/fastapi-realworld-example-app/workflows/Tests/badge.svg
   :target: https://github.com/nsidnev/fastapi-realworld-example-app

.. image:: https://github.com/nsidnev/fastapi-realworld-example-app/workflows/Styles/badge.svg
   :target: https://github.com/nsidnev/fastapi-realworld-example-app

.. image:: https://codecov.io/gh/nsidnev/fastapi-realworld-example-app/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/nsidnev/fastapi-realworld-example-app

.. image:: https://img.shields.io/github/license/Naereen/StrapDown.js.svg
   :target: https://github.com/nsidnev/fastapi-realworld-example-app/blob/master/LICENSE

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/ambv/black

.. image:: https://img.shields.io/badge/style-wemake-000000.svg
   :target: https://github.com/wemake-services/wemake-python-styleguide

----------

**NOTE**: This repository is not actively maintained because this example is quite complete and does its primary goal - passing Conduit testsuite.

More modern and relevant examples can be found in other repositories with ``fastapi`` tag on GitHub.

Quickstart
----------

First, run ``PostgreSQL``, set environment variables and create database. For example using ``docker``: ::

    export POSTGRES_DB=rwdb POSTGRES_PORT=5432 POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres
    docker run --name pgdb --rm -e POSTGRES_USER="$POSTGRES_USER" -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" -e POSTGRES_DB="$POSTGRES_DB" postgres
    export POSTGRES_HOST=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' pgdb)
    createdb --host=$POSTGRES_HOST --port=$POSTGRES_PORT --username=$POSTGRES_USER $POSTGRES_DB

Then run the following commands to bootstrap your environment with ``poetry``: ::

    git clone https://github.com/nsidnev/fastapi-realworld-example-app
    cd fastapi-realworld-example-app
    poetry install
    poetry shell

Then create ``.env`` file (or rename and modify ``.env.example``) in project root and set environment variables for application: ::

    touch .env
    echo APP_ENV=dev >> .env
    echo DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB >> .env
    echo SECRET_KEY=$(openssl rand -hex 32) >> .env

To run the web application in debug use::

    alembic upgrade head
    uvicorn app.main:app --reload

If you run into the following error in your docker container:

   sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server: No such file or directory
   Is the server running locally and accepting
   connections on Unix domain socket "/tmp/.s.PGSQL.5432"?

Ensure the DATABASE_URL variable is set correctly in the `.env` file.
It is most likely caused by POSTGRES_HOST not pointing to its localhost.

   DATABASE_URL=postgresql://postgres:postgres@0.0.0.0:5432/rwdb



Run tests
---------

Tests for this project are defined in the ``tests/`` folder.

Set up environment variable ``DATABASE_URL`` or set up ``database_url`` in ``app/core/settings/test.py``

This project uses `pytest
<https://docs.pytest.org/>`_ to define tests because it allows you to use the ``assert`` keyword with good formatting for failed assertations.


To run all the tests of a project, simply run the ``pytest`` command: ::

    $ pytest
    ================================================= test session starts ==================================================
    platform linux -- Python 3.8.3, pytest-5.4.2, py-1.8.1, pluggy-0.13.1
    rootdir: /home/some-user/user-projects/fastapi-realworld-example-app, inifile: setup.cfg, testpaths: tests
    plugins: env-0.6.2, cov-2.9.0, asyncio-0.12.0
    collected 90 items

    tests/test_api/test_errors/test_422_error.py .                                                                   [  1%]
    tests/test_api/test_errors/test_error.py .                                                                       [  2%]
    tests/test_api/test_routes/test_articles.py .................................                                    [ 38%]
    tests/test_api/test_routes/test_authentication.py ..                                                             [ 41%]
    tests/test_api/test_routes/test_comments.py ....                                                                 [ 45%]
    tests/test_api/test_routes/test_login.py ...                                                                     [ 48%]
    tests/test_api/test_routes/test_profiles.py ............                                                         [ 62%]
    tests/test_api/test_routes/test_registration.py ...                                                              [ 65%]
    tests/test_api/test_routes/test_tags.py ..                                                                       [ 67%]
    tests/test_api/test_routes/test_users.py ....................                                                    [ 90%]
    tests/test_db/test_queries/test_tables.py ...                                                                    [ 93%]
    tests/test_schemas/test_rw_model.py .                                                                            [ 94%]
    tests/test_services/test_jwt.py .....                                                                            [100%]

    ============================================ 90 passed in 70.50s (0:01:10) =============================================
    $

If you want to run a specific test, you can do this with `this
<https://docs.pytest.org/en/latest/usage.html#specifying-tests-selecting-tests>`_ pytest feature: ::

    $ pytest tests/test_api/test_routes/test_users.py::test_user_can_not_take_already_used_credentials

Deployment with Docker
----------------------

You must have ``docker`` and ``docker-compose`` tools installed to work with material in this section.
First, create ``.env`` file like in `Quickstart` section or modify ``.env.example``.
``POSTGRES_HOST`` must be specified as `db` or modified in ``docker-compose.yml`` also.
Then just run::

    docker-compose up -d db
    docker-compose up -d app

Application will be available on ``localhost`` in your browser.

Web routes
----------

All routes are available on ``/docs`` or ``/redoc`` paths with Swagger or ReDoc.


Project structure
-----------------

Files related to application are in the ``app`` or ``tests`` directories.
Application parts are:

::

    app
    ├── api              - web related stuff.
    │   ├── dependencies - dependencies for routes definition.
    │   ├── errors       - definition of error handlers.
    │   └── routes       - web routes.
    ├── core             - application configuration, startup events, logging.
    ├── db               - db related stuff.
    │   ├── migrations   - manually written alembic migrations.
    │   └── repositories - all crud stuff.
    ├── models           - pydantic models for this application.
    │   ├── domain       - main models that are used almost everywhere.
    │   └── schemas      - schemas for using in web routes.
    ├── resources        - strings that are used in web responses.
    ├── services         - logic that is not just crud related.
    └── main.py          - FastAPI application creation and configuration.
