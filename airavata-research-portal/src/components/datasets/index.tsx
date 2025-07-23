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

interface Dataset {
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

export const Datasets = () => {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState("All");

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminApiService.getDatasets();
      setDatasets(data);
    } catch (err) {
      console.error("Failed to fetch datasets:", err);
      setError("Failed to load datasets. Make sure the API server is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleStar = async (id: number) => {
    try {
      const updatedDataset = await adminApiService.starDataset(id);
      setDatasets(prev => 
        prev.map(dataset => 
          dataset.id === id ? { ...dataset, starCount: updatedDataset.starCount } : dataset
        )
      );
    } catch (err) {
      console.error("Failed to star dataset:", err);
    }
  };

  const filteredDatasets = activeFilter === "All" 
    ? datasets 
    : datasets.filter(dataset => dataset.category === activeFilter.toLowerCase().replace(" ", "_"));

  return (
    <Box bg="gray.50" minH="100vh">
      <Container maxW="1400px" py={10}>
        <VStack spacing={10} align="stretch">
          {/* Header */}
          <Flex justify="space-between" align="start">
            <Box flex={1}>
              <Text fontSize="4xl" fontWeight="bold" color="gray.800" mb={4}>
                Datasets
              </Text>
              <Text color="gray.600" maxW="600px" lineHeight="1.6" fontSize="md">
                Access and manage datasets seamlessly in CyberShuttle. Use them directly 
                in notebooks or add your own for easy integration into your workflows.
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
                <Text fontSize="3xl">📊</Text>
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
                <Text fontSize="xl">💾</Text>
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
                <Text fontSize="lg">🗂️</Text>
              </Box>
            </Box>
          </Flex>

          {/* New Dataset Button */}
          <Box>
            <Button
              bg="#60b4f7"
              color="white"
              size="md"
              leftIcon={<Text>+</Text>}
              _hover={{ bg: "#4a9ce6" }}
              borderRadius="md"
              onClick={() => navigate('/resources/datasets/new')}
            >
              New Dataset
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
              <Text color="gray.500">Loading datasets...</Text>
            </Box>
          )}

          {error && (
            <Box textAlign="center" py={12}>
              <Text color="red.500">{error}</Text>
              <Button mt={4} onClick={fetchDatasets} size="sm">
                Retry
              </Button>
            </Box>
          )}

          {/* Datasets Grid */}
          {!loading && !error && (
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={12}>
              {filteredDatasets.map((dataset) => (
                <ItemCard
                  key={dataset.id}
                  id={dataset.id}
                  title={dataset.title}
                  description={dataset.description}
                  tags={dataset.tags}
                  authors={dataset.authors}
                  starCount={dataset.starCount}
                  onStar={handleStar}
                />
              ))}
            </SimpleGrid>
          )}

          {/* Empty State */}
          {!loading && !error && filteredDatasets.length === 0 && (
            <Box textAlign="center" py={12}>
              <Text color="gray.500" fontSize="lg">
                No datasets found for "{activeFilter}"
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