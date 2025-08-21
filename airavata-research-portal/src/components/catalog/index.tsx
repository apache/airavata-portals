/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements. See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership. The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License. You may obtain a copy of the License at
 *
 *  http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing,
 *  software distributed under the License is distributed on an
 *  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 *  KIND, either express or implied. See the License for the
 *  specific language governing permissions and limitations
 *  under the License.
 */

import {
  Box,
  Container,
  Text,
  VStack,
  HStack,
  Button,
  SimpleGrid,
  Flex,
  Input,
} from "@chakra-ui/react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { v1ApiService } from "../../lib/v1Api";
import { ItemCard } from "../common/ItemCard";

interface Resource {
  id: string;
  name: string;
  description: string;
  tags: Array<{name?: string; value?: string} | string>;
  authors: string[];
  headerImage: string;
  createdAt: string;
  updatedAt: string;
}

interface CatalogState {
  models: Resource[];
  repositories: Resource[];
  notebooks: Resource[];
  loading: boolean;
  error: string | null;
}

export const Catalog = () => {
  const navigate = useNavigate();
  const [state, setState] = useState<CatalogState>({
    models: [],
    repositories: [],
    notebooks: [],
    loading: true,
    error: null
  });
  const [searchTerm, setSearchTerm] = useState("");
  const [activeResourceType, setActiveResourceType] = useState<string>("all");

  useEffect(() => {
    fetchAllResources();
  }, []);

  const fetchAllResources = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      // Fetch all resource types from v1 API in parallel
      const [modelsResponse, repositoriesResponse, notebooksResponse] = await Promise.all([
        v1ApiService.getModels().catch(() => ({ content: [] })),
        v1ApiService.getRepositories().catch(() => ({ content: [] })),
        v1ApiService.getNotebooks().catch(() => ({ content: [] }))
      ]);

      setState(prev => ({
        ...prev,
        models: modelsResponse.content || modelsResponse || [],
        repositories: repositoriesResponse.content || repositoriesResponse || [],
        notebooks: notebooksResponse.content || notebooksResponse || [],
        loading: false
      }));
    } catch (err) {
      console.error("Failed to fetch catalog resources:", err);
      setState(prev => ({
        ...prev,
        error: "Failed to load catalog resources. Make sure the research service API is running on port 8080.",
        loading: false
      }));
    }
  };

  const handleStar = async (id: string) => {
    try {
      await v1ApiService.starDataset(id);
      console.log("Resource starred:", id);
      fetchAllResources();
    } catch (err) {
      console.error("Failed to star resource:", err);
    }
  };

  const getAllResources = () => [
    ...state.models.map(r => ({ ...r, type: 'MODEL' })),
    ...state.repositories.map(r => ({ ...r, type: 'REPOSITORY' })),
    ...state.notebooks.map(r => ({ ...r, type: 'NOTEBOOK' }))
  ];

  const getFilteredResources = () => {
    let resources = getAllResources();

    // Filter by resource type
    if (activeResourceType !== "all") {
      resources = resources.filter(r => r.type.toLowerCase() === activeResourceType);
    }

    // Filter by search term
    if (searchTerm.trim()) {
      resources = resources.filter(resource => 
        resource.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        resource.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    return resources;
  };

  const filteredResources = getFilteredResources();

  return (
    <Box bg="gray.50" minH="100vh">
      <Container maxW="1200px" py={8}>
        <VStack spacing={6} align="stretch">
          {/* Header */}
          <Box>
            <Text fontSize="3xl" fontWeight="bold" color="gray.800" mb={2}>
              Research Catalog
            </Text>
            <Text color="gray.600" fontSize="md">
              Browse models, repositories, and notebooks from the v1 API
            </Text>
          </Box>

          {/* Search */}
          <Box>
            <Input
              placeholder="Search resources..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              bg="white"
              maxW="400px"
            />
          </Box>

          {/* Filter Buttons */}
          <HStack spacing={2}>
            <Button
              size="sm"
              variant={activeResourceType === "all" ? "solid" : "outline"}
              onClick={() => setActiveResourceType("all")}
            >
              All ({getAllResources().length})
            </Button>
            <Button
              size="sm"
              variant={activeResourceType === "model" ? "solid" : "outline"}
              onClick={() => setActiveResourceType("model")}
            >
              Models ({state.models.length})
            </Button>
            <Button
              size="sm"
              variant={activeResourceType === "repository" ? "solid" : "outline"}
              onClick={() => setActiveResourceType("repository")}
            >
              Repositories ({state.repositories.length})
            </Button>
            <Button
              size="sm"
              variant={activeResourceType === "notebook" ? "solid" : "outline"}
              onClick={() => setActiveResourceType("notebook")}
            >
              Notebooks ({state.notebooks.length})
            </Button>
          </HStack>

          {/* Loading/Error States */}
          {state.loading && (
            <Box textAlign="center" py={8}>
              <Text color="gray.500">Loading catalog resources...</Text>
            </Box>
          )}

          {state.error && (
            <Box textAlign="center" py={8}>
              <Text color="red.500" mb={4}>{state.error}</Text>
              <Button onClick={fetchAllResources} size="sm">
                Retry
              </Button>
            </Box>
          )}

          {/* Resources Grid */}
          {!state.loading && !state.error && (
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
              {filteredResources.map((resource) => (
                <Box key={`${resource.type}-${resource.id}`} position="relative">
                  <Box
                    position="absolute"
                    top={2}
                    right={2}
                    bg="white"
                    px={2}
                    py={1}
                    borderRadius="md"
                    fontSize="xs"
                    fontWeight="medium"
                    zIndex={1}
                  >
                    {resource.type}
                  </Box>
                  <ItemCard
                    id={resource.id}
                    title={resource.name}
                    description={resource.description}
                    tags={resource.tags.map(tag => tag.name || tag.value || tag)}
                    authors={resource.authors}
                    starCount={0}
                    onStar={handleStar}
                    resourceType={resource.type}
                  />
                </Box>
              ))}
            </SimpleGrid>
          )}

          {/* Empty State */}
          {!state.loading && !state.error && filteredResources.length === 0 && (
            <Box textAlign="center" py={8}>
              <Text color="gray.500">No resources found</Text>
              {searchTerm && (
                <Text color="gray.400" fontSize="sm" mt={1}>
                  Try clearing your search term
                </Text>
              )}
            </Box>
          )}
        </VStack>
      </Container>
    </Box>
  );
};