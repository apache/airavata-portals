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
  HStack,
  Input,
  Button,
  Text,
  Spacer,
} from "@chakra-ui/react";
import { useState } from "react";
import { useNavigate } from "react-router";
import { useAuth } from "react-oidc-context";

export const Topbar = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const navigate = useNavigate();
  const auth = useAuth();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <Box
      h="60px"
      bg="white"
      borderBottom="1px solid"
      borderColor="gray.200"
      px={6}
      position="fixed"
      top={0}
      left={0}
      right={0}
      zIndex={999}
      display="flex"
      alignItems="center"
    >
      <HStack spacing={4} w="full">
        {/* Logo */}
        <HStack spacing={2} w="250px">
          <Box w={8} h={8} bg="blue.500" borderRadius="md" />
          <Text fontWeight="bold" fontSize="lg">Cybershuttle</Text>
        </HStack>

        {/* Search Bar */}
        <Box as="form" onSubmit={handleSearch} flex={1} maxW="500px">
          <Input
            placeholder="Search models, datasets, notebooks, repositories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            bg="gray.50"
            border="1px solid"
            borderColor="gray.300"
            borderRadius="md"
            _focus={{
              borderColor: "blue.500",
              boxShadow: "0 0 0 1px #3182ce",
            }}
          />
        </Box>

        <Spacer />

        {/* Right side buttons */}
        <HStack spacing={3}>
          {auth.isAuthenticated ? (
            <>
              <Button variant="ghost" size="sm">
                <Text>🔔</Text>
              </Button>
              <Button variant="ghost" size="sm">
                <Text>👤</Text>
              </Button>
            </>
          ) : (
            <Button
              size="sm"
              bg="blue.500"
              color="white"
              _hover={{ bg: "blue.600" }}
              onClick={() => auth.signinRedirect()}
            >
              Sign In
            </Button>
          )}
        </HStack>
      </HStack>
    </Box>
  );
};