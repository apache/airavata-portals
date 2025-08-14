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
  Badge,
} from "@chakra-ui/react";
import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { unifiedApiService } from "../../lib/apiConfig";
import { toaster } from "../ui/toaster";

interface StorageResource {
  storageResourceId: string;
  name: string;
  storage?: string;
  storageType: string;
  status?: string;
  isActive?: boolean;
  enabled?: boolean;
  description: string;
  storageResourceDescription?: string;
  capacityTB?: number;
  supportsEncryption?: boolean;
  supportsVersioning?: boolean;
  host?: string;
  hostName?: string;
  port?: number;
  accessCredentials?: string;
  createdAt?: string;
  updatedAt?: string;
  creationTime?: number;
  updateTime?: number;
}

interface ComputeResource {
  computeResourceId: string;
  name: string;
  compute?: string;
  computeType: string;
  status?: string;
  isActive?: boolean;
  enabled?: boolean;
  description: string;
  resourceDescription?: string;
  cpuCores?: number;
  memoryGB?: number;
  gpuCores?: number;
  host?: string;
  hostName?: string;
  port?: number;
  accessCredentials?: string;
  createdAt?: string;
  updatedAt?: string;
  creationTime?: number;
  updateTime?: number;
}

export const ResourceDetail = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const cancelRef = useRef<HTMLButtonElement>(null);
  
  const [resource, setResource] = useState<StorageResource | ComputeResource | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
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
        const data = await unifiedApiService.getStorageResourceById(id);
        setResource(data);
      } else if (type === "compute" && id) {
        const data = await unifiedApiService.getComputeResourceById(id);
        setResource(data);
      } else {
        setError("Invalid resource type or ID");
      }
    } catch (err: any) {
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

  const handleEdit = () => {
    navigate(`/resources/${type}/${id}/edit`);
  };

  const handleDelete = async () => {
    console.log("🗑️ Delete button clicked!", { type, id, resource: resource?.name });
    
    try {
      setDeleting(true);
      
      if (type === "storage" && id) {
        console.log("🔄 Calling deleteStorageResource with ID:", id);
        const result = await unifiedApiService.deleteStorageResource(id);
        console.log("✅ Storage resource deleted successfully:", result);
        toaster.create({
          title: "Storage resource deleted",
          description: "The storage resource has been successfully deleted.",
          type: "success",
        });
      } else if (type === "compute" && id) {
        console.log("🔄 Calling deleteComputeResource with ID:", id);
        const result = await unifiedApiService.deleteComputeResource(id);
        console.log("✅ Compute resource deleted successfully:", result);
        toaster.create({
          title: "Compute resource deleted", 
          description: "The compute resource has been successfully deleted.",
          type: "success",
        });
      } else {
        console.error("❌ Invalid type or ID for deletion:", { type, id });
        throw new Error(`Invalid type (${type}) or ID (${id}) for deletion`);
      }
      
      console.log("🚀 Navigating back to resources with tab:", type);
      navigate(`/resources?tab=${type}`);
    } catch (err: any) {
      console.error("❌ Failed to delete resource:", err);
      console.error("Error details:", {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status,
        config: err.config
      });
      toaster.create({
        title: "Delete failed",
        description: `Failed to delete resource: ${err.response?.data || err.message}`,
        type: "error",
      });
    } finally {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const getStatusColor = (resource: any) => {
    // Handle both old status string format and new enabled/isActive boolean format
    if (typeof resource.status === 'string') {
      switch (resource.status.toLowerCase()) {
        case "active":
          return "green";
        case "full":
          return "red";
        case "archived":
          return "yellow";
        default:
          return "gray";
      }
    } else if (typeof resource.isActive === 'boolean') {
      return resource.isActive ? "green" : "gray";
    } else if (typeof resource.enabled === 'boolean') {
      return resource.enabled ? "green" : "gray";
    }
    return "gray";
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
            <Button onClick={() => navigate(`/resources?tab=${type || 'compute'}`)}>
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
                onClick={() => navigate(`/resources?tab=${type}`)}
                color="gray.600"
              >
                ← Back to {type === 'compute' ? 'Compute' : 'Storage'} Resources
              </Button>
              <Heading size="lg" color="gray.800">
                {resource.name}
              </Heading>
              <HStack>
                <Text color="gray.600" textTransform="capitalize">
                  {type} Resource
                </Text>
                <Badge
                  px={3}
                  py={1}
                  borderRadius="full"
                  fontSize="sm"
                  fontWeight="medium"
                  colorScheme={getStatusColor(resource)}
                >
                  {typeof resource.status === 'string' ? resource.status : 
                   (resource.isActive !== undefined ? (resource.isActive ? 'Active' : 'Inactive') :
                    (resource.enabled !== undefined ? (resource.enabled ? 'Active' : 'Inactive') : 'Unknown'))}
                </Badge>
              </HStack>
            </VStack>
            
            {/* Action Buttons */}
            <HStack spacing={3}>
              <Button
                colorScheme="blue"
                onClick={handleEdit}
              >
                Edit
              </Button>
              <Button
                colorScheme="red"
                variant="outline"
                onClick={() => {
                  console.log("🔴 Delete button clicked");
                  setShowDeleteConfirm(true);
                }}
              >
                Delete
              </Button>
            </HStack>
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
                  
                  <HStack justify="space-between">
                    <Text fontWeight="medium" color="gray.600">ID:</Text>
                    <Text fontSize="sm" fontFamily="mono" color="gray.500">
                      {type === "storage" ? (resource as StorageResource).storageResourceId : (resource as ComputeResource).computeResourceId}
                    </Text>
                  </HStack>
                  
                  {type === "storage" ? (
                    <>
                      <HStack justify="space-between">
                        <Text fontWeight="medium" color="gray.600">Storage Type:</Text>
                        <Text>{(resource as StorageResource).storageType}</Text>
                      </HStack>
                      {(resource as StorageResource).capacityTB && (
                        <HStack justify="space-between">
                          <Text fontWeight="medium" color="gray.600">Capacity:</Text>
                          <Text>{(resource as StorageResource).capacityTB} TB</Text>
                        </HStack>
                      )}
                      {(resource as StorageResource).supportsEncryption !== undefined && (
                        <HStack justify="space-between">
                          <Text fontWeight="medium" color="gray.600">Supports Encryption:</Text>
                          <Badge colorScheme={(resource as StorageResource).supportsEncryption ? "green" : "gray"}>
                            {(resource as StorageResource).supportsEncryption ? "Yes" : "No"}
                          </Badge>
                        </HStack>
                      )}
                      {(resource as StorageResource).supportsVersioning !== undefined && (
                        <HStack justify="space-between">
                          <Text fontWeight="medium" color="gray.600">Supports Versioning:</Text>
                          <Badge colorScheme={(resource as StorageResource).supportsVersioning ? "green" : "gray"}>
                            {(resource as StorageResource).supportsVersioning ? "Yes" : "No"}
                          </Badge>
                        </HStack>
                      )}
                    </>
                  ) : (
                    <>
                      <HStack justify="space-between">
                        <Text fontWeight="medium" color="gray.600">Compute Type:</Text>
                        <Text>{(resource as ComputeResource).computeType}</Text>
                      </HStack>
                      {(resource as ComputeResource).cpuCores && (
                        <HStack justify="space-between">
                          <Text fontWeight="medium" color="gray.600">CPU Cores:</Text>
                          <Text>{(resource as ComputeResource).cpuCores}</Text>
                        </HStack>
                      )}
                      {(resource as ComputeResource).memoryGB && (
                        <HStack justify="space-between">
                          <Text fontWeight="medium" color="gray.600">Memory:</Text>
                          <Text>{(resource as ComputeResource).memoryGB} GB</Text>
                        </HStack>
                      )}
                      {(resource as ComputeResource).gpuCores && (
                        <HStack justify="space-between">
                          <Text fontWeight="medium" color="gray.600">GPU Cores:</Text>
                          <Text>{(resource as ComputeResource).gpuCores}</Text>
                        </HStack>
                      )}
                    </>
                  )}
                  
                  {((resource as any).host || (resource as any).hostName || (resource as any).port) && (
                    <>
                      {((resource as any).host || (resource as any).hostName) && (
                        <HStack justify="space-between">
                          <Text fontWeight="medium" color="gray.600">Host:</Text>
                          <Text fontFamily="mono" fontSize="sm">{(resource as any).host || (resource as any).hostName}</Text>
                        </HStack>
                      )}
                      {(resource as any).port && (
                        <HStack justify="space-between">
                          <Text fontWeight="medium" color="gray.600">Port:</Text>
                          <Text>{(resource as any).port}</Text>
                        </HStack>
                      )}
                    </>
                  )}
                  
                  <HStack justify="space-between">
                    <Text fontWeight="medium" color="gray.600">Status:</Text>
                    <Badge
                      px={2}
                      py={1}
                      borderRadius="full"
                      fontSize="xs"
                      fontWeight="medium"
                      colorScheme={getStatusColor(resource)}
                    >
                      {typeof resource.status === 'string' ? resource.status : 
                       (resource.isActive !== undefined ? (resource.isActive ? 'Active' : 'Inactive') :
                        (resource.enabled !== undefined ? (resource.enabled ? 'Active' : 'Inactive') : 'Unknown'))}
                    </Badge>
                  </HStack>
                  
                  {((resource as any).createdAt || (resource as any).creationTime) && (
                    <HStack justify="space-between">
                      <Text fontWeight="medium" color="gray.600">Created:</Text>
                      <Text fontSize="sm" color="gray.500">
                        {new Date((resource as any).createdAt || (resource as any).creationTime).toLocaleDateString()}
                      </Text>
                    </HStack>
                  )}
                </VStack>
              </Box>

              <Box>
                <Text fontSize="lg" fontWeight="bold" color="gray.800" mb={3}>
                  Description
                </Text>
                <Text color="gray.600" lineHeight="1.6">
                  {resource.description || 
                   (type === "storage" ? (resource as StorageResource).storageResourceDescription : 
                    (resource as ComputeResource).resourceDescription) || 
                   "No description available"}
                </Text>
              </Box>

              <Box>
                <Text fontSize="lg" fontWeight="bold" color="gray.800" mb={3}>
                  Quick Actions
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
                    Test Connection
                  </Button>
                  <Button
                    variant="outline"
                    borderColor="gray.300"
                  >
                    Monitor
                  </Button>
                  <Button
                    colorScheme="blue"
                    onClick={handleEdit}
                  >
                    Edit Resource
                  </Button>
                </HStack>
              </Box>
            </VStack>
          </Box>
        </VStack>
      </Container>
      
      {/* Delete Confirmation */}
      {showDeleteConfirm && (
        <Box
          position="fixed"
          top="0"
          left="0"
          right="0"
          bottom="0"
          bg="blackAlpha.600"
          display="flex"
          alignItems="center"
          justifyContent="center"
          zIndex="9999"
        >
          <Box
            bg="white"
            borderRadius="lg"
            p={6}
            maxW="400px"
            w="90%"
            boxShadow="xl"
          >
            <Heading size="md" mb={4}>Delete {type} Resource</Heading>
            <Text mb={6}>
              Are you sure you want to delete "{resource?.name}"? This action cannot be undone.
            </Text>
            <HStack spacing={3} justify="flex-end">
              <Button 
                onClick={() => {
                  console.log("🔵 Cancel clicked!");
                  setShowDeleteConfirm(false);
                }}
              >
                Cancel
              </Button>
              <Button
                colorScheme="red"
                onClick={() => {
                  console.log("🟥 Delete confirmed!");
                  handleDelete();
                }}
                isLoading={deleting}
                loadingText="Deleting..."
              >
                Delete
              </Button>
            </HStack>
          </Box>
        </Box>
      )}
    </Box>
  );
};