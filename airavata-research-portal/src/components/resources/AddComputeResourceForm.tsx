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
import { Box, VStack, HStack, Text, Button, Container, Input, Textarea } from '@chakra-ui/react';
import { useNavigate, useParams } from 'react-router-dom';
import { unifiedApiService } from '../../lib/apiConfig';
import { toaster } from '../ui/toaster';

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

interface QueueFormData {
  queueName: string;
  queueDescription: string;
  queueMaxRunTime: number;
  queueMaxNodes: number;
  queueMaxProcessors: number;
  maxJobsInQueue: number;
  cpusPerNode: number;
  defaultNodeCount: number;
  defaultCpuCount: number;
  defaultWallTime: number;
  queueSpecificMacros: string;
  isDefaultQueue: boolean;
}

const QueueModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  onSave: (queue: QueueFormData) => void;
  initialData?: QueueFormData;
}> = ({ isOpen, onClose, onSave, initialData }) => {
  const [queueData, setQueueData] = useState<QueueFormData>({
    queueName: '',
    queueDescription: '',
    queueMaxRunTime: 1440,
    queueMaxNodes: 1,
    queueMaxProcessors: 1,
    maxJobsInQueue: 100,
    cpusPerNode: 1,
    defaultNodeCount: 1,
    defaultCpuCount: 1,
    defaultWallTime: 60,
    queueSpecificMacros: '',
    isDefaultQueue: false,
    ...initialData,
  });

  const handleInputChange = (field: keyof QueueFormData, value: string | number | boolean) => {
    setQueueData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = () => {
    onSave(queueData);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <Box
      position="fixed"
      top="0"
      left="0"
      right="0"
      bottom="0"
      bg="rgba(0,0,0,0.5)"
      display="flex"
      alignItems="center"
      justifyContent="center"
      zIndex="1000"
    >
      <Box
        bg="white"
        borderRadius="lg"
        p={6}
        maxW="600px"
        w="90%"
        maxH="80vh"
        overflowY="auto"
      >
        <HStack justify="space-between" mb={6}>
          <Text fontSize="xl" fontWeight="semibold">Add a Queue</Text>
          <Button
            variant="ghost"
            onClick={onClose}
            color="red.500"
            fontSize="xl"
            p={2}
          >
            ✕
          </Button>
        </HStack>

        <VStack spacing={4} align="stretch">
          {/* Queue Name */}
          <HStack spacing={4} align="start">
            <Box minW="180px" pt={2}>
              <Text fontSize="sm" color="gray.700" fontWeight="medium">Queue Name</Text>
            </Box>
            <Text color="gray.500" pt={2}>:</Text>
            <Box flex={1}>
              <Input
                placeholder="Queue name"
                value={queueData.queueName}
                onChange={(e) => handleInputChange('queueName', e.target.value)}
                bg="gray.50"
                border="1px solid"
                borderColor="gray.300"
                borderRadius="md"
                _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
              />
            </Box>
          </HStack>

          {/* Queue Description */}
          <HStack spacing={4} align="start">
            <Box minW="180px" pt={2}>
              <Text fontSize="sm" color="gray.700" fontWeight="medium">Queue Description</Text>
            </Box>
            <Text color="gray.500" pt={2}>:</Text>
            <Box flex={1}>
              <Input
                placeholder="Queue description"
                value={queueData.queueDescription}
                onChange={(e) => handleInputChange('queueDescription', e.target.value)}
                bg="gray.50"
                border="1px solid"
                borderColor="gray.300"
                borderRadius="md"
                _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
              />
            </Box>
          </HStack>

          {/* Queue Max Run Time */}
          <HStack spacing={4} align="start">
            <Box minW="180px" pt={2}>
              <Text fontSize="sm" color="gray.700" fontWeight="medium">Queue Max Run Time</Text>
            </Box>
            <Text color="gray.500" pt={2}>:</Text>
            <Box flex={1}>
              <Input
                type="number"
                placeholder="Max run time in minutes"
                value={queueData.queueMaxRunTime}
                onChange={(e) => handleInputChange('queueMaxRunTime', parseInt(e.target.value) || 0)}
                bg="gray.50"
                border="1px solid"
                borderColor="gray.300"
                borderRadius="md"
                _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
              />
            </Box>
          </HStack>

          {/* Queue Max Nodes */}
          <HStack spacing={4} align="start">
            <Box minW="180px" pt={2}>
              <Text fontSize="sm" color="gray.700" fontWeight="medium">Queue Max Nodes</Text>
            </Box>
            <Text color="gray.500" pt={2}>:</Text>
            <Box flex={1}>
              <Input
                type="number"
                placeholder="Max nodes"
                value={queueData.queueMaxNodes}
                onChange={(e) => handleInputChange('queueMaxNodes', parseInt(e.target.value) || 0)}
                bg="gray.50"
                border="1px solid"
                borderColor="gray.300"
                borderRadius="md"
                _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
              />
            </Box>
          </HStack>

          {/* Queue Max Processors */}
          <HStack spacing={4} align="start">
            <Box minW="180px" pt={2}>
              <Text fontSize="sm" color="gray.700" fontWeight="medium">Queue Max Processors</Text>
            </Box>
            <Text color="gray.500" pt={2}>:</Text>
            <Box flex={1}>
              <Input
                type="number"
                placeholder="Max processors"
                value={queueData.queueMaxProcessors}
                onChange={(e) => handleInputChange('queueMaxProcessors', parseInt(e.target.value) || 0)}
                bg="gray.50"
                border="1px solid"
                borderColor="gray.300"
                borderRadius="md"
                _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
              />
            </Box>
          </HStack>

          {/* Max Jobs in Queue */}
          <HStack spacing={4} align="start">
            <Box minW="180px" pt={2}>
              <Text fontSize="sm" color="gray.700" fontWeight="medium">Max Jobs in Queue</Text>
            </Box>
            <Text color="gray.500" pt={2}>:</Text>
            <Box flex={1}>
              <Input
                type="number"
                placeholder="Max jobs"
                value={queueData.maxJobsInQueue}
                onChange={(e) => handleInputChange('maxJobsInQueue', parseInt(e.target.value) || 0)}
                bg="gray.50"
                border="1px solid"
                borderColor="gray.300"
                borderRadius="md"
                _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
              />
            </Box>
          </HStack>

          {/* CPUs per Node */}
          <HStack spacing={4} align="start">
            <Box minW="180px" pt={2}>
              <Text fontSize="sm" color="gray.700" fontWeight="medium">CPUs per Node</Text>
            </Box>
            <Text color="gray.500" pt={2}>:</Text>
            <Box flex={1}>
              <Input
                type="number"
                placeholder="CPUs per node"
                value={queueData.cpusPerNode}
                onChange={(e) => handleInputChange('cpusPerNode', parseInt(e.target.value) || 0)}
                bg="gray.50"
                border="1px solid"
                borderColor="gray.300"
                borderRadius="md"
                _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
              />
            </Box>
          </HStack>

          {/* Default Node Count */}
          <HStack spacing={4} align="start">
            <Box minW="180px" pt={2}>
              <Text fontSize="sm" color="gray.700" fontWeight="medium">Default Node Count</Text>
            </Box>
            <Text color="gray.500" pt={2}>:</Text>
            <Box flex={1}>
              <Input
                type="number"
                placeholder="Default node count"
                value={queueData.defaultNodeCount}
                onChange={(e) => handleInputChange('defaultNodeCount', parseInt(e.target.value) || 0)}
                bg="gray.50"
                border="1px solid"
                borderColor="gray.300"
                borderRadius="md"
                _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
              />
            </Box>
          </HStack>

          {/* Default CPU Count */}
          <HStack spacing={4} align="start">
            <Box minW="180px" pt={2}>
              <Text fontSize="sm" color="gray.700" fontWeight="medium">Default CPU Count</Text>
            </Box>
            <Text color="gray.500" pt={2}>:</Text>
            <Box flex={1}>
              <Input
                type="number"
                placeholder="Default CPU count"
                value={queueData.defaultCpuCount}
                onChange={(e) => handleInputChange('defaultCpuCount', parseInt(e.target.value) || 0)}
                bg="gray.50"
                border="1px solid"
                borderColor="gray.300"
                borderRadius="md"
                _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
              />
            </Box>
          </HStack>

          {/* Default Wall Time */}
          <HStack spacing={4} align="start">
            <Box minW="180px" pt={2}>
              <Text fontSize="sm" color="gray.700" fontWeight="medium">Default Wall Time</Text>
            </Box>
            <Text color="gray.500" pt={2}>:</Text>
            <Box flex={1}>
              <Input
                type="number"
                placeholder="Default wall time in minutes"
                value={queueData.defaultWallTime}
                onChange={(e) => handleInputChange('defaultWallTime', parseInt(e.target.value) || 0)}
                bg="gray.50"
                border="1px solid"
                borderColor="gray.300"
                borderRadius="md"
                _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
              />
            </Box>
          </HStack>

          {/* Queue Specific Macros */}
          <HStack spacing={4} align="start">
            <Box minW="180px" pt={2}>
              <Text fontSize="sm" color="gray.700" fontWeight="medium">Queue Specific Macros</Text>
            </Box>
            <Text color="gray.500" pt={2}>:</Text>
            <Box flex={1}>
              <Input
                placeholder="Queue specific macros"
                value={queueData.queueSpecificMacros}
                onChange={(e) => handleInputChange('queueSpecificMacros', e.target.value)}
                bg="gray.50"
                border="1px solid"
                borderColor="gray.300"
                borderRadius="md"
                _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
              />
            </Box>
          </HStack>
        </VStack>

        <HStack justify="center" mt={8} pt={4}>
          <Button
            bg="black"
            color="white"
            onClick={handleSave}
            px={8}
            py={2}
            borderRadius="md"
            _hover={{ bg: "gray.800" }}
          >
            Save
          </Button>
        </HStack>
      </Box>
    </Box>
  );
};

export const AddComputeResourceForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(!!id);
  const [currentStep, setCurrentStep] = useState(1);
  const [autoFill, setAutoFill] = useState(false);
  const [showQueueModal, setShowQueueModal] = useState(false);
  const [queues, setQueues] = useState<QueueFormData[]>([]);
  
  const isEditMode = !!id;
  
  const [formData, setFormData] = useState({
    // Step 1 fields
    name: '',
    hostName: '',
    hostAliases: [''],
    ipAddresses: [''],
    resourceDescription: '',
    // SSH configuration (mapped from JobSubmissionInterface)
    sshPort: 22,
    alternativeSSHHostName: '',
    securityProtocol: 'SSH_KEYS',
    
    // Required backend fields
    computeType: 'HPC',
    cpuCores: 1,
    memoryGB: 1,
    operatingSystem: 'Linux',
    queueSystem: 'SLURM',
    
    // Job management fields (mapped from JobSubmissionInterface -> SSHJobSubmission -> ResourceJobManager)
    resourceJobManagerType: 'SLURM',
    dataMovementProtocol: 'SCP',
    
    // Backend compatibility fields
    additionalInfo: '',
    resourceManager: ''
  });

  useEffect(() => {
    if (isEditMode && id) {
      loadExistingResource();
    }
  }, [isEditMode, id]);

  const loadExistingResource = async () => {
    try {
      setInitialLoading(true);
      const resource = await unifiedApiService.getComputeResourceById(id!);
      
      setFormData({
        name: resource.name || '',
        hostName: resource.hostName || '',
        hostAliases: resource.hostAliases || [''],
        ipAddresses: resource.ipAddresses || [''], 
        resourceDescription: resource.resourceDescription || '',
        // SSH configuration
        sshPort: resource.sshPort || 22,
        alternativeSSHHostName: resource.alternativeSSHHostName || '',
        securityProtocol: resource.securityProtocol || 'SSH_KEYS',
        // Required backend fields
        computeType: resource.computeType || 'HPC',
        cpuCores: resource.cpuCores || 1,
        memoryGB: resource.memoryGB || 1,
        operatingSystem: resource.operatingSystem || 'Linux',
        queueSystem: resource.queueSystem || 'SLURM',
        resourceJobManagerType: resource.resourceJobManagerType || 'SLURM',
        dataMovementProtocol: resource.dataMovementProtocol || 'SCP',
        // Backend compatibility fields
        additionalInfo: resource.additionalInfo || '',
        resourceManager: resource.resourceManager || ''
      });
      
      // Load queues if available
      if (resource.queues) {
        setQueues(resource.queues);
      }
    } catch (error: any) {
      console.error('Failed to load compute resource:', error);
      toaster.create({
        title: "Error",
        description: "Failed to load compute resource data",
        type: "error",
      });
      navigate('/resources?tab=compute');
    } finally {
      setInitialLoading(false);
    }
  };

  const handleInputChange = (field: string, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleArrayInputChange = (field: 'hostAliases' | 'ipAddresses', index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].map((item, i) => i === index ? value : item)
    }));
  };

  const addArrayField = (field: 'hostAliases' | 'ipAddresses') => {
    setFormData(prev => ({
      ...prev,
      [field]: [...prev[field], '']
    }));
  };

  const removeArrayField = (field: 'hostAliases' | 'ipAddresses', index: number) => {
    if (formData[field].length > 1) {
      setFormData(prev => ({
        ...prev,
        [field]: prev[field].filter((_, i) => i !== index)
      }));
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    } else {
      if (isEditMode) {
        navigate(`/resources/compute/${id}`);
      } else {
        navigate('/resources?tab=compute');
      }
    }
  };

  const handleNext = () => {
    if (currentStep < 2) {
      setCurrentStep(currentStep + 1);
    }
  };

  const addQueue = (queueData: QueueFormData) => {
    setQueues(prev => [...prev, queueData]);
  };

  const removeQueue = (index: number) => {
    setQueues(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!formData.name.trim() || !formData.hostName.trim() || !formData.resourceDescription.trim()) {
      toaster.create({
        title: "Validation Error",
        description: "Please fill in all required fields: name, hostname, and description",
        type: "error",
      });
      return;
    }

    if (!formData.computeType || !formData.operatingSystem || !formData.queueSystem) {
      toaster.create({
        title: "Validation Error",
        description: "Please select compute type, operating system, and queue system",
        type: "error",
      });
      return;
    }

    if (formData.cpuCores < 1 || formData.memoryGB < 1) {
      toaster.create({
        title: "Validation Error",
        description: "CPU cores and memory must be at least 1",
        type: "error",
      });
      return;
    }


    setLoading(true);

    try {
      // Create object matching ComputeResourceDTO structure exactly
      const computeResourceData = {
        name: formData.name.trim(),
        hostName: formData.hostName.trim() || formData.name.toLowerCase().replace(/\s+/g, '-') + '.compute.edu',
        resourceDescription: formData.resourceDescription.trim(),
        hostAliases: formData.hostAliases.filter(alias => alias.trim() !== ''),
        ipAddresses: formData.ipAddresses.filter(ip => ip.trim() !== ''),
        // Required backend fields
        computeType: formData.computeType,
        cpuCores: parseInt(formData.cpuCores.toString()) || 1,
        memoryGB: parseInt(formData.memoryGB.toString()) || 1,
        operatingSystem: formData.operatingSystem,
        queueSystem: formData.queueSystem,
        // SSH configuration (mapped from JobSubmissionInterface)
        sshPort: parseInt(formData.sshPort.toString()) || 22,
        alternativeSSHHostName: formData.alternativeSSHHostName.trim() || null,
        securityProtocol: formData.securityProtocol,
        // Job management fields
        resourceJobManagerType: formData.resourceJobManagerType,
        dataMovementProtocol: formData.dataMovementProtocol,
        resourceManager: formData.resourceManager.trim() || 'Default Resource Manager',
        additionalInfo: formData.additionalInfo.trim() || null,
        queues: queues
      };

      console.log(`${isEditMode ? 'Updating' : 'Creating'} compute resource:`, computeResourceData);
      
      let result;
      if (isEditMode && id) {
        result = await unifiedApiService.updateComputeResource(id, computeResourceData);
        toaster.create({
          title: "Success",
          description: "Compute resource updated successfully",
          type: "success",
        });
        navigate(`/resources/compute/${id}`);
      } else {
        result = await unifiedApiService.createComputeResource(computeResourceData);
        toaster.create({
          title: "Success", 
          description: "Compute resource created successfully",
          type: "success",
        });
        navigate('/resources?tab=compute');
      }
      
      console.log(`Compute resource ${isEditMode ? 'updated' : 'created'} successfully:`, result);
    } catch (error: any) {
      console.error(`Failed to ${isEditMode ? 'update' : 'create'} compute resource:`, error);
      toaster.create({
        title: "Error",
        description: `Failed to ${isEditMode ? 'update' : 'create'} compute resource: ${parseValidationError(error)}`,
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) {
    return (
      <Box bg="gray.50" minH="100vh" display="flex" alignItems="center" justifyContent="center">
        <Text>Loading compute resource...</Text>
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
              onClick={handleBack}
              color="gray.600"
              size="sm"
              leftIcon={<Text>←</Text>}
            >
              Back
            </Button>
          </HStack>

          {/* Title and Step Indicator */}
          <VStack spacing={6} align="center">
            <Text fontSize="2xl" fontWeight="semibold" color="gray.800">
              {isEditMode ? 'Edit' : 'Add'} <Text as="span" color="#60B4F7">Compute Resource</Text>
            </Text>
            
            {/* Step Indicator */}
            <HStack spacing={4}>
              <HStack spacing={2}>
                <Box
                  bg={currentStep === 1 ? "black" : "gray.300"}
                  color="white"
                  borderRadius="full"
                  w={8}
                  h={8}
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  fontSize="sm"
                  fontWeight="bold"
                >
                  1
                </Box>
                <Text fontSize="sm" fontWeight={currentStep === 1 ? "semibold" : "normal"}>
                  Step 1
                </Text>
              </HStack>
              
              <Box w={8} h={1} bg="gray.300" />
              
              <HStack spacing={2}>
                <Box
                  bg={currentStep === 2 ? "black" : "gray.300"}
                  color="white"
                  borderRadius="full"
                  w={8}
                  h={8}
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  fontSize="sm"
                  fontWeight="bold"
                >
                  2
                </Box>
                <Text fontSize="sm" fontWeight={currentStep === 2 ? "semibold" : "normal"}>
                  Step 2
                </Text>
              </HStack>
            </HStack>
            
            <Text color="gray.600" textAlign="center" fontSize="sm" maxW="600px" lineHeight="1.6">
              {currentStep === 1 
                ? "Fill in the basic information to connect your compute resource. Ensure the hostname and SSH credentials are accurate to allow CyberShuttle to establish a secure connection and access the system for running jobs."
                : "Retrieve configuration details directly from the HPC system."
              }
            </Text>
          </VStack>

          {/* Form */}
          <Box bg="white" p={8} borderRadius="lg" border="1px solid" borderColor="gray.200">
            <VStack as="form" onSubmit={handleSubmit} spacing={8} align="stretch">
              
              {currentStep === 1 && (
                <VStack spacing={6} align="stretch">
                  {/* Resource Name */}
                  <HStack spacing={4} align="start">
                    <Box minW="200px" pt={2}>
                      <Text fontSize="sm" color="gray.700" fontWeight="medium">
                        Resource Name <Text as="span" color="red.500">*</Text>
                      </Text>
                    </Box>
                    <Text color="gray.500" pt={2}>:</Text>
                    <Box flex={1}>
                      <Input
                        placeholder="e.g., University HPC Cluster"
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

                  {/* Host Name */}
                  <HStack spacing={4} align="start">
                    <Box minW="200px" pt={2}>
                      <Text fontSize="sm" color="gray.700" fontWeight="medium">
                        Hostname <Text as="span" color="red.500">*</Text>
                      </Text>
                    </Box>
                    <Text color="gray.500" pt={2}>:</Text>
                    <Box flex={1}>
                      <Input
                        placeholder="Hostname or IP address"
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

                  {/* Host Aliases */}
                  <HStack spacing={4} align="start">
                    <Box minW="200px" pt={2}>
                      <Text fontSize="sm" color="gray.700" fontWeight="medium">Host Aliases</Text>
                    </Box>
                    <Text color="gray.500" pt={2}>:</Text>
                    <Box flex={1}>
                      <VStack spacing={2} align="stretch">
                        {formData.hostAliases.map((alias, index) => (
                          <HStack key={index} spacing={2}>
                            <Input
                              placeholder="Alternative hostname"
                              value={alias}
                              onChange={(e) => handleArrayInputChange('hostAliases', index, e.target.value)}
                              bg="white"
                              border="1px solid"
                              borderColor="gray.300"
                              borderRadius="md"
                              _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                            />
                            {formData.hostAliases.length > 1 && (
                              <Button
                                variant="ghost"
                                onClick={() => removeArrayField('hostAliases', index)}
                                color="red.500"
                                size="sm"
                              >
                                ×
                              </Button>
                            )}
                          </HStack>
                        ))}
                        <Button
                          variant="ghost"
                          onClick={() => addArrayField('hostAliases')}
                          size="sm"
                          color="#60B4F7"
                          alignSelf="flex-start"
                        >
                          + Add Alias
                        </Button>
                      </VStack>
                    </Box>
                  </HStack>

                  {/* IP Addresses */}
                  <HStack spacing={4} align="start">
                    <Box minW="200px" pt={2}>
                      <Text fontSize="sm" color="gray.700" fontWeight="medium">IP addresses</Text>
                    </Box>
                    <Text color="gray.500" pt={2}>:</Text>
                    <Box flex={1}>
                      <VStack spacing={2} align="stretch">
                        {formData.ipAddresses.map((ip, index) => (
                          <HStack key={index} spacing={2}>
                            <Input
                              placeholder="IP address"
                              value={ip}
                              onChange={(e) => handleArrayInputChange('ipAddresses', index, e.target.value)}
                              bg="white"
                              border="1px solid"
                              borderColor="gray.300"
                              borderRadius="md"
                              _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                            />
                            {formData.ipAddresses.length > 1 && (
                              <Button
                                variant="ghost"
                                onClick={() => removeArrayField('ipAddresses', index)}
                                color="red.500"
                                size="sm"
                              >
                                ×
                              </Button>
                            )}
                          </HStack>
                        ))}
                        <Button
                          variant="ghost"
                          onClick={() => addArrayField('ipAddresses')}
                          size="sm"
                          color="#60B4F7"
                          alignSelf="flex-start"
                        >
                          + Add IP Address
                        </Button>
                      </VStack>
                    </Box>
                  </HStack>

                  {/* Resource Description */}
                  <HStack spacing={4} align="start">
                    <Box minW="200px" pt={2}>
                      <Text fontSize="sm" color="gray.700" fontWeight="medium">
                        Resource Description <Text as="span" color="red.500">*</Text>
                      </Text>
                    </Box>
                    <Text color="gray.500" pt={2}>:</Text>
                    <Box flex={1}>
                      <Textarea
                        placeholder="Brief description of the compute resource"
                        value={formData.resourceDescription}
                        onChange={(e) => handleInputChange('resourceDescription', e.target.value)}
                        bg="white"
                        border="1px solid"
                        borderColor="gray.300"
                        borderRadius="md"
                        _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                        rows={3}
                        required
                      />
                    </Box>
                  </HStack>

                  {/* Alternative SSH Hostname */}
                  <HStack spacing={4} align="start">
                    <Box minW="200px" pt={2}>
                      <Text fontSize="sm" color="gray.700" fontWeight="medium">
                        Alternative SSH Hostname
                      </Text>
                    </Box>
                    <Text color="gray.500" pt={2}>:</Text>
                    <Box flex={1}>
                      <Input
                        placeholder="Alternative hostname (optional)"
                        value={formData.alternativeSSHHostName}
                        onChange={(e) => handleInputChange('alternativeSSHHostName', e.target.value)}
                        bg="white"
                        border="1px solid"
                        borderColor="gray.300"
                        borderRadius="md"
                        _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                      />
                    </Box>
                  </HStack>

                  {/* SSH Port */}
                  <HStack spacing={4} align="start">
                    <Box minW="200px" pt={2}>
                      <Text fontSize="sm" color="gray.700" fontWeight="medium">
                        SSH Port <Text as="span" color="red.500">*</Text>
                      </Text>
                    </Box>
                    <Text color="gray.500" pt={2}>:</Text>
                    <Box flex={1}>
                      <Input
                        type="number"
                        placeholder="SSH port (default: 22)"
                        value={formData.sshPort}
                        onChange={(e) => handleInputChange('sshPort', parseInt(e.target.value) || 22)}
                        bg="white"
                        border="1px solid"
                        borderColor="gray.300"
                        borderRadius="md"
                        _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                        required
                      />
                    </Box>
                  </HStack>

                  {/* Security Protocol */}
                  <HStack spacing={4} align="start">
                    <Box minW="200px" pt={2}>
                      <Text fontSize="sm" color="gray.700" fontWeight="medium">
                        Security Protocol <Text as="span" color="red.500">*</Text>
                      </Text>
                    </Box>
                    <Text color="gray.500" pt={2}>:</Text>
                    <Box flex={1}>
                      <Box as="select" 
                        value={formData.securityProtocol}
                        onChange={(e: any) => handleInputChange('securityProtocol', e.target.value)}
                        bg="white"
                        border="1px solid"
                        borderColor="gray.300"
                        borderRadius="md"
                        p={2}
                        _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                        w="full"
                      >
                        <option value="SSH_KEYS">SSH Keys</option>
                        <option value="USERNAME_PASSWORD">Username/Password</option>
                      </Box>
                    </Box>
                  </HStack>

                  {/* Compute Type */}
                  <HStack spacing={4} align="start">
                    <Box minW="200px" pt={2}>
                      <Text fontSize="sm" color="gray.700" fontWeight="medium">
                        Compute Type <Text as="span" color="red.500">*</Text>
                      </Text>
                    </Box>
                    <Text color="gray.500" pt={2}>:</Text>
                    <Box flex={1}>
                      <Box as="select" 
                        value={formData.computeType}
                        onChange={(e: any) => handleInputChange('computeType', e.target.value)}
                        bg="white"
                        border="1px solid"
                        borderColor="gray.300"
                        borderRadius="md"
                        p={2}
                        _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                        w="full"
                      >
                        <option value="HPC">HPC</option>
                        <option value="Cloud">Cloud</option>
                        <option value="Local">Local</option>
                        <option value="Cluster">Cluster</option>
                      </Box>
                    </Box>
                  </HStack>

                  {/* CPU Cores */}
                  <HStack spacing={4} align="start">
                    <Box minW="200px" pt={2}>
                      <Text fontSize="sm" color="gray.700" fontWeight="medium">
                        CPU Cores <Text as="span" color="red.500">*</Text>
                      </Text>
                    </Box>
                    <Text color="gray.500" pt={2}>:</Text>
                    <Box flex={1}>
                      <Input
                        type="number"
                        placeholder="Number of CPU cores"
                        value={formData.cpuCores}
                        onChange={(e) => handleInputChange('cpuCores', parseInt(e.target.value) || 1)}
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

                  {/* Memory GB */}
                  <HStack spacing={4} align="start">
                    <Box minW="200px" pt={2}>
                      <Text fontSize="sm" color="gray.700" fontWeight="medium">
                        Memory (GB) <Text as="span" color="red.500">*</Text>
                      </Text>
                    </Box>
                    <Text color="gray.500" pt={2}>:</Text>
                    <Box flex={1}>
                      <Input
                        type="number"
                        placeholder="Memory in gigabytes"
                        value={formData.memoryGB}
                        onChange={(e) => handleInputChange('memoryGB', parseInt(e.target.value) || 1)}
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

                  {/* Operating System */}
                  <HStack spacing={4} align="start">
                    <Box minW="200px" pt={2}>
                      <Text fontSize="sm" color="gray.700" fontWeight="medium">
                        Operating System <Text as="span" color="red.500">*</Text>
                      </Text>
                    </Box>
                    <Text color="gray.500" pt={2}>:</Text>
                    <Box flex={1}>
                      <Box as="select" 
                        value={formData.operatingSystem}
                        onChange={(e: any) => handleInputChange('operatingSystem', e.target.value)}
                        bg="white"
                        border="1px solid"
                        borderColor="gray.300"
                        borderRadius="md"
                        p={2}
                        _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                        w="full"
                      >
                        <option value="Linux">Linux</option>
                        <option value="Windows">Windows</option>
                        <option value="macOS">macOS</option>
                        <option value="Unix">Unix</option>
                      </Box>
                    </Box>
                  </HStack>

                  {/* Queue System */}
                  <HStack spacing={4} align="start">
                    <Box minW="200px" pt={2}>
                      <Text fontSize="sm" color="gray.700" fontWeight="medium">
                        Queue System <Text as="span" color="red.500">*</Text>
                      </Text>
                    </Box>
                    <Text color="gray.500" pt={2}>:</Text>
                    <Box flex={1}>
                      <Box as="select" 
                        value={formData.queueSystem}
                        onChange={(e: any) => handleInputChange('queueSystem', e.target.value)}
                        bg="white"
                        border="1px solid"
                        borderColor="gray.300"
                        borderRadius="md"
                        p={2}
                        _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                        w="full"
                      >
                        <option value="SLURM">SLURM</option>
                        <option value="PBS">PBS</option>
                        <option value="SGE">SGE</option>
                        <option value="TORQUE">TORQUE</option>
                        <option value="LSF">LSF</option>
                      </Box>
                    </Box>
                  </HStack>

                  {/* Resource Job Manager Type */}
                  <HStack spacing={4} align="start">
                    <Box minW="200px" pt={2}>
                      <Text fontSize="sm" color="gray.700" fontWeight="medium">
                        Resource Job Manager Type <Text as="span" color="red.500">*</Text>
                      </Text>
                    </Box>
                    <Text color="gray.500" pt={2}>:</Text>
                    <Box flex={1}>
                      <Box as="select" 
                        value={formData.resourceJobManagerType}
                        onChange={(e: any) => handleInputChange('resourceJobManagerType', e.target.value)}
                        bg="white"
                        border="1px solid"
                        borderColor="gray.300"
                        borderRadius="md"
                        p={2}
                        _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                        w="full"
                      >
                        <option value="SLURM">SLURM</option>
                        <option value="PBS">PBS</option>
                        <option value="UGE">UGE</option>
                        <option value="LSF">LSF</option>
                        <option value="FORK">FORK</option>
                      </Box>
                    </Box>
                  </HStack>
                </VStack>
              )}

              {currentStep === 2 && (
                <Box>
                  {/* Auto Fill Section */}
                  <Box 
                    border="2px dashed"
                    borderColor="#60B4F7"
                    borderRadius="lg"
                    p={6}
                    mb={6}
                    bg={autoFill ? "blue.50" : "white"}
                  >
                    <HStack justify="space-between" mb={4}>
                      <Text color="gray.600" fontSize="sm">
                        Retrieve configuration details directly from the HPC system.
                      </Text>
                      <HStack spacing={2}>
                        <Text fontSize="sm" color="gray.700">Auto Fill</Text>
                        <input
                          type="checkbox"
                          checked={autoFill}
                          onChange={(e) => setAutoFill(e.target.checked)}
                          style={{ accentColor: "#60B4F7" }}
                        />
                      </HStack>
                    </HStack>

                    <VStack spacing={6} align="stretch">
                      {/* Resource Job Manager Type */}
                      <HStack spacing={4} align="start">
                        <Box minW="200px" pt={2}>
                          <Text fontSize="sm" color="gray.700" fontWeight="medium">Resource Job Manager Type</Text>
                        </Box>
                        <Text color="gray.500" pt={2}>:</Text>
                        <Box flex={1}>
                          <Text fontSize="sm" color="gray.600" pt={2}>
                            {formData.resourceJobManagerType}
                          </Text>
                        </Box>
                      </HStack>

                      {/* Data Movement Protocol */}
                      <HStack spacing={4} align="start">
                        <Box minW="200px" pt={2}>
                          <Text fontSize="sm" color="gray.700" fontWeight="medium">Data Movement Protocol</Text>
                        </Box>
                        <Text color="gray.500" pt={2}>:</Text>
                        <Box flex={1}>
                          <Text fontSize="sm" color="gray.600" pt={2}>
                            {formData.dataMovementProtocol}
                          </Text>
                        </Box>
                      </HStack>

                      {/* Add Queues */}
                      <HStack spacing={4} align="start">
                        <Box minW="200px" pt={2}>
                          <Text fontSize="sm" color="gray.700" fontWeight="medium">Add Queues</Text>
                        </Box>
                        <Text color="gray.500" pt={2}>:</Text>
                        <Box flex={1}>
                          <VStack spacing={3} align="stretch">
                            {/* Queue List */}
                            {queues.map((queue, index) => (
                              <HStack key={index} justify="space-between" p={3} bg="gray.50" borderRadius="md">
                                <VStack align="start" spacing={1}>
                                  <Text fontSize="sm" fontWeight="medium">{queue.queueName}</Text>
                                  <Text fontSize="xs" color="gray.600">{queue.queueDescription}</Text>
                                </VStack>
                                <Button
                                  variant="ghost"
                                  onClick={() => removeQueue(index)}
                                  color="red.500"
                                  size="sm"
                                >
                                  Remove
                                </Button>
                              </HStack>
                            ))}
                            
                            {/* Add Queue Button */}
                            <Button
                              variant="outline"
                              onClick={() => setShowQueueModal(true)}
                              bg="#60B4F7"
                              color="white"
                              size="sm"
                              alignSelf="flex-start"
                              _hover={{ bg: "#4A9BE7" }}
                              leftIcon={<Text>+</Text>}
                            >
                              Add a Queue
                            </Button>
                          </VStack>
                        </Box>
                      </HStack>
                    </VStack>
                  </Box>
                </Box>
              )}

              {/* Navigation Buttons */}
              <HStack justify="center" pt={6} spacing={4}>
                {currentStep === 1 && (
                  <Button
                    onClick={handleNext}
                    bg="black"
                    color="white"
                    size="lg"
                    px={8}
                    py={3}
                    borderRadius="md"
                    _hover={{ bg: "gray.800" }}
                    fontWeight="medium"
                  >
                    Verify & Create
                  </Button>
                )}
                
                {currentStep === 2 && (
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
                      : (isEditMode ? "Update Resource" : "Save")
                    }
                  </Button>
                )}
              </HStack>
            </VStack>
          </Box>
        </VStack>
      </Container>

      {/* Queue Modal */}
      <QueueModal
        isOpen={showQueueModal}
        onClose={() => setShowQueueModal(false)}
        onSave={addQueue}
      />
    </Box>
  );
};