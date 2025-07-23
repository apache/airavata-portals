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
import { Box, VStack, Text, Button } from '@chakra-ui/react';
import { useNavigate } from 'react-router';
import { adminApiService } from '../../lib/adminApi';

export const AddModelForm = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim() || !description.trim()) {
      alert('Please fill in title and description');
      return;
    }

    setLoading(true);
    try {
      const newModel = {
        title: title.trim(),
        description: description.trim(),
        category: 'medical',
        tags: ['test'],
        authors: ['test@user.com'],
        starCount: 0
      };

      console.log('Submitting model:', newModel);
      const createdModel = await adminApiService.createModel(newModel);
      console.log('Model created successfully:', createdModel);
      
      navigate('/resources/models');
    } catch (error) {
      console.error('Failed to create model:', error);
      alert('Failed to create model. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box bg="gray.50" minH="100vh" p={8}>
      <VStack spacing={6} maxW="600px" mx="auto">
        <Button
          onClick={() => navigate('/resources/models')}
          color="gray.600"
        >
          ← Back to Models
        </Button>
        
        <Text fontSize="2xl" fontWeight="bold">
          Add New Model
        </Text>
        
        <Box bg="white" p={6} borderRadius="lg" w="full">
          <VStack as="form" onSubmit={handleSubmit} spacing={4}>
            <VStack w="full" align="start">
              <Text fontWeight="medium">Title *</Text>
              <Box
                as="input"
                type="text"
                placeholder="Enter model title"
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
                placeholder="Describe your model"
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

            <Button
              type="submit"
              bg="blue.500"
              color="white"
              _hover={{ bg: "blue.600" }}
              disabled={loading}
              w="full"
              mt={4}
            >
              {loading ? 'Creating...' : 'Create Model'}
            </Button>
          </VStack>
        </Box>
      </VStack>
    </Box>
  );
};