package com.example.githubrag.dto;

import java.util.List;

import com.example.githubrag.model.RepositoryDocument;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class SearchResult {
    private String answer;
    private List<RepositoryDocument> documents;
}
