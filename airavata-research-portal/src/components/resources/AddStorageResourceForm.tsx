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
import { Box, VStack, HStack, Text, Button, Container, Input } from '@chakra-ui/react';
import { toaster } from '../ui/toaster';
import { useNavigate, useParams } from 'react-router-dom';
import { unifiedApiService } from '../../lib/apiConfig';

// Utility function to parse validation errors from backend
const parseValidationError = (error: any): string => {
  if (error.response?.data) {
    const errorData = error.response.data;
    
    // Handle structured validation error messages from backend
    if (typeof errorData === 'string' && errorData.includes('Validation failed:')) {
      return errorData.replace('Validation failed: ', '');
    }
    
    // Handle generic string error messages
    if (typeof errorData === 'string') {
      return errorData;
    }
    
    // Handle object error responses
    if (errorData.message) {
      return errorData.message;
    }
  }
  
  // Fallback to error message
  return error.message || 'An unexpected error occurred';
};

export const AddStorageResourceForm = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(!!id);
  
  const isEditMode = !!id;
  const [formData, setFormData] = useState({
    name: '',
    storageResourceDescription: '',
    hostName: '',
    storageType: 'S3',
    // Required fields for all storage types
    accessProtocol: 'HTTPS',
    capacityTB: 1,
    endpoint: '',
    // S3-specific fields
    bucketName: '',
    accessKey: '',
    secretKey: '',
    supportsEncryption: true,
    supportsVersioning: true,
    // SCP-specific fields
    port: 22,
    username: '',
    authenticationMethod: 'SSH_KEY',
    sshKey: '',
    remotePath: '',
    // Common fields
    resourceManager: '',
    additionalInfo: ''
  });

  useEffect(() => {
    if (isEditMode && id) {
      loadExistingResource();
    }
  }, [isEditMode, id]);

  const loadExistingResource = async () => {
    try {
      setInitialLoading(true);
      const resource = await unifiedApiService.getStorageResourceById(id!);
      
      setFormData({
        name: resource.name || '',
        storageResourceDescription: resource.storageResourceDescription || '',
        hostName: resource.hostName || '',
        storageType: resource.storageType || 'S3',
        // Required fields
        accessProtocol: resource.accessProtocol || (resource.storageType === 'S3' ? 'HTTPS' : 'SCP'),
        capacityTB: resource.capacityTB || 1,
        endpoint: resource.storageType === 'S3' 
          ? (resource.endpoint || resource.hostName || '') 
          : (resource.hostName || resource.endpoint || ''),
        // S3-specific fields
        bucketName: resource.bucketName || '',
        accessKey: resource.accessKey || '',
        secretKey: resource.secretKey || '',
        supportsEncryption: resource.supportsEncryption !== undefined ? resource.supportsEncryption : true,
        supportsVersioning: resource.supportsVersioning !== undefined ? resource.supportsVersioning : true,
        // SCP-specific fields
        port: resource.port || 22,
        username: resource.username || '',
        authenticationMethod: resource.authenticationMethod || 'SSH_KEY',
        sshKey: resource.sshKey || '',
        remotePath: resource.remotePath || '',
        // Common fields
        resourceManager: resource.resourceManager || '',
        additionalInfo: resource.additionalInfo || ''
      });
    } catch (error: any) {
      console.error('Failed to load storage resource:', error);
      toaster.create({
        title: "Error",
        description: "Failed to load storage resource data",
        type: "error",
      });
      navigate('/resources?tab=storage');
    } finally {
      setInitialLoading(false);
    }
  };

  const handleInputChange = (field: string, value: string | number | boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic validation
    if (!formData.name.trim() || !formData.storageResourceDescription.trim()) {
      toaster.create({
        title: "Validation Error",
        description: "Please fill in name and description",
        type: "error",
      });
      return;
    }

    // Storage type specific validation
    if (formData.storageType === 'S3') {
      if (!formData.endpoint.trim() || !formData.bucketName.trim() || !formData.accessKey.trim() || !formData.secretKey.trim()) {
        toaster.create({
          title: "Validation Error",
          description: "Please fill in all S3 fields: endpoint, bucket name, access key, and secret key",
          type: "error",
        });
        return;
      }
    } else if (formData.storageType === 'SCP') {
      if (!formData.hostName.trim() || !formData.username.trim() || !formData.remotePath.trim()) {
        toaster.create({
          title: "Validation Error",
          description: "Please fill in all SCP fields: hostname, username, and remote path",
          type: "error",
        });
        return;
      }
      if (formData.authenticationMethod === 'SSH_KEY' && !formData.sshKey.trim()) {
        toaster.create({
          title: "Validation Error",
          description: "Please provide SSH key for SSH key authentication",
          type: "error",
        });
        return;
      }
    }

    // Validate required fields for all storage types
    if (!formData.accessProtocol || formData.capacityTB < 1) {
      toaster.create({
        title: "Validation Error",
        description: "Please ensure access protocol is selected and capacity is at least 1 TB",
        type: "error",
      });
      return;
    }

    setLoading(true);
    try {
      // Create object matching StorageResourceDTO structure exactly
      const storageResourceData: any = {
        name: formData.name.trim(),
        hostName: formData.hostName.trim() || (formData.storageType === 'S3' ? formData.endpoint.trim() : formData.hostName.trim()),
        storageResourceDescription: formData.storageResourceDescription.trim(),
        storageType: formData.storageType,
        // Required fields for all storage types
        accessProtocol: formData.accessProtocol,
        capacityTB: parseInt(formData.capacityTB.toString()) || 1,
        endpoint: formData.endpoint.trim(),
        resourceManager: formData.resourceManager.trim() || 'Default Resource Manager',
        additionalInfo: formData.additionalInfo.trim() || null
      };

      // Add type-specific fields based on storage type
      if (formData.storageType === 'S3') {
        storageResourceData.bucketName = formData.bucketName.trim();
        storageResourceData.accessKey = formData.accessKey.trim();
        storageResourceData.secretKey = formData.secretKey.trim();
        storageResourceData.supportsEncryption = formData.supportsEncryption;
        storageResourceData.supportsVersioning = formData.supportsVersioning;
        // For S3, hostName should be the endpoint
        storageResourceData.hostName = formData.endpoint.trim();
      } else if (formData.storageType === 'SCP') {
        storageResourceData.port = parseInt(formData.port.toString()) || 22;
        storageResourceData.username = formData.username.trim();
        storageResourceData.authenticationMethod = formData.authenticationMethod;
        storageResourceData.sshKey = formData.sshKey.trim();
        storageResourceData.remotePath = formData.remotePath.trim();
        // For SCP, endpoint should be the hostname
        storageResourceData.endpoint = formData.hostName.trim();
      }

      console.log(`${isEditMode ? 'Updating' : 'Creating'} storage resource:`, storageResourceData);
      
      let result;
      if (isEditMode && id) {
        result = await unifiedApiService.updateStorageResource(id, storageResourceData);
        toaster.create({
          title: "Success",
          description: "Storage resource updated successfully",
          type: "success",
        });
        navigate(`/resources/storage/${id}`);
      } else {
        result = await unifiedApiService.createStorageResource(storageResourceData);
        toaster.create({
          title: "Success",
          description: "Storage resource created successfully",
          type: "success",
        });
        navigate('/resources?tab=storage');
      }
      
      console.log(`Storage resource ${isEditMode ? 'updated' : 'created'} successfully:`, result);
    } catch (error: any) {
      console.error(`Failed to ${isEditMode ? 'update' : 'create'} storage resource:`, error);
      toaster.create({
        title: "Error",
        description: `Failed to ${isEditMode ? 'update' : 'create'} storage resource: ${parseValidationError(error)}`,
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) {
    return (
      <Box bg="gray.50" minH="100vh" display="flex" alignItems="center" justifyContent="center">
        <Text>Loading storage resource...</Text>
      </Box>
    );
  }

  return (
    <Box bg="gray.50" minH="100vh">
      <Container maxW="1000px" py={8}>
        {/* Header */}
        <VStack spacing={8} align="stretch">
          <HStack>
            <Button
              variant="ghost"
              onClick={() => {
                if (isEditMode) {
                  navigate(`/resources/storage/${id}`);
                } else {
                  navigate('/resources?tab=storage');
                }
              }}
              color="gray.600"
              size="sm"
              leftIcon={<Text>←</Text>}
            >
              Back
            </Button>
          </HStack>

          {/* Title */}
          <VStack spacing={6} align="center">
            <Text fontSize="2xl" fontWeight="semibold" color="gray.800">
              {isEditMode ? 'Edit' : 'Add'} <Text as="span" color="#60B4F7">Storage Resource</Text>
            </Text>
            
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
                      placeholder="e.g., Campus Data Storage"
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

                {/* Hostname */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Hostname <Text as="span" color="red.500">*</Text>
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      placeholder="e.g., storage.university.edu"
                      value={formData.hostName}
                      onChange={(e) => handleInputChange('hostName', e.target.value)}
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
                      Description <Text as="span" color="red.500">*</Text>
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      placeholder="Brief description of the storage resource"
                      value={formData.storageResourceDescription}
                      onChange={(e) => handleInputChange('storageResourceDescription', e.target.value)}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                      required
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
                      onChange={(e: any) => {
                        const newType = e.target.value;
                        handleInputChange('storageType', newType);
                        // Update access protocol based on storage type
                        if (newType === 'S3') {
                          handleInputChange('accessProtocol', 'HTTPS');
                        } else if (newType === 'SCP') {
                          handleInputChange('accessProtocol', 'SCP');
                        }
                      }}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      p={2}
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                      w="full"
                    >
                      <option value="S3">S3</option>
                      <option value="SCP">SCP</option>
                    </Box>
                  </Box>
                </HStack>

                {/* Access Protocol */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Access Protocol <Text as="span" color="red.500">*</Text>
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Box as="select" 
                      value={formData.accessProtocol}
                      onChange={(e: any) => handleInputChange('accessProtocol', e.target.value)}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      p={2}
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                      w="full"
                    >
                      {formData.storageType === 'S3' ? (
                        <>
                          <option value="HTTPS">HTTPS</option>
                          <option value="HTTP">HTTP</option>
                        </>
                      ) : (
                        <>
                          <option value="SCP">SCP</option>
                          <option value="SFTP">SFTP</option>
                        </>
                      )}
                    </Box>
                  </Box>
                </HStack>

                {/* Capacity */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Capacity (TB) <Text as="span" color="red.500">*</Text>
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      type="number"
                      placeholder="Storage capacity in terabytes"
                      value={formData.capacityTB}
                      onChange={(e) => handleInputChange('capacityTB', parseInt(e.target.value) || 1)}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                      min={1}
                      required
                    />
                  </Box>
                </HStack>

                {/* S3-specific fields */}
                {formData.storageType === 'S3' && (
                  <>
                    {/* Endpoint */}
                    <HStack spacing={4} align="start">
                      <Box minW="200px" pt={2}>
                        <Text fontSize="sm" color="gray.700" fontWeight="medium">
                          Endpoint <Text as="span" color="red.500">*</Text>
                        </Text>
                      </Box>
                      <Text color="gray.500" pt={2}>:</Text>
                      <Box flex={1}>
                        <Input
                          placeholder="e.g., https://s3.amazonaws.com"
                          value={formData.endpoint}
                          onChange={(e) => handleInputChange('endpoint', e.target.value)}
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
                          placeholder="e.g., my-research-bucket"
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
                          Access Key <Text as="span" color="red.500">*</Text>
                        </Text>
                      </Box>
                      <Text color="gray.500" pt={2}>:</Text>
                      <Box flex={1}>
                        <Input
                          placeholder="e.g., AKIAIOSFODNN7EXAMPLE"
                          value={formData.accessKey}
                          onChange={(e) => handleInputChange('accessKey', e.target.value)}
                          bg="white"
                          border="1px solid"
                          borderColor="gray.300"
                          borderRadius="md"
                          _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                          required
                        />
                      </Box>
                    </HStack>

                    {/* Secret Key */}
                    <HStack spacing={4} align="start">
                      <Box minW="200px" pt={2}>
                        <Text fontSize="sm" color="gray.700" fontWeight="medium">
                          Secret Key <Text as="span" color="red.500">*</Text>
                        </Text>
                      </Box>
                      <Text color="gray.500" pt={2}>:</Text>
                      <Box flex={1}>
                        <Input
                          type="password"
                          placeholder="Secret access key"
                          value={formData.secretKey}
                          onChange={(e) => handleInputChange('secretKey', e.target.value)}
                          bg="white"
                          border="1px solid"
                          borderColor="gray.300"
                          borderRadius="md"
                          _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                          required
                        />
                      </Box>
                    </HStack>

                    {/* Supports Encryption */}
                    <HStack spacing={4} align="start">
                      <Box minW="200px" pt={2}>
                        <Text fontSize="sm" color="gray.700" fontWeight="medium">
                          Supports Encryption
                        </Text>
                      </Box>
                      <Text color="gray.500" pt={2}>:</Text>
                      <Box flex={1}>
                        <HStack spacing={2}>
                          <input
                            type="checkbox"
                            checked={formData.supportsEncryption}
                            onChange={(e) => handleInputChange('supportsEncryption', e.target.checked)}
                            style={{ accentColor: "#60B4F7" }}
                          />
                          <Text fontSize="sm" color="gray.600">Storage supports encryption</Text>
                        </HStack>
                      </Box>
                    </HStack>

                    {/* Supports Versioning */}
                    <HStack spacing={4} align="start">
                      <Box minW="200px" pt={2}>
                        <Text fontSize="sm" color="gray.700" fontWeight="medium">
                          Supports Versioning
                        </Text>
                      </Box>
                      <Text color="gray.500" pt={2}>:</Text>
                      <Box flex={1}>
                        <HStack spacing={2}>
                          <input
                            type="checkbox"
                            checked={formData.supportsVersioning}
                            onChange={(e) => handleInputChange('supportsVersioning', e.target.checked)}
                            style={{ accentColor: "#60B4F7" }}
                          />
                          <Text fontSize="sm" color="gray.600">Storage supports versioning</Text>
                        </HStack>
                      </Box>
                    </HStack>
                  </>
                )}

                {/* SCP-specific fields */}
                {formData.storageType === 'SCP' && (
                  <>

                    {/* Port */}
                    <HStack spacing={4} align="start">
                      <Box minW="200px" pt={2}>
                        <Text fontSize="sm" color="gray.700" fontWeight="medium">
                          Port <Text as="span" color="red.500">*</Text>
                        </Text>
                      </Box>
                      <Text color="gray.500" pt={2}>:</Text>
                      <Box flex={1}>
                        <Input
                          type="number"
                          placeholder="e.g., 22"
                          value={formData.port}
                          onChange={(e) => handleInputChange('port', parseInt(e.target.value) || 22)}
                          bg="white"
                          border="1px solid"
                          borderColor="gray.300"
                          borderRadius="md"
                          _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                          min={1}
                          max={65535}
                          required
                        />
                      </Box>
                    </HStack>

                    {/* Username */}
                    <HStack spacing={4} align="start">
                      <Box minW="200px" pt={2}>
                        <Text fontSize="sm" color="gray.700" fontWeight="medium">
                          Username <Text as="span" color="red.500">*</Text>
                        </Text>
                      </Box>
                      <Text color="gray.500" pt={2}>:</Text>
                      <Box flex={1}>
                        <Input
                          placeholder="e.g., researcher01"
                          value={formData.username}
                          onChange={(e) => handleInputChange('username', e.target.value)}
                          bg="white"
                          border="1px solid"
                          borderColor="gray.300"
                          borderRadius="md"
                          _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                          required
                        />
                      </Box>
                    </HStack>

                    {/* Authentication Method */}
                    <HStack spacing={4} align="start">
                      <Box minW="200px" pt={2}>
                        <Text fontSize="sm" color="gray.700" fontWeight="medium">
                          Authentication <Text as="span" color="red.500">*</Text>
                        </Text>
                      </Box>
                      <Text color="gray.500" pt={2}>:</Text>
                      <Box flex={1}>
                        <Box as="select" 
                          value={formData.authenticationMethod}
                          onChange={(e: any) => handleInputChange('authenticationMethod', e.target.value)}
                          bg="white"
                          border="1px solid"
                          borderColor="gray.300"
                          borderRadius="md"
                          p={2}
                          _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                          w="full"
                        >
                          <option value="SSH_KEY">SSH Key</option>
                          <option value="PASSWORD">Password</option>
                        </Box>
                      </Box>
                    </HStack>

                    {/* SSH Key (only show if SSH_KEY is selected) */}
                    {formData.authenticationMethod === 'SSH_KEY' && (
                      <HStack spacing={4} align="start">
                        <Box minW="200px" pt={2}>
                          <Text fontSize="sm" color="gray.700" fontWeight="medium">
                            SSH Key <Text as="span" color="red.500">*</Text>
                          </Text>
                        </Box>
                        <Text color="gray.500" pt={2}>:</Text>
                        <Box flex={1}>
                          <Box
                            as="textarea"
                            placeholder="-----BEGIN RSA PRIVATE KEY-----&#10;...&#10;-----END RSA PRIVATE KEY-----"
                            value={formData.sshKey}
                            onChange={(e: any) => handleInputChange('sshKey', e.target.value)}
                            bg="white"
                            border="1px solid"
                            borderColor="gray.300"
                            borderRadius="md"
                            p={2}
                            h="100px"
                            resize="vertical"
                            fontFamily="monospace"
                            fontSize="sm"
                            _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                            required
                          />
                        </Box>
                      </HStack>
                    )}

                    {/* Remote Path */}
                    <HStack spacing={4} align="start">
                      <Box minW="200px" pt={2}>
                        <Text fontSize="sm" color="gray.700" fontWeight="medium">
                          Remote Path <Text as="span" color="red.500">*</Text>
                        </Text>
                      </Box>
                      <Text color="gray.500" pt={2}>:</Text>
                      <Box flex={1}>
                        <Input
                          placeholder="e.g., /home/user/data"
                          value={formData.remotePath}
                          onChange={(e) => handleInputChange('remotePath', e.target.value)}
                          bg="white"
                          border="1px solid"
                          borderColor="gray.300"
                          borderRadius="md"
                          _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                          required
                        />
                      </Box>
                    </HStack>
                  </>
                )}

                {/* Resource Manager */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Resource Manager
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      placeholder="e.g., University IT Department (optional)"
                      value={formData.resourceManager}
                      onChange={(e) => handleInputChange('resourceManager', e.target.value)}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                    />
                  </Box>
                </HStack>

                {/* Additional Info */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Additional Info
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      placeholder="Any additional configuration details"
                      value={formData.additionalInfo}
                      onChange={(e) => handleInputChange('additionalInfo', e.target.value)}
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
                  disabled={loading}
                  fontWeight="medium"
                >
                  {loading 
                    ? (isEditMode ? "Updating..." : "Creating...") 
                    : (isEditMode ? "Update Storage Resource" : "Create Storage Resource")
                  }
                </Button>
              </HStack>
            </VStack>
          </Box>
        </VStack>
      </Container>
    </Box>
  );
};