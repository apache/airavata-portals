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
  VStack,
  Text,
  Button,
  HStack,
  Flex,
  Spacer,
} from "@chakra-ui/react";
import { Link, useLocation } from "react-router";
import { useAuth } from "react-oidc-context";

interface SidebarItemProps {
  icon: string;
  label: string;
  to: string;
  isActive?: boolean;
}

const SidebarItem = ({ icon, label, to, isActive }: SidebarItemProps) => {
  return (
    <Box as={Link} to={to} w="full">
      <HStack
        p={3}
        borderRadius="md"
        bg={isActive ? "blue.50" : "transparent"}
        color={isActive ? "blue.600" : "gray.700"}
        _hover={{ bg: "gray.50" }}
        cursor="pointer"
      >
        <Text fontSize="lg">{icon}</Text>
        <Text fontWeight={isActive ? "medium" : "normal"}>{label}</Text>
      </HStack>
    </Box>
  );
};

interface GlobalSidebarProps {
  isLoggedIn: boolean;
}

export const GlobalSidebar = ({ isLoggedIn }: GlobalSidebarProps) => {
  const location = useLocation();
  const auth = useAuth();

  const publicItems = [
    { icon: "⌂", label: "Home", to: "/" },
    { icon: "◉", label: "Models", to: "/resources/models" },
    { icon: "□", label: "Repositories", to: "/resources/repositories" },
    { icon: "☰", label: "Notebooks", to: "/resources/notebooks" },
    { icon: "▦", label: "Datasets", to: "/resources/datasets" },
    { icon: "◈", label: "Resources", to: "/resources" },
  ];

  const authenticatedItems = [
    { icon: "☆", label: "Your Stars", to: "/resources/starred" },
    { icon: "□", label: "Sessions", to: "/sessions" },
    { icon: "+", label: "Add", to: "/add" },
  ];

  const moreItems = [
    { icon: "◐", label: "Your Activity", to: "/activity" },
  ];

  return (
    <Box
      w="250px"
      h="calc(100vh - 60px)"
      bg="white"
      borderRight="1px solid"
      borderColor="gray.200"
      p={4}
      position="fixed"
      left={0}
      top="60px"
      zIndex={1000}
    >
      <VStack spacing={6} align="stretch" h="full">
        {/* Create New Button */}
        <Button
          bg="#40a9f7"
          color="white"
          size="sm"
          w="full"
          leftIcon={<Text>+</Text>}
          _hover={{ bg: "#2e90d9" }}
        >
          Create New
        </Button>

        {/* Navigation Items */}
        <VStack spacing={1} align="stretch">
          {publicItems.map((item) => (
            <SidebarItem
              key={item.to}
              {...item}
              isActive={location.pathname === item.to}
            />
          ))}
        </VStack>

        {/* Authenticated Items */}
        {isLoggedIn && (
          <VStack spacing={1} align="stretch">
            {authenticatedItems.map((item) => (
              <SidebarItem
                key={item.to}
                {...item}
                isActive={location.pathname === item.to}
              />
            ))}
          </VStack>
        )}

        {/* More Section */}
        <Box>
          <Text fontSize="sm" fontWeight="medium" color="gray.500" mb={2} px={3}>
            More
          </Text>
          <VStack spacing={1} align="stretch">
            {moreItems.map((item) => (
              <SidebarItem
                key={item.to}
                {...item}
                isActive={location.pathname === item.to}
              />
            ))}
          </VStack>
        </Box>

        <Spacer />

        {/* Bottom Section */}
        <Box>
          {isLoggedIn ? (
            <VStack spacing={2} align="stretch">
              <SidebarItem icon="❓" label="Need Help?" to="/help" />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => auth.signoutRedirect()}
                w="full"
                justifyContent="flex-start"
                leftIcon={<Text>🚪</Text>}
              >
                Sign Out
              </Button>
            </VStack>
          ) : (
            <Box p={3} bg="gray.50" borderRadius="md">
              <Text fontSize="sm" fontWeight="medium" mb={1}>Need Help?</Text>
              <Text fontSize="xs" color="gray.600" mb={2}>
                Find answers quickly in our Help Center or reach out to our support team.
              </Text>
              <Button size="xs" variant="outline" w="full">
                Get Support
              </Button>
            </Box>
          )}
        </Box>
      </VStack>
    </Box>
  );
};