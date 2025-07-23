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

import { Box, Container, Text, VStack } from "@chakra-ui/react";
import { PageHeader } from "../PageHeader";
import { useEffect, useState } from "react";
import { adminApiService } from "../../lib/adminApi";

const Catalog = () => {
  const [healthStatus, setHealthStatus] = useState<any>(null);
  const [testData, setTestData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchApiData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Test health endpoint
        const health = await adminApiService.getHealth();
        setHealthStatus(health);

        // Test data endpoint
        const test = await adminApiService.getTestData();
        setTestData(test);

      } catch (err) {
        console.error("Failed to fetch API data:", err);
        setError("Failed to connect to Admin API Server. Make sure it's running on localhost:8080");
      } finally {
        setLoading(false);
      }
    };

    fetchApiData();
  }, []);

  return (
    <Box>
      <Container maxW="container.xl" mt={8}>
        <PageHeader
          title="Research Catalog"
          description="Testing connection to Admin API Server"
        />

        <VStack spacing={6} mt={8} align="stretch">
          {loading && (
            <Box textAlign="center" py={8}>
              <Text>Loading...</Text>
            </Box>
          )}

          {error && (
            <Box p={6} border="1px solid red" borderRadius="md" bg="red.50">
              <Text color="red.600" fontWeight="bold">Error:</Text>
              <Text color="red.700">{error}</Text>
            </Box>
          )}

          {!loading && !error && (
            <VStack spacing={4} align="stretch">
              {/* Health Status */}
              <Box p={6} border="1px solid gray" borderRadius="md">
                <Text fontSize="xl" fontWeight="bold" mb={4}>API Health Status</Text>
                {healthStatus && (
                  <VStack align="start" spacing={2}>
                    <Text>Status: {healthStatus.status}</Text>
                    <Text>Message: {healthStatus.message}</Text>
                    <Text fontSize="sm" color="gray.500">
                      Timestamp: {new Date(healthStatus.timestamp).toLocaleString()}
                    </Text>
                  </VStack>
                )}
              </Box>

              {/* Test Data */}
              <Box p={6} border="1px solid gray" borderRadius="md">
                <Text fontSize="xl" fontWeight="bold" mb={4}>API Test Data</Text>
                {testData && (
                  <VStack align="start" spacing={2}>
                    <Text>Message: {testData.message}</Text>
                    <Text color="blue.500">{testData.data}</Text>
                  </VStack>
                )}
              </Box>

              {/* Success Message */}
              <Box p={6} border="1px solid green" borderRadius="md" bg="green.50">
                <Text color="green.600" fontWeight="bold" fontSize="lg">
                  Success! Connected to Admin API Server!
                </Text>
                <Text color="green.700" mt={2}>
                  The integration is working. React portal can communicate with Spring Boot API.
                </Text>
              </Box>
            </VStack>
          )}
        </VStack>
      </Container>
    </Box>
  );
};

export { Catalog };