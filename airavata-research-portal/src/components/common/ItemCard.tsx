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
import { useNavigate, useLocation } from "react-router";
import { useAuth } from "react-oidc-context";
import { useState, useEffect } from "react";
import { toaster } from "@/components/ui/toaster";

interface ItemCardProps {
  id: number;
  title: string;
  description: string;
  tags: string[];
  authors: string[];
  starCount: number;
  onStar?: (id: number) => void;
}

export const ItemCard = ({ 
  id, 
  title, 
  description, 
  tags, 
  authors, 
  starCount, 
  onStar 
}: ItemCardProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const auth = useAuth();
  const [isStarred, setIsStarred] = useState(false);
  const [starLoading, setStarLoading] = useState(false);

  const getResourceTypeAndEndpoint = () => {
    if (location.pathname.includes('/datasets')) {
      return { type: 'DATASET', endpoint: 'datasets' };
    } else if (location.pathname.includes('/models')) {
      return { type: 'MODEL', endpoint: 'models' };
    } else if (location.pathname.includes('/notebooks')) {
      return { type: 'NOTEBOOK', endpoint: 'notebooks' };
    } else if (location.pathname.includes('/repositories')) {
      return { type: 'REPOSITORY', endpoint: 'repositories' };
    }
    return { type: 'MODEL', endpoint: 'models' };
  };

  useEffect(() => {
    if (!auth.user?.profile.email) return;
    
    const checkStarStatus = async () => {
      try {
        const { endpoint } = getResourceTypeAndEndpoint();
        const response = await fetch(`http://localhost:8080/api/${endpoint}/${id}/star?userEmail=${encodeURIComponent(auth.user?.profile.email || '')}`);
        const starred = await response.json();
        setIsStarred(starred);
      } catch (error) {
        console.error('Error checking star status:', error);
      }
    };

    checkStarStatus();
  }, [id, location.pathname, auth.user?.profile.email]);

  const handleCardClick = () => {
    // Determine the route based on current path
    if (location.pathname.includes('/datasets')) {
      navigate(`/resources/datasets/${id}`);
    } else if (location.pathname.includes('/models')) {
      navigate(`/resources/models/${id}`);
    } else if (location.pathname.includes('/notebooks')) {
      navigate(`/resources/notebooks/${id}`);
    } else if (location.pathname.includes('/repositories')) {
      navigate(`/resources/repositories/${id}`);
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

    try {
      setStarLoading(true);
      const { endpoint } = getResourceTypeAndEndpoint();
      const response = await fetch(`http://localhost:8080/api/${endpoint}/${id}/star`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          userEmail: auth.user.profile.email,
          userName: auth.user.profile.name || 'User'
        })
      });
      
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
      h="220px"
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
            loading={starLoading}
          >
            {isStarred ? "★" : "☆"}
          </Button>
        </Flex>

        {/* Description */}
        <Text color="gray.600" fontSize="sm" lineHeight="1.5" flex={1} mt={1}>
          {description}
        </Text>

        {/* Tags */}
        <Box>
          <HStack spacing={2} flexWrap="wrap">
            {tags.map((tag, index) => (
              <Box
                key={index}
                bg="#60b4f7"
                color="white"
                px={3}
                py={1}
                borderRadius="full"
                fontSize="xs"
                fontWeight="medium"
              >
                {tag}
              </Box>
            ))}
          </HStack>
        </Box>

        <Spacer />

        {/* Authors */}
        <Box mt={2}>
          <Text fontSize="xs" color="gray.500" mb={1} fontWeight="medium">Authors -</Text>
          <Text 
            fontSize="xs" 
            color="gray.600" 
            lineHeight="1.3"
            overflow="hidden"
            textOverflow="ellipsis"
            noOfLines={2}
          >
            {authors.join(", ")}
          </Text>
        </Box>
      </VStack>
    </Box>
  );
};