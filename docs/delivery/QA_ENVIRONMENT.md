# Repeatable QA — explicitly invoked, not automatic

For the v0.7.5 docs/contract candidate, Python `3.11.11` and exact package versions in `requirements-qa.txt` are specified by `Dockerfile.qa`.

With a Docker engine:
```sh
sh scripts/run_qa_docker.sh
```

The QA runner runs the full Master Kit 16-script local checks **only after the entire kit is imported**. In BOOTSTRAP_ONLY mode it runs the local bootstrap tests. Docker image download needs network on build; the test container itself uses no network. The Docker image build has not been tested here because this ChatGPT environment does not provide Docker. The image tag is pinned to a Python patch version but not to an immutable base-image digest, and dependencies are pinned by version rather than by download hashes.

For each PR log the exact source SHA, Python version, installed package versions, all test commands/results, negative and regression tests, and known NOT_RUN. Do not auto-merge without independent CI. GPT cannot receive a PR event automatically in this configuration.
