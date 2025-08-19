package com.example.githubrag.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import com.example.githubrag.model.RepositoryDocument;

public interface RepositoryDocumentRepository extends JpaRepository<RepositoryDocument, Long> {
    List<RepositoryDocument> findTop5ByOrderByIdAsc();
}
