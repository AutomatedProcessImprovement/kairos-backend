# Kairos Interface Web Server

![build](https://github.com/VisualPM/backend-flask/actions/workflows/python-app.yml/badge.svg) 
![production_build](https://github.com/VisualPM/backend-flask/actions/workflows/docker-image.yml/badge.svg)

## Start the web server locally (via locally installed Python)
> Please, note that you need to have `Python` and `MongoDB` installed in order to follow the following steps. The installation instructions can be found here: https://wiki.python.org/moin/BeginnersGuide/Download and https://www.mongodb.com/docs/manual/installation/ respectively.

0) *Pre-requisite step*: MongoDB is running.
1) Create a new virtual environment
    ```
    python3 -m venv env
    ```

2) Activate it
    ```
    source env/bin/activate
    ```

3) Install all required modules listed in [requirements.txt](https://github.com/VisualPM/backend-flask/blob/main/requirements.txt)
    ```
    pip3 install -r requirements.txt
    ```

4) The web server is now running and available here: http://localhost:5000.


## Start the web server locally (via Docker)
> Please, note that you need to have `Docker` installed in order to follow the following steps. The installation instructions can be found here: https://docs.docker.com/get-docker/

0) *Pre-requisite step*: Docker is running. MongoDB is running.
1) Build the image from the current code version in the repository. 
    ```
    docker build-f Dockerfile -t kairos-api .
    ```
2) Start the container
    ```
    docker run --rm -p 5000:5000 kairos-api
    ```
3) The web server is now running and available here: http://localhost:5000.
