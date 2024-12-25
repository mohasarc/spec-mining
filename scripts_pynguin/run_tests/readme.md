### run

```bash
bash ./run_tests.sh https://github.com/auth0/auth0-python 
```

results are will be in the current dir in `results/project_name`.

We are not using Docker here because I believe there are missing dependencies in the docker image to run some projects. If you want to run with docker:

```bash
docker build -t denini/run_tests .
```

```bash
docker run --rm -v "$(pwd):/app" denini/run_tests https://github.com/auth0/auth0-python
```

to run in docker needs to change the `REPORT_DIR` in the .sh