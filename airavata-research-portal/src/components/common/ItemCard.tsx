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
  Text,
  VStack,
  HStack,
  Button,
  Flex,
  Spacer,
} from "@chakra-ui/react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "react-oidc-context";
import { useState, useEffect } from "react";
import { toaster } from "@/components/ui/toaster";

interface ItemCardProps {
  id: number | string;
  title: string;
  description: string;
  tags: string[];
  authors: string[];
  starCount: number;
  onStar?: (id: number | string) => void;
  resourceType?: string;
}

export const ItemCard = ({ 
  id, 
  title, 
  description, 
  tags, 
  authors, 
  starCount, 
  onStar,
  resourceType 
}: ItemCardProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const auth = useAuth();
  const [isStarred, setIsStarred] = useState(false);
  const [starLoading, setStarLoading] = useState(false);

  const getResourceTypeAndEndpoint = () => {
    if (location.pathname.includes('/datasets')) {
      return { type: 'DATASET', endpoint: 'datasets', apiVersion: 'v1' };
    } else if (location.pathname.includes('/models')) {
      return { type: 'MODEL', endpoint: 'models', apiVersion: 'v1' };
    } else if (location.pathname.includes('/notebooks')) {
      return { type: 'NOTEBOOK', endpoint: 'notebooks', apiVersion: 'v1' };
    } else if (location.pathname.includes('/repositories')) {
      return { type: 'REPOSITORY', endpoint: 'repositories', apiVersion: 'v1' };
    } else if (location.pathname.includes('/codes')) {
      return { type: 'CODE', endpoint: 'codes', apiVersion: 'v2' };
    }
    return { type: 'MODEL', endpoint: 'models', apiVersion: 'v1' };
  };

  useEffect(() => {
    if (!auth.user?.profile.email) return;
    
    const checkStarStatus = async () => {
      try {
        const { endpoint, apiVersion } = getResourceTypeAndEndpoint();
        
        // Skip star status check for v1 API due to authentication requirements
        if (apiVersion === 'v1') {
          setIsStarred(false);
          return;
        }
        
        const url = `http://localhost:8080/api/v2/rf/${endpoint}/${id}/star`;
        const response = await fetch(url);
        const starred = await response.json();
        setIsStarred(starred);
      } catch (error) {
        console.error('Error checking star status:', error);
      }
    };

    checkStarStatus();
  }, [id, location.pathname, auth.user?.profile.email]);

  const handleCardClick = () => {
    // Use resourceType prop if available (for catalog page), otherwise fall back to path-based detection
    if (resourceType) {
      const type = resourceType.toLowerCase();
      const navigateOptions = location.pathname.includes('/catalog') ? { state: { from: '/catalog' } } : undefined;
      
      if (type === 'dataset') {
        navigate(`/resources/datasets/${id}`, navigateOptions);
      } else if (type === 'model') {
        navigate(`/resources/models/${id}`, navigateOptions);
      } else if (type === 'notebook') {
        navigate(`/resources/notebooks/${id}`, navigateOptions);
      } else if (type === 'repository') {
        navigate(`/resources/repositories/${id}`, navigateOptions);
      }
      return;
    }
    
    // Fallback: Determine the route based on current path
    if (location.pathname.includes('/datasets')) {
      navigate(`/resources/datasets/${id}`);
    } else if (location.pathname.includes('/models')) {
      navigate(`/resources/models/${id}`);
    } else if (location.pathname.includes('/notebooks')) {
      navigate(`/resources/notebooks/${id}`);
    } else if (location.pathname.includes('/repositories')) {
      navigate(`/resources/repositories/${id}`);
    } else if (location.pathname.includes('/codes')) {
      navigate(`/codes/${id}`);
    }
  };

  const handleStarClick = async (e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!auth.user?.profile.email) {
      toaster.create({
        title: "Please log in to star resources",
        type: "error",
      });
      return;
    }

    const { apiVersion } = getResourceTypeAndEndpoint();
    
    // Disable star functionality for v1 API (datasets) due to authentication requirements
    if (apiVersion === 'v1') {
      toaster.create({
        title: "Star functionality unavailable",
        description: "Star functionality requires full authentication for this resource type",
        type: "warning",
      });
      return;
    }

    try {
      setStarLoading(true);
      const { endpoint } = getResourceTypeAndEndpoint();
      const url = `http://localhost:8080/api/v2/rf/${endpoint}/${id}/star`;
      const requestOptions = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      };
      
      const response = await fetch(url, requestOptions);
      const newStarredState = await response.json();
      setIsStarred(newStarredState);
      
      toaster.create({
        title: newStarredState ? "Starred" : "Unstarred",
        description: title,
        type: "success",
      });

      if (onStar) {
        onStar(id);
      }
    } catch (error) {
      console.error('Error starring resource:', error);
      toaster.create({
        title: "Error updating star status",
        type: "error",
      });
    } finally {
      setStarLoading(false);
    }
  };

  return (
    <Box
      border="1px solid"
      borderColor="gray.200"
      borderRadius="xl"
      p={4}
      bg="white"
      _hover={{ borderColor: "gray.300", shadow: "md", cursor: "pointer" }}
      h="240px"
      display="flex"
      flexDirection="column"
      m={3}
      onClick={handleCardClick}
    >
      <VStack align="stretch" spacing={3} flex={1}>
        {/* Header with title and star */}
        <Flex align="start" justify="space-between">
          <Text fontSize="lg" fontWeight="bold" color="gray.800" lineHeight="1.3" flex={1} pr={2}>
            {title}
          </Text>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleStarClick}
            color={isStarred ? "yellow.500" : "gray.400"}
            _hover={{ color: "yellow.500" }}
            minW="auto"
            h="auto"
            p={1}
            disabled={starLoading}
          >
            {isStarred ? "★" : "☆"}
          </Button>
        </Flex>

        {/* Description */}
        <Text 
          color="gray.600" 
          fontSize="sm" 
          lineHeight="1.4"
          overflow="hidden"
          textOverflow="ellipsis"
          noOfLines={3}
          mb={2}
        >
          {description}
        </Text>

        {/* Tags */}
        <Box mb={2}>
          <HStack spacing={1} flexWrap="wrap">
            {tags.slice(0, 4).map((tag, index) => (
              <Box
                key={index}
                bg="#60b4f7"
                color="white"
                px={2}
                py={1}
                borderRadius="full"
                fontSize="xs"
                fontWeight="medium"
              >
                {tag}
              </Box>
            ))}
            {tags.length > 4 && (
              <Text fontSize="xs" color="gray.500">+{tags.length - 4} more</Text>
            )}
          </HStack>
        </Box>

        <Spacer />

        {/* Authors - Fixed at bottom */}
        <Box mt="auto" pt={2}>
          <Text fontSize="xs" color="gray.500" mb={1} fontWeight="medium">Authors -</Text>
          <Text 
            fontSize="xs" 
            color="gray.600" 
            lineHeight="1.2"
            overflow="hidden"
            textOverflow="ellipsis"
            noOfLines={1}
          >
            {authors.join(", ")}
          </Text>
        </Box>
      </VStack>
    </Box>
  );
};