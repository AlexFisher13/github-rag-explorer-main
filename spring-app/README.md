# Spring Boot GitHub RAG Explorer

This module provides a Spring Boot implementation of the GitHub RAG Explorer.
It demonstrates how to ingest GitHub repository content, store simple metadata
and interact with a Large Language Model through Spring AI.

## Features

* Fetch repository contents using the `org.kohsuke:github-api` library.
* Generate embeddings with Spring AI's `EmbeddingClient` and persist them with
  Spring Data JPA.
* Query documents and generate answers with Spring AI's `ChatClient`.
* Simple Thymeleaf web UI for submitting questions and displaying results.

## Requirements

* Java 21
* Maven 3.9+
* PostgreSQL database
* API keys for OpenAI and GitHub (via environment variables `OPENAI_API_KEY`
  and `GITHUB_TOKEN`).

## Running

```
cd spring-app
mvn spring-boot:run
```

The application will start on [http://localhost:8080](http://localhost:8080).

## Testing

```
cd spring-app
mvn test
```

The tests use mocked AI clients and an in-memory database.
