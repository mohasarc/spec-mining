## How to run

```bash
docker run --rm -v "$(pwd):/app" denini/pynguin $project_url
```

example:

```bash
docker run --rm -v "$(pwd):/app" denini/pynguin https://github.com/denini08/pytoy
```

```bash
docker run --rm -v "$(pwd):/app" denini/pynguin https://github.com/huzecong/flutes
```

the output file will be in the `project_name` folder and `projecet_name.zip`

in the example it will be in the `pytoy` and `pytoy`.zip
