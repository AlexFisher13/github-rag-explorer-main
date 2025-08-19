package com.example.githubrag.controller;

import java.util.List;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;

import com.example.githubrag.dto.SearchRequest;
import com.example.githubrag.dto.SearchResult;
import com.example.githubrag.model.RepositoryDocument;
import com.example.githubrag.service.RagService;
import com.example.githubrag.repository.RepositoryDocumentRepository;

@Controller
public class SearchController {

    private final RagService ragService;
    private final RepositoryDocumentRepository repository;

    public SearchController(RagService ragService, RepositoryDocumentRepository repository) {
        this.ragService = ragService;
        this.repository = repository;
    }

    @GetMapping("/")
    public String index(Model model) {
        model.addAttribute("request", new SearchRequest());
        return "index";
    }

    @PostMapping("/search")
    public String search(@ModelAttribute("request") SearchRequest request, Model model) {
        String answer = ragService.chat(request.getQuery());
        List<RepositoryDocument> docs = repository.findTop5ByOrderByIdAsc();
        model.addAttribute("result", new SearchResult(answer, docs));
        return "index";
    }
}
