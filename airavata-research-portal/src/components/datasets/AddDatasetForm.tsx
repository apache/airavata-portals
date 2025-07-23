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

import React, { useState } from 'react';
import { Box, VStack, HStack, Text, Button } from '@chakra-ui/react';
import { useNavigate } from 'react-router';
import { adminApiService } from '../../lib/adminApi';

type UploadOption = 'file' | 'url' | 'repository';

export const AddDatasetForm = () => {
  const navigate = useNavigate();
  const [selectedOption, setSelectedOption] = useState<UploadOption | null>(null);
  const [loading, setLoading] = useState(false);
  
  // Form states for different options
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [url, setUrl] = useState('');
  const [repositoryUrl, setRepositoryUrl] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim() || !description.trim()) {
      alert('Please fill in title and description');
      return;
    }

    if (!selectedOption) {
      alert('Please select an upload option');
      return;
    }

    setLoading(true);
    try {
      const newDataset = {
        title: title.trim(),
        description: description.trim(),
        category: 'medical',
        tags: ['test', selectedOption],
        authors: ['test@user.com'],
        starCount: 0,
        sourceType: selectedOption,
        sourceUrl: selectedOption === 'url' ? url : selectedOption === 'repository' ? repositoryUrl : null
      };

      console.log('Submitting dataset:', newDataset);
      const createdDataset = await adminApiService.createDataset(newDataset);
      console.log('Dataset created successfully:', createdDataset);
      
      navigate('/resources/datasets');
    } catch (error) {
      console.error('Failed to create dataset:', error);
      alert('Failed to create dataset. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderUploadOptions = () => {
    if (selectedOption) return null;

    return (
      <VStack spacing={4} w="full">
        <Text fontSize="lg" fontWeight="medium" textAlign="center">
          Easily share and publish your datasets for others to access and use.
        </Text>
        
        <Text fontSize="sm" color="gray.600" textAlign="center">
          File • Link • Dataset Output
        </Text>

        <HStack spacing={6} justify="center" pt={4}>
          {/* File Upload Option */}
          <VStack
            spacing={3}
            p={6}
            border="2px solid"
            borderColor="gray.200"
            borderRadius="lg"
            cursor="pointer"
            _hover={{ borderColor: "blue.300", bg: "blue.50" }}
            onClick={() => setSelectedOption('file')}
            w="140px"
            h="140px"
            justify="center"
          >
            <Box
              w="50px"
              h="50px"
              bg="blue.100"
              borderRadius="full"
              display="flex"
              alignItems="center"
              justifyContent="center"
            >
              <Text fontSize="24px">📁</Text>
            </Box>
            <Text fontSize="sm" fontWeight="medium" textAlign="center">
              Upload Files
            </Text>
          </VStack>

          {/* URL Option */}
          <VStack
            spacing={3}
            p={6}
            border="2px solid"
            borderColor="gray.200"
            borderRadius="lg"
            cursor="pointer"
            _hover={{ borderColor: "blue.300", bg: "blue.50" }}
            onClick={() => setSelectedOption('url')}
            w="140px"
            h="140px"
            justify="center"
          >
            <Box
              w="50px"
              h="50px"
              bg="green.100"
              borderRadius="full"
              display="flex"
              alignItems="center"
              justifyContent="center"
            >
              <Text fontSize="24px">🔗</Text>
            </Box>
            <Text fontSize="sm" fontWeight="medium" textAlign="center">
              Remote URL
            </Text>
          </VStack>

          {/* Repository Option */}
          <VStack
            spacing={3}
            p={6}
            border="2px solid"
            borderColor="gray.200"
            borderRadius="lg"
            cursor="pointer"
            _hover={{ borderColor: "blue.300", bg: "blue.50" }}
            onClick={() => setSelectedOption('repository')}
            w="140px"
            h="140px"
            justify="center"
          >
            <Box
              w="50px"
              h="50px"
              bg="purple.100"
              borderRadius="full"
              display="flex"
              alignItems="center"
              justifyContent="center"
            >
              <Text fontSize="24px">📚</Text>
            </Box>
            <Text fontSize="sm" fontWeight="medium" textAlign="center">
              GitHub Repository
            </Text>
          </VStack>
        </HStack>

        <Text fontSize="xs" color="gray.500" textAlign="center" pt={4}>
          Upload your dataset using either this link.
        </Text>
      </VStack>
    );
  };

  const renderSelectedOptionForm = () => {
    if (!selectedOption) return null;

    return (
      <VStack spacing={4} w="full">
        <HStack w="full" justify="space-between" align="center">
          <Text fontSize="lg" fontWeight="medium">
            Upload Data - {selectedOption === 'file' ? 'File Upload' : selectedOption === 'url' ? 'Remote URL' : 'GitHub Repository'}
          </Text>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setSelectedOption(null)}
          >
            ← Back
          </Button>
        </HStack>

        <VStack as="form" onSubmit={handleSubmit} spacing={4} w="full">
          {/* Basic Info */}
          <VStack w="full" align="start">
            <Text fontWeight="medium">Dataset Title *</Text>
            <Box
              as="input"
              type="text"
              placeholder="Enter dataset title"
              value={title}
              onChange={(e: any) => setTitle(e.target.value)}
              w="full"
              p={3}
              border="1px solid"
              borderColor="gray.300"
              borderRadius="md"
              _focus={{ borderColor: "blue.500" }}
            />
          </VStack>

          <VStack w="full" align="start">
            <Text fontWeight="medium">Description *</Text>
            <Box
              as="textarea"
              placeholder="Describe your dataset"
              value={description}
              onChange={(e: any) => setDescription(e.target.value)}
              w="full"
              p={3}
              border="1px solid"
              borderColor="gray.300"
              borderRadius="md"
              minH="100px"
              _focus={{ borderColor: "blue.500" }}
            />
          </VStack>

          {/* Option-specific fields */}
          {selectedOption === 'file' && (
            <VStack w="full" align="start">
              <Text fontWeight="medium">Files</Text>
              <Box
                w="full"
                h="120px"
                border="2px dashed"
                borderColor="gray.300"
                borderRadius="md"
                display="flex"
                alignItems="center"
                justifyContent="center"
                bg="gray.50"
                cursor="pointer"
                _hover={{ borderColor: "blue.300" }}
              >
                <VStack spacing={2}>
                  <Text fontSize="24px">📁</Text>
                  <Text fontSize="sm" color="gray.600">
                    Drop your files here to get started
                  </Text>
                  <Text fontSize="xs" color="gray.500">
                    or click to browse
                  </Text>
                </VStack>
              </Box>
            </VStack>
          )}

          {selectedOption === 'url' && (
            <VStack w="full" align="start">
              <Text fontWeight="medium">Remote URL *</Text>
              <Box
                as="input"
                type="url"
                placeholder="https://example.com/dataset.csv"
                value={url}
                onChange={(e: any) => setUrl(e.target.value)}
                w="full"
                p={3}
                border="1px solid"
                borderColor="gray.300"
                borderRadius="md"
                _focus={{ borderColor: "blue.500" }}
              />
            </VStack>
          )}

          {selectedOption === 'repository' && (
            <VStack w="full" align="start">
              <Text fontWeight="medium">GitHub Repository URL *</Text>
              <Box
                as="input"
                type="url"
                placeholder="https://github.com/username/repository"
                value={repositoryUrl}
                onChange={(e: any) => setRepositoryUrl(e.target.value)}
                w="full"
                p={3}
                border="1px solid"
                borderColor="gray.300"
                borderRadius="md"
                _focus={{ borderColor: "blue.500" }}
              />
            </VStack>
          )}

          <Button
            type="submit"
            bg="blue.500"
            color="white"
            _hover={{ bg: "blue.600" }}
            disabled={loading}
            w="full"
            mt={4}
          >
            {loading ? 'Creating...' : 'Create Dataset'}
          </Button>
        </VStack>
      </VStack>
    );
  };

  return (
    <Box bg="gray.50" minH="100vh" p={8}>
      <VStack spacing={6} maxW="800px" mx="auto">
        <Button
          onClick={() => navigate('/resources/datasets')}
          color="gray.600"
          alignSelf="flex-start"
        >
          ← Back to Datasets
        </Button>
        
        <Text fontSize="2xl" fontWeight="bold">
          Upload Data
        </Text>
        
        <Box bg="white" p={8} borderRadius="lg" w="full" minH="400px">
          {renderUploadOptions()}
          {renderSelectedOptionForm()}
        </Box>
      </VStack>
    </Box>
  );
};