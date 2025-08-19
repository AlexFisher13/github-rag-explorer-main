package com.example.githubrag;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.model;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.view;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import com.example.githubrag.controller.SearchController;
import com.example.githubrag.model.RepositoryDocument;
import com.example.githubrag.repository.RepositoryDocumentRepository;
import com.example.githubrag.service.RagService;

@WebMvcTest(SearchController.class)
class SearchControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private RagService ragService;

    @MockBean
    private RepositoryDocumentRepository repository;

    @Test
    void indexShouldReturnForm() throws Exception {
        mockMvc.perform(get("/")).andExpect(status().isOk()).andExpect(view().name("index"));
    }

    @Test
    void searchShouldReturnResult() throws Exception {
        when(ragService.chat("test")).thenReturn("answer");
        when(repository.findTop5ByOrderByIdAsc()).thenReturn(List.of());
        mockMvc.perform(post("/search").param("query", "test"))
                .andExpect(status().isOk())
                .andExpect(model().attributeExists("result"));
    }
}
