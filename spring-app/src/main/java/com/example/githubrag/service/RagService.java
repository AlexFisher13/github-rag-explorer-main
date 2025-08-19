package com.example.githubrag.service;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.springframework.ai.chat.ChatClient;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.ai.chat.prompt.PromptTemplate;
import org.springframework.stereotype.Service;

import com.example.githubrag.model.RepositoryDocument;
import com.example.githubrag.repository.RepositoryDocumentRepository;

@Service
public class RagService {

    private final RepositoryDocumentRepository repository;
    private final ChatClient chatClient;

    public RagService(RepositoryDocumentRepository repository, ChatClient chatClient) {
        this.repository = repository;
        this.chatClient = chatClient;
    }

    public String chat(String question) {
        List<RepositoryDocument> docs = repository.findTop5ByOrderByIdAsc();
        String context = docs.stream().map(RepositoryDocument::getContent)
                .collect(Collectors.joining("\n---\n"));
        PromptTemplate template = new PromptTemplate("""
                Answer the user's question using the following repository context.

                {context}

                Question: {question}
                """);
        Prompt prompt = template.create(Map.of("context", context, "question", question));
        return chatClient.call(prompt).getResult().getOutput().getContent();
    }
}
