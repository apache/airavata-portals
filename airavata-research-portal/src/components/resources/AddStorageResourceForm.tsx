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
import { Box, VStack, HStack, Text, Button, Container, Input } from '@chakra-ui/react';
import { useNavigate } from 'react-router';
import { adminApiService } from '../../lib/adminApi';

export const AddStorageResourceForm = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    storageType: 'S3',
    endPointUrl: '',
    bucketName: '',
    accessKey: '',
    secretKey: ''
  });

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim() || !formData.description.trim()) {
      alert('Please fill in name and description');
      return;
    }

    if (!formData.endPointUrl.trim() || !formData.bucketName.trim()) {
      alert('Please fill in endpoint URL and bucket name');
      return;
    }

    setLoading(true);
    try {
      const newStorageResource = {
        name: formData.name.trim(),
        description: formData.description.trim(),
        storageType: formData.storageType,
        storage: `${formData.bucketName} (${formData.endPointUrl})`,
        status: 'ACTIVE'
      };

      console.log('Submitting storage resource:', newStorageResource);
      const createdResource = await adminApiService.createStorageResource(newStorageResource);
      console.log('Storage resource created successfully:', createdResource);
      
      navigate('/resources?tab=storage');
    } catch (error) {
      console.error('Failed to create storage resource:', error);
      alert('Failed to create storage resource. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box bg="gray.50" minH="100vh">
      <Container maxW="1000px" py={8}>
        {/* Header */}
        <VStack spacing={8} align="stretch">
          <HStack>
            <Button
              variant="ghost"
              onClick={() => navigate('/resources?tab=storage')}
              color="gray.600"
              size="sm"
              leftIcon={<Text>←</Text>}
            >
              Back
            </Button>
          </HStack>

          {/* Title and Steps */}
          <VStack spacing={6} align="center">
            <Text fontSize="2xl" fontWeight="semibold" color="gray.800">
              Add <Text as="span" color="#60B4F7">Storage Resource</Text>
            </Text>
            
            {/* Single Step Indicator */}
            <Box
              bg="black"
              color="white"
              px={3}
              py={1}
              borderRadius="full"
              fontSize="sm"
              fontWeight="medium"
            >
              Storage Resource Setup
            </Box>

            <Text color="gray.600" textAlign="center" fontSize="sm" maxW="600px" lineHeight="1.6">
              Provide a name, description, and select the type of storage you want to register. The form will update to show the relevant fields based on your chosen storage type.
            </Text>
          </VStack>

          {/* Form */}
          <Box bg="white" p={8} borderRadius="lg" border="1px solid" borderColor="gray.200">
            <VStack as="form" onSubmit={handleSubmit} spacing={8} align="stretch">
              {/* Form Fields */}
              <VStack spacing={6} align="stretch">
                {/* Name */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Name <Text as="span" color="red.500">*</Text>
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      placeholder=""
                      value={formData.name}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                      required
                    />
                  </Box>
                </HStack>

                {/* Description */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Description
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      placeholder=""
                      value={formData.description}
                      onChange={(e) => handleInputChange('description', e.target.value)}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                    />
                  </Box>
                </HStack>

                {/* Storage Type */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Storage Type <Text as="span" color="red.500">*</Text>
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Box as="select" 
                      value={formData.storageType}
                      onChange={(e: any) => handleInputChange('storageType', e.target.value)}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      p={2}
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                      w="full"
                    >
                      <option value="S3">S3</option>
                      <option value="GCS">Google Cloud Storage</option>
                      <option value="Azure">Azure Blob Storage</option>
                    </Box>
                  </Box>
                </HStack>

                {/* End Point URL */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      End Point URL <Text as="span" color="red.500">*</Text>
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      placeholder="https://your-storage-endpoint.com"
                      value={formData.endPointUrl}
                      onChange={(e) => handleInputChange('endPointUrl', e.target.value)}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                      required
                    />
                  </Box>
                </HStack>

                {/* Bucket Name */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Bucket Name <Text as="span" color="red.500">*</Text>
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      placeholder="bucket-name"
                      value={formData.bucketName}
                      onChange={(e) => handleInputChange('bucketName', e.target.value)}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                      required
                    />
                  </Box>
                </HStack>

                {/* Access Key */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Access Key
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      placeholder="Your access key"
                      value={formData.accessKey}
                      onChange={(e) => handleInputChange('accessKey', e.target.value)}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                    />
                  </Box>
                </HStack>

                {/* Secret Key */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Secret Key
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      type="password"
                      placeholder="Your secret key"
                      value={formData.secretKey}
                      onChange={(e) => handleInputChange('secretKey', e.target.value)}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                    />
                  </Box>
                </HStack>
              </VStack>

              {/* Submit Button */}
              <HStack justify="center" pt={6}>
                <Button
                  type="submit"
                  bg="black"
                  color="white"
                  size="lg"
                  px={8}
                  py={3}
                  borderRadius="md"
                  _hover={{ bg: "gray.800" }}
                  loading={loading}
                  fontWeight="medium"
                >
                  {loading ? "Creating..." : "Verify & Create"}
                </Button>
              </HStack>
            </VStack>
          </Box>
        </VStack>
      </Container>
    </Box>
  );
};