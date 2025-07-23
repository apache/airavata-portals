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
} from "@chakra-ui/react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { adminApiService } from "../../lib/adminApi";
import { ItemCard } from "../common/ItemCard";

interface Repository {
  id: number;
  title: string;
  description: string;
  tags: string[];
  authors: string[];
  starCount: number;
  category: string;
}

const filterCategories = [
  "All",
  "Computer Vision", 
  "Cyber Security",
  "Finance",
  "Healthcare",
  "NLP",
  "Life Sciences"
];

const Repositories = () => {
  const navigate = useNavigate();
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState("All");

  useEffect(() => {
    fetchRepositories();
  }, []);

  const fetchRepositories = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminApiService.getRepositories();
      setRepositories(data);
    } catch (err) {
      console.error("Failed to fetch repositories:", err);
      setError("Failed to load repositories. Make sure the API server is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleStar = async (id: number) => {
    try {
      const updatedRepository = await adminApiService.starRepository(id);
      setRepositories(prev => 
        prev.map(repository => 
          repository.id === id ? { ...repository, starCount: updatedRepository.starCount } : repository
        )
      );
    } catch (err) {
      console.error("Failed to star repository:", err);
    }
  };

  const filteredRepositories = activeFilter === "All" 
    ? repositories 
    : repositories.filter(repository => repository.category === activeFilter.toLowerCase().replace(" ", "_"));

  return (
    <Box bg="gray.50" minH="100vh">
      <Container maxW="1400px" py={10}>
        <VStack spacing={10} align="stretch">
          {/* Header */}
          <Flex justify="space-between" align="start">
            <Box flex={1}>
              <Text fontSize="4xl" fontWeight="bold" color="gray.800" mb={4}>
                Repositories
              </Text>
              <Text color="gray.600" maxW="600px" lineHeight="1.6" fontSize="md">
                Manage version-controlled code repositories within CyberShuttle. Connect your own
                or explore available ones to support your projects and experiments.
              </Text>
            </Box>
            
            {/* Decorative icon area */}
            <Box w="200px" h="140px" position="relative">
              <Box
                position="absolute"
                top="10px"
                right="30px"
                w="80px"
                h="80px"
                bg="#e6f3ff"
                borderRadius="xl"
                display="flex"
                alignItems="center"
                justifyContent="center"
              >
                <Text fontSize="3xl">📁</Text>
              </Box>
              <Box
                position="absolute"
                top="50px"
                right="10px"
                w="50px"
                h="50px"
                bg="#f0e6ff"
                borderRadius="lg"
                display="flex"
                alignItems="center"
                justifyContent="center"
              >
                <Text fontSize="xl">🔗</Text>
              </Box>
              <Box
                position="absolute"
                top="30px"
                right="70px"
                w="35px"
                h="35px"
                bg="#e6ffe6"
                borderRadius="md"
                display="flex"
                alignItems="center"
                justifyContent="center"
              >
                <Text fontSize="lg">💼</Text>
              </Box>
            </Box>
          </Flex>

          {/* New Repository Button */}
          <Box>
            <Button
              bg="#60b4f7"
              color="white"
              size="md"
              leftIcon={<Text>+</Text>}
              _hover={{ bg: "#4a9ce6" }}
              borderRadius="md"
              onClick={() => navigate("/resources/repositories/new")}
            >
              New Repository
            </Button>
          </Box>

          {/* Filters */}
          <Box>
            <HStack spacing={3} mb={2}>
              <Text fontSize="sm" fontWeight="medium" color="gray.700" mr={2}>
                Filters :
              </Text>
              {filterCategories.map((category) => (
                <Button
                  key={category}
                  size="sm"
                  variant={activeFilter === category ? "solid" : "outline"}
                  bg={activeFilter === category ? "black" : "transparent"}
                  color={activeFilter === category ? "white" : "gray.600"}
                  borderColor="gray.300"
                  borderRadius="full"
                  px={4}
                  onClick={() => setActiveFilter(category)}
                  _hover={{
                    bg: activeFilter === category ? "gray.800" : "gray.50"
                  }}
                >
                  {category}
                </Button>
              ))}
            </HStack>
          </Box>

          {/* Loading/Error States */}
          {loading && (
            <Box textAlign="center" py={12}>
              <Text color="gray.500">Loading repositories...</Text>
            </Box>
          )}

          {error && (
            <Box textAlign="center" py={12}>
              <Text color="red.500">{error}</Text>
              <Button mt={4} onClick={fetchRepositories} size="sm">
                Retry
              </Button>
            </Box>
          )}

          {/* Repositories Grid */}
          {!loading && !error && (
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={12}>
              {filteredRepositories.map((repository) => (
                <ItemCard
                  key={repository.id}
                  id={repository.id}
                  title={repository.title}
                  description={repository.description}
                  tags={repository.tags}
                  authors={repository.authors}
                  starCount={repository.starCount}
                  onStar={handleStar}
                />
              ))}
            </SimpleGrid>
          )}

          {/* Empty State */}
          {!loading && !error && filteredRepositories.length === 0 && (
            <Box textAlign="center" py={12}>
              <Text color="gray.500" fontSize="lg">
                No repositories found for "{activeFilter}"
              </Text>
              <Text color="gray.400" fontSize="sm" mt={2}>
                Try selecting a different filter or check back later.
              </Text>
            </Box>
          )}
        </VStack>
      </Container>
    </Box>
  );
};

export default Repositories;
