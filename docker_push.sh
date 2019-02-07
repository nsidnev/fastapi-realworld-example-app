#!/usr/bin/env bash

#!/bin/bash
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
docker push nikelwolf/fastapi-realworld