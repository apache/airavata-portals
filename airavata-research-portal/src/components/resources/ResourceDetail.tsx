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
  Heading,
  Flex,
  Spinner,
} from "@chakra-ui/react";
import { useEffect, useState } from "react";
import { useParams, useNavigate, useLocation } from "react-router";
import { adminApiService } from "../../lib/adminApi";

interface StorageResource {
  id: number;
  name: string;
  storage: string;
  storageType: string;
  status: string;
  description: string;
}

interface ComputeResource {
  id: number;
  name: string;
  compute: string;
  computeType: string;
  status: string;
  description: string;
}

export const ResourceDetail = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const [resource, setResource] = useState<StorageResource | ComputeResource | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Extract type from URL path
  const type = location.pathname.includes('/storage/') ? 'storage' : 'compute';


  useEffect(() => {
    fetchResource();
  }, [type, id]);

  const fetchResource = async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (type === "storage" && id) {
        const data = await adminApiService.getStorageResourceById(parseInt(id));
        setResource(data);
      } else if (type === "compute" && id) {
        const data = await adminApiService.getComputeResourceById(parseInt(id));
        setResource(data);
      } else {
        setError("Invalid resource type or ID");
      }
    } catch (err) {
      console.error("Failed to fetch resource:", err);
      console.error("Error details:", {
        type,
        id,
        error: err.response?.data,
        status: err.response?.status,
        message: err.message
      });
      setError(`Failed to load resource details. Error: ${err.response?.status || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "active":
        return "green";
      case "full":
        return "red";
      case "archived":
        return "yellow";
      default:
        return "gray";
    }
  };

  if (loading) {
    return (
      <Box bg="gray.50" minH="100vh" display="flex" alignItems="center" justifyContent="center">
        <Spinner size="xl" />
      </Box>
    );
  }

  if (error || !resource) {
    return (
      <Box bg="gray.50" minH="100vh">
        <Container maxW="1200px" py={10}>
          <VStack spacing={4}>
            <Text color="red.500" fontSize="lg">{error || "Resource not found"}</Text>
            <Button onClick={() => navigate("/resources")}>
              Back to Resources
            </Button>
          </VStack>
        </Container>
      </Box>
    );
  }

  return (
    <Box bg="gray.50" minH="100vh">
      <Container maxW="1200px" py={10}>
        <VStack spacing={8} align="stretch">
          {/* Header */}
          <Flex justify="space-between" align="center">
            <VStack align="start" spacing={2}>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/resources")}
                color="gray.600"
              >
                ← Back to Resources
              </Button>
              <Heading size="lg" color="gray.800">
                {resource.name}
              </Heading>
              <HStack>
                <Text color="gray.600" textTransform="capitalize">
                  {type} Resource
                </Text>
                <Box
                  px={3}
                  py={1}
                  borderRadius="full"
                  fontSize="sm"
                  fontWeight="medium"
                  color="white"
                  bg={`${getStatusColor(resource.status)}.500`}
                >
                  {resource.status}
                </Box>
              </HStack>
            </VStack>
          </Flex>

          {/* Details Card */}
          <Box 
            bg="white" 
            borderRadius="lg" 
            p={6} 
            border="1px solid" 
            borderColor="gray.200"
            shadow="sm"
          >
            <VStack spacing={6} align="stretch">
              <Box>
                <Text fontSize="lg" fontWeight="bold" color="gray.800" mb={4}>
                  Resource Details
                </Text>
                <VStack spacing={4} align="stretch">
                  <HStack justify="space-between">
                    <Text fontWeight="medium" color="gray.600">Name:</Text>
                    <Text>{resource.name}</Text>
                  </HStack>
                  
                  {(resource as any).storage ? (
                    <>
                      <HStack justify="space-between">
                        <Text fontWeight="medium" color="gray.600">Storage:</Text>
                        <Text>{(resource as StorageResource).storage}</Text>
                      </HStack>
                      <HStack justify="space-between">
                        <Text fontWeight="medium" color="gray.600">Storage Type:</Text>
                        <Text>{(resource as StorageResource).storageType}</Text>
                      </HStack>
                    </>
                  ) : (
                    <>
                      <HStack justify="space-between">
                        <Text fontWeight="medium" color="gray.600">Compute:</Text>
                        <Text>{(resource as ComputeResource).compute}</Text>
                      </HStack>
                      <HStack justify="space-between">
                        <Text fontWeight="medium" color="gray.600">Compute Type:</Text>
                        <Text>{(resource as ComputeResource).computeType}</Text>
                      </HStack>
                    </>
                  )}
                  
                  <HStack justify="space-between">
                    <Text fontWeight="medium" color="gray.600">Status:</Text>
                    <Box
                      px={2}
                      py={1}
                      borderRadius="full"
                      fontSize="xs"
                      fontWeight="medium"
                      color="white"
                      bg={`${getStatusColor(resource.status)}.500`}
                    >
                      {resource.status}
                    </Box>
                  </HStack>
                </VStack>
              </Box>

              <Box>
                <Text fontSize="lg" fontWeight="bold" color="gray.800" mb={3}>
                  Description
                </Text>
                <Text color="gray.600" lineHeight="1.6">
                  {resource.description}
                </Text>
              </Box>

              <Box>
                <Text fontSize="lg" fontWeight="bold" color="gray.800" mb={3}>
                  Actions
                </Text>
                <HStack spacing={3}>
                  <Button
                    bg="#60b4f7"
                    color="white"
                    _hover={{ bg: "#4a9ce6" }}
                  >
                    Connect
                  </Button>
                  <Button
                    variant="outline"
                    borderColor="gray.300"
                  >
                    Configure
                  </Button>
                  <Button
                    variant="outline"
                    borderColor="gray.300"
                  >
                    Monitor
                  </Button>
                </HStack>
              </Box>
            </VStack>
          </Box>
        </VStack>
      </Container>
    </Box>
  );
};