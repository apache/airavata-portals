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
import { useNavigate, useParams } from 'react-router-dom';
import { v1ApiService } from '../../lib/v1Api';
import { normalizeTags, TagV2 } from "../../lib/tagUtils";

interface Dataset {
  id: string;
  name: string;
  description: string;
  tags: TagV2[];
  authors: string[];
  status: string;
  state: string;
  privacy: string;
  createdAt: string;
  updatedAt: string;
  datasetUrl: string;
  type: string;
}

export const DatasetDetail = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      fetchDataset(id);
    }
  }, [id]);

  const fetchDataset = async (datasetId: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await v1ApiService.getDatasetById(datasetId);
      setDataset(data);
    } catch (err) {
      console.error('Failed to fetch dataset:', err);
      setError('Failed to load dataset');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box bg="gray.50" minH="100vh" p={8}>
        <Text>Loading dataset...</Text>
      </Box>
    );
  }

  if (error || !dataset) {
    return (
      <Box bg="gray.50" minH="100vh" p={8}>
        <VStack spacing={4}>
          <Text color="red.500">{error || 'Dataset not found'}</Text>
          <Button onClick={() => navigate('/resources/datasets')}>
            ← Back to Datasets
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
            onClick={() => navigate('/resources/datasets')}
            color="gray.600"
            size="sm"
            leftIcon={<Text>←</Text>}
          >
            Back
          </Button>
          <HStack spacing={2}>
            <Button size="sm" variant="outline">
              Star
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
                {dataset.name}
              </Text>
              <Text color="gray.600" fontSize="lg">
                {dataset.description}
              </Text>
            </VStack>

            {/* Tags */}
            <HStack spacing={2} wrap="wrap">
              {normalizeTags(dataset.tags).map((tag, index) => (
                <Badge key={index} colorScheme="blue" variant="subtle">
                  {tag}
                </Badge>
              ))}
            </HStack>

            {/* Authors */}
            <VStack align="start" spacing={2}>
              <Text fontWeight="medium">Authors:</Text>
              <VStack align="start" spacing={1}>
                {dataset.authors.map((author) => (
                  <Text key={author} color="gray.600">
                    {author}
                  </Text>
                ))}
              </VStack>
            </VStack>

            <VStack align="start" spacing={3} w="full">
              <Text fontWeight="medium">Dataset Information</Text>
              <Box 
                bg="gray.50" 
                p={4} 
                borderRadius="md" 
                w="full"
                border="1px solid"
                borderColor="gray.200"
              >
                <Text fontSize="sm" color="gray.600">
                  Status: {dataset.status}
                </Text>
                <Text fontSize="sm" color="gray.600">
                  Privacy: {dataset.privacy}
                </Text>
                <Text fontSize="sm" color="gray.600">
                  Type: {dataset.type}
                </Text>
                <Text fontSize="sm" color="gray.600">
                  Created: {new Date(dataset.createdAt).toLocaleDateString()}
                </Text>
              </Box>
            </VStack>

            <HStack spacing={4} pt={4}>
              <Button bg="blue.500" color="white" _hover={{ bg: "blue.600" }}>
                Start Session
              </Button>
              <Button variant="outline">
                Download
              </Button>
            </HStack>
          </VStack>
        </Box>
      </VStack>
    </Box>
  );
};