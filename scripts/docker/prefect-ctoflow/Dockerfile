FROM geobeyond/geoprefect:2.20.20-amd64-ctoflow-dind-08072025

RUN poetry run prefect config set PREFECT_API_URL=http://prefect:4200/api
CMD ["poetry", "run", "prefect", "shell", "serve", "poetry run python flows/smidt_wf.py", "--flow-name", "Catasto-Open Workflow Shell", "--deployment-name", "Catasto-Open Workflow shell deployment"]