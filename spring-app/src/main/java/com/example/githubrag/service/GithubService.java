package com.example.githubrag.service;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import org.kohsuke.github.GHContent;
import org.kohsuke.github.GHRepository;
import org.kohsuke.github.GitHub;
import org.kohsuke.github.GitHubBuilder;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class GithubService {

    private final GitHub github;

    public GithubService(@Value("${github.token:}") String token) throws IOException {
        if (token != null && !token.isBlank()) {
            this.github = new GitHubBuilder().withOAuthToken(token).build();
        } else {
            this.github = GitHubBuilder.fromEnvironment().build();
        }
    }

    public List<RepositoryFile> fetchRepository(String owner, String repo) throws IOException {
        GHRepository repository = github.getRepository(owner + "/" + repo);
        List<RepositoryFile> files = new ArrayList<>();
        for (GHContent content : repository.getDirectoryContent("/")) {
            traverse(content, files);
        }
        return files;
    }

    private void traverse(GHContent content, List<RepositoryFile> files) throws IOException {
        if (content.isFile()) {
            files.add(new RepositoryFile(content.getPath(), content.getContent()));
        } else if (content.isDirectory()) {
            for (GHContent c : content.listDirectoryContent()) {
                traverse(c, files);
            }
        }
    }

    public record RepositoryFile(String path, String content) {
    }
}
