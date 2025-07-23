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

interface QueueConfig {
  queueName: string;
  queueDescription: string;
  queueMaxRunTime: string;
  queueMaxNodes: string;
  queueMaxProcessors: string;
  queueMaxJobsInQueue: string;
  queueMaxMemory: string;
}

export const AddComputeResourceForm: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [autoFill, setAutoFill] = useState(true);
  
  const [formData, setFormData] = useState({
    hostName: '',
    hostAddress: '',
    description: '',
    sshUsername: '',
    sshPort: '22',
    workingDirectory: '',
    ipAddresses: '',
    resourceDescription: '',
    sshKey: '',
    authMethod: 'SSH Key'
  });

  const [step2Data, setStep2Data] = useState({
    schedulerType: 'SLURM',
    dataMovementProtocol: 'SCP',
    selectedQueues: ['GPU queue', 'Compute queue', 'Debug queue', 'GPU shared queue']
  });

  const [queueConfig, setQueueConfig] = useState<QueueConfig>({
    queueName: '',
    queueDescription: '',
    queueMaxRunTime: '',
    queueMaxNodes: '',
    queueMaxProcessors: '',
    queueMaxJobsInQueue: '',
    queueMaxMemory: '',
  });

  const availableQueues = [
    'GPU queue',
    'Compute queue', 
    'Debug queue',
    'GPU shared queue'
  ];

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleStep2Change = (field: string, value: string | string[]) => {
    setStep2Data(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleQueueToggle = (queue: string) => {
    setStep2Data(prev => ({
      ...prev,
      selectedQueues: prev.selectedQueues.includes(queue)
        ? prev.selectedQueues.filter(q => q !== queue)
        : [...prev.selectedQueues, queue]
    }));
  };

  const handleNext = () => {
    if (currentStep === 1) {
      setCurrentStep(2);
    }
  };

  const handleBack = () => {
    if (currentStep === 2) {
      setCurrentStep(1);
    } else {
      navigate('/resources?tab=compute');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const newComputeResource = {
        name: formData.hostName,
        compute: formData.hostAddress,
        computeType: 'SSH',
        status: 'ACTIVE',
        description: formData.resourceDescription || formData.description,
        schedulerType: step2Data.schedulerType,
        dataMovementProtocol: step2Data.dataMovementProtocol,
        queues: step2Data.selectedQueues
      };

      console.log('Submitting compute resource:', newComputeResource);
      const createdResource = await adminApiService.createComputeResource(newComputeResource);
      console.log('Compute resource created successfully:', createdResource);
      
      navigate('/resources?tab=compute');
    } catch (error) {
      console.error('Failed to create compute resource:', error);
      alert('Failed to create compute resource. Please try again.');
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
              onClick={handleBack}
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
              Add <Text as="span" color="#60B4F7">Compute Resource</Text>
            </Text>
            
            {/* Step Indicators */}
            <HStack spacing={4}>
              <Box
                bg={currentStep === 1 ? "black" : "gray.200"}
                color={currentStep === 1 ? "white" : "gray.600"}
                px={3}
                py={1}
                borderRadius="full"
                fontSize="sm"
                fontWeight="medium"
                cursor="pointer"
                onClick={() => setCurrentStep(1)}
              >
                {currentStep > 1 ? "1" : "Step 1"}
              </Box>
              <Box
                bg={currentStep === 2 ? "black" : "gray.200"}
                color={currentStep === 2 ? "white" : "gray.600"}
                px={3}
                py={1}
                borderRadius="full"
                fontSize="sm"
                fontWeight="medium"
              >
                {currentStep === 2 ? "Step 2" : "2"}
              </Box>
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
              {/* Form Fields */}
              {currentStep === 1 && (
              <VStack spacing={6} align="stretch">
                {/* Host Name */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Host Name <Text as="span" color="red.500">*</Text>
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      placeholder=""
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
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Host Aliases
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      placeholder=""
                      value={formData.hostAddress}
                      onChange={(e) => handleInputChange('hostAddress', e.target.value)}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                    />
                  </Box>
                </HStack>

                {/* IP addresses */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      IP addresses
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      placeholder=""
                      value={formData.ipAddresses}
                      onChange={(e) => handleInputChange('ipAddresses', e.target.value)}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                    />
                  </Box>
                </HStack>

                {/* Resource description */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Resource description
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      placeholder=""
                      value={formData.resourceDescription}
                      onChange={(e) => handleInputChange('resourceDescription', e.target.value)}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                    />
                  </Box>
                </HStack>

                {/* SSH Username */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      SSH Username
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      placeholder=""
                      value={formData.sshUsername}
                      onChange={(e) => handleInputChange('sshUsername', e.target.value)}
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
                      SSH Port
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      placeholder=""
                      value={formData.sshPort}
                      onChange={(e) => handleInputChange('sshPort', e.target.value)}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                    />
                  </Box>
                </HStack>

                {/* Authentication Method */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Authentication Method <Text as="span" color="red.500">*</Text>
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <HStack spacing={4}>
                      <Box as="select" 
                        value={formData.authMethod}
                        onChange={(e: any) => handleInputChange('authMethod', e.target.value)}
                        bg="white"
                        border="1px solid"
                        borderColor="gray.300"
                        borderRadius="md"
                        p={2}
                        _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                        minW="120px"
                      >
                        <option value="SSH Key">SSH Key</option>
                      </Box>
                      <Input
                        placeholder="Enter your SSH key"
                        value={formData.sshKey}
                        onChange={(e) => handleInputChange('sshKey', e.target.value)}
                        bg="white"
                        border="1px solid"
                        borderColor="gray.300"
                        borderRadius="md"
                        _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                        flex={1}
                      />
                    </HStack>
                  </Box>
                </HStack>

                {/* Working Directory */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Working Directory <Text as="span" color="red.500">*</Text>
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Input
                      placeholder=""
                      value={formData.workingDirectory}
                      onChange={(e) => handleInputChange('workingDirectory', e.target.value)}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                      required
                    />
                  </Box>
                </HStack>
              </VStack>
              )}

              {/* Step 2 - Queue Configuration */}
              {currentStep === 2 && (
              <VStack spacing={6} align="stretch">
                {/* Auto Fill Toggle */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.600">
                      Retrieve configuration details directly from the HPC system.
                    </Text>
                  </Box>
                  <HStack spacing={2} align="center">
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">Auto Fill</Text>
                    <Box
                      as="input"
                      type="checkbox"
                      checked={autoFill}
                      onChange={(e: any) => setAutoFill(e.target.checked)}
                      w="16px"
                      h="16px"
                      bg={autoFill ? "#60B4F7" : "white"}
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="sm"
                      _focus={{ borderColor: "#60B4F7" }}
                    />
                  </HStack>
                </HStack>

                {/* Scheduler Type */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Scheduler Type
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Box as="select" 
                      value={step2Data.schedulerType}
                      onChange={(e: any) => handleStep2Change('schedulerType', e.target.value)}
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
                    </Box>
                  </Box>
                </HStack>

                {/* Data Movement Protocol */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Data Movement Protocol
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <Box flex={1}>
                    <Box as="select" 
                      value={step2Data.dataMovementProtocol}
                      onChange={(e: any) => handleStep2Change('dataMovementProtocol', e.target.value)}
                      bg="white"
                      border="1px solid"
                      borderColor="gray.300"
                      borderRadius="md"
                      p={2}
                      _focus={{ borderColor: "#60B4F7", boxShadow: "0 0 0 1px #60B4F7" }}
                      w="full"
                    >
                      <option value="SCP">SCP</option>
                      <option value="SFTP">SFTP</option>
                      <option value="RSYNC">RSYNC</option>
                    </Box>
                  </Box>
                </HStack>

                {/* Add Queues */}
                <HStack spacing={4} align="start">
                  <Box minW="200px" pt={2}>
                    <Text fontSize="sm" color="gray.700" fontWeight="medium">
                      Add Queues
                    </Text>
                  </Box>
                  <Text color="gray.500" pt={2}>:</Text>
                  <VStack flex={1} align="stretch" spacing={3}>
                    {/* Deselect All */}
                    <HStack spacing={2} align="center">
                      <Box
                        as="input"
                        type="checkbox"
                        checked={step2Data.selectedQueues.length === availableQueues.length}
                        onChange={(e: any) => {
                          if (e.target.checked) {
                            handleStep2Change('selectedQueues', availableQueues);
                          } else {
                            handleStep2Change('selectedQueues', []);
                          }
                        }}
                        w="16px"
                        h="16px"
                        bg={step2Data.selectedQueues.length === availableQueues.length ? "#60B4F7" : "white"}
                        border="1px solid"
                        borderColor="gray.300"
                        borderRadius="sm"
                        _focus={{ borderColor: "#60B4F7" }}
                      />
                      <Text fontSize="sm" color="gray.700" fontWeight="medium">
                        Deselect All
                      </Text>
                    </HStack>

                    {/* Individual Queues */}
                    {availableQueues.map((queue) => (
                      <HStack key={queue} spacing={2} align="center">
                        <Box
                          as="input"
                          type="checkbox"
                          checked={step2Data.selectedQueues.includes(queue)}
                          onChange={() => handleQueueToggle(queue)}
                          w="16px"
                          h="16px"
                          bg={step2Data.selectedQueues.includes(queue) ? "#60B4F7" : "white"}
                          border="1px solid"
                          borderColor="gray.300"
                          borderRadius="sm"
                          _focus={{ borderColor: "#60B4F7" }}
                        />
                        <Text fontSize="sm" color="gray.700" flex={1}>
                          {queue}
                        </Text>
                        <Box as="select" 
                          bg="white"
                          border="1px solid"
                          borderColor="gray.300"
                          borderRadius="md"
                          p={1}
                          fontSize="sm"
                          _focus={{ borderColor: "#60B4F7" }}
                          w="100px"
                        >
                          <option>Configure</option>
                        </Box>
                      </HStack>
                    ))}
                  </VStack>
                </HStack>
              </VStack>
              )}

              {/* Submit Button */}
              <HStack justify="center" pt={6} spacing={4}>
                {currentStep === 1 ? (
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
                    Next
                  </Button>
                ) : (
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
                    {loading ? "Saving..." : "Save"}
                  </Button>
                )}
              </HStack>
            </VStack>
          </Box>
        </VStack>
      </Container>
    </Box>
  );
};