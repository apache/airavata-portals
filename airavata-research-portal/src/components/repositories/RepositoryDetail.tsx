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

import React, { useState, useEffect } from 'react';
import { Box, VStack, HStack, Text, Button, Badge } from '@chakra-ui/react';
import { useNavigate, useParams } from 'react-router';
import { adminApiService } from '../../lib/adminApi';

interface Repository {
  id: number;
  title: string;
  description: string;
  tags: string[];
  authors: string[];
  starCount: number;
  category: string;
}

export const RepositoryDetail = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [repository, setRepository] = useState<Repository | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      fetchRepository(parseInt(id));
    }
  }, [id]);

  const fetchRepository = async (repositoryId: number) => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminApiService.getRepositoryById(repositoryId);
      setRepository(data);
    } catch (err) {
      console.error('Failed to fetch repository:', err);
      setError('Failed to load repository');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box bg="gray.50" minH="100vh" p={8}>
        <Text>Loading repository...</Text>
      </Box>
    );
  }

  if (error || !repository) {
    return (
      <Box bg="gray.50" minH="100vh" p={8}>
        <VStack spacing={4}>
          <Text color="red.500">{error || 'Repository not found'}</Text>
          <Button
            variant="ghost"
            onClick={() => navigate('/resources/repositories')}
            color="gray.600"
            size="sm"
            leftIcon={<Text>←</Text>}
          >
            Back to Repositories
          </Button>
        </VStack>
      </Box>
    );
  }

  return (
    <Box bg="gray.50" minH="100vh" p={8}>
      <VStack spacing={6} maxW="1000px" mx="auto">
        <HStack w="full" justify="space-between" align="center">
          <Button
            variant="ghost"
            onClick={() => navigate('/resources/repositories')}
            color="gray.600"
            size="sm"
            leftIcon={<Text>←</Text>}
          >
            Back
          </Button>
          <HStack spacing={2}>
            <Button size="sm" variant="outline">
              Star {repository.starCount}
            </Button>
            <Button size="sm" variant="outline">
              Fork
            </Button>
          </HStack>
        </HStack>

        <Box bg="white" p={8} borderRadius="lg" w="full">
          <VStack spacing={6} align="start">
            {/* Header */}
            <VStack align="start" spacing={2} w="full">
              <Text fontSize="3xl" fontWeight="bold">
                {repository.title}
              </Text>
              <Text color="gray.600" fontSize="lg">
                {repository.description}
              </Text>
            </VStack>

            {/* Tags */}
            <HStack spacing={2} wrap="wrap">
              {repository.tags.map((tag) => (
                <Badge key={tag} colorScheme="blue" variant="subtle">
                  {tag}
                </Badge>
              ))}
            </HStack>

            {/* Authors */}
            <VStack align="start" spacing={2}>
              <Text fontWeight="medium">Authors:</Text>
              <VStack align="start" spacing={1}>
                {repository.authors.map((author) => (
                  <Text key={author} color="gray.600">
                    {author}
                  </Text>
                ))}
              </VStack>
            </VStack>

            <VStack align="start" spacing={3} w="full">
              <Text fontWeight="medium">Repository Information</Text>
              <Box 
                bg="gray.50" 
                p={4} 
                borderRadius="md" 
                w="full"
                border="1px solid"
                borderColor="gray.200"
              >
                <Text fontSize="sm" color="gray.600">
                  Category: {repository.category}
                </Text>
                <Text fontSize="sm" color="gray.600">
                  Stars: {repository.starCount}
                </Text>
              </Box>
            </VStack>

            <HStack spacing={4} pt={4}>
              <Button bg="blue.500" color="white" _hover={{ bg: "blue.600" }}>
                Clone Repository
              </Button>
              <Button variant="outline">
                Download ZIP
              </Button>
            </HStack>
          </VStack>
        </Box>
      </VStack>
    </Box>
  );
};