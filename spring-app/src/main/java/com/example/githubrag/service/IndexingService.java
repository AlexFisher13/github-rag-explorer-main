package com.example.githubrag.service;

import java.io.IOException;
import java.util.List;

import org.springframework.ai.embedding.EmbeddingClient;
import org.springframework.stereotype.Service;

import com.example.githubrag.model.RepositoryDocument;
import com.example.githubrag.repository.RepositoryDocumentRepository;

@Service
public class IndexingService {

    private final GithubService githubService;
    private final RepositoryDocumentRepository repository;
    private final EmbeddingClient embeddingClient;

    public IndexingService(GithubService githubService, RepositoryDocumentRepository repository,
            EmbeddingClient embeddingClient) {
        this.githubService = githubService;
        this.repository = repository;
        this.embeddingClient = embeddingClient;
    }

    public void indexRepository(String owner, String repo) throws IOException {
        List<GithubService.RepositoryFile> files = githubService.fetchRepository(owner, repo);
        for (GithubService.RepositoryFile file : files) {
            List<Double> embedding = embeddingClient.embed(file.content());
            RepositoryDocument doc = new RepositoryDocument();
            doc.setPath(file.path());
            doc.setContent(file.content());
            doc.setEmbedding(embedding.toString());
            repository.save(doc);
        }
    }
}
