# monologue [WIP]

A project to illustrate integrating logging framework with ingestion into  Retrieval Augmented Generation (RAG) system. Python is used for agents. Python and Rust both used for the ingestion back-end.

See the medium article:

---

## Concepts

Data is extracted from logs and sent to blob storage in different formats such as parquet columnar data and vector data. For now the important points is we use a low tech blob storage solution with databases such as DuckDB and LanceDB to store data on s3 backend. We need then to organize our tables. These tables will be the memory of our agents. So how we organize and move data around is important. This brings us to spaces

### Spaces

Spaces can be thought of almost as you would think of indexes. If data are stored on s3, then spaces either simply wrap those data or provide views or replications of those data. The game here is how we add or remove from what an agent recalls. You can think of a space as an index just as we added indexes on relational databases as a way to provide faster access to data. You can also think of spaces as a way to manage different contexts. As we ingest data in a fairly simple way from the logging modules, spaces are how we get creative with how data are organized to support RAG.

### Agents

Agents are chat agents in the RAG system. We use the LLM in conjunction with these data stores. One of the main things `monologue` aims to do is experiment with how an ecosystem of such agents evolves as log data are parsed and relayed.

### Logging

The main idea we explore is logging as a learning system interface. It becomes easy for all pods running on a K8s cluster to send data into the memory of the agent ecosystem and we are here experimenting with what that even means with an emphasis on simplicity. We can play with log levels and logging structure as we send structured and unstructured data to our RAG system.

---

## Install

Set environment vars; OPEN_AI, AWS, MONO_BUCKET, LOKI_ADDR

Use poetry commands in the project folder

```bash
poetry build
poetry install
poetry run monologue [args]
```

For **Docker** you can build the docker file from the root and test that you can run with the test script. This is just a deps check.

```bash
docker build --platform linux/amd64 -t monologue:latest . 
docker run  --platform linux/amd64  -t monologue
```

## Deploy

Deploy the pods to your cluster to test the logger. You need Loki on your cluster.
The files for this are in the K8s folder

```bash
kubectl apply -f  k8s/ ...
```

## Usage

To test locally we can use a logging mode that sends data to an agent that will illustrate the ingestion. In practice that agent will be running on the Kubernetes cluster consuming logs from Loki. Lets take a look at some examples of how this might work...

If you have sample data

```bash
poetry run monologue generate book_reviews &> out.log
```

Using the output file use the (slow) single line parser to test

```bash
cli ingest -f out.log
```

If you ave run the pod on kubernetes to generate sample logs

```bash
cli ingest --loki
```
