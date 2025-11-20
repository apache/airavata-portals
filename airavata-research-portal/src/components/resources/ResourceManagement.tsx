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
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import {
  Box,
  Button,
  Container,
  Heading,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
} from "@chakra-ui/react";
import { useState, useEffect } from "react";
import { ComputeResourceForm } from "./ComputeResourceForm";
import { StorageResourceForm } from "./StorageResourceForm";
import { computeResourceApi, storageResourceApi } from "@/lib/resourceApi";
import { ComputeResource } from "@/interfaces/ComputeResourceType";
import { StorageResource } from "@/interfaces/StorageResourceType";
import { ResourceName } from "@/interfaces/ComputeResourceType";

export const ResourceManagement = () => {
  const [computeResources, setComputeResources] = useState<ResourceName[]>([]);
  const [storageResources, setStorageResources] = useState<ResourceName[]>([]);
  const [selectedComputeResource, setSelectedComputeResource] = useState<ComputeResource | null>(null);
  const [selectedStorageResource, setSelectedStorageResource] = useState<StorageResource | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadResources();
  }, []);

  const loadResources = async () => {
    setLoading(true);
    try {
      const [compute, storage] = await Promise.all([
        computeResourceApi.getAll(),
        storageResourceApi.getAll(),
      ]);
      setComputeResources(compute);
      setStorageResources(storage);
    } catch (error) {
      console.error("Error loading resources:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleComputeResourceSelect = async (id: string) => {
    if (!id) {
      setSelectedComputeResource(null);
      return;
    }
    try {
      const resource = await computeResourceApi.get(id);
      setSelectedComputeResource(resource);
    } catch (error) {
      console.error("Error loading compute resource:", error);
    }
  };

  const handleStorageResourceSelect = async (id: string) => {
    if (!id) {
      setSelectedStorageResource(null);
      return;
    }
    try {
      const resource = await storageResourceApi.get(id);
      setSelectedStorageResource(resource);
    } catch (error) {
      console.error("Error loading storage resource:", error);
    }
  };

  const handleComputeResourceSave = async () => {
    await loadResources();
    setSelectedComputeResource(null);
  };

  const handleStorageResourceSave = async () => {
    await loadResources();
    setSelectedStorageResource(null);
  };

  return (
    <Container maxW="container.xl" mt={8}>
      <Heading mb={6}>Resource Management</Heading>
      <Tabs>
        <TabList>
          <Tab>Compute Resources</Tab>
          <Tab>Storage Resources</Tab>
        </TabList>

        <TabPanels>
          <TabPanel>
            <Box>
              <Button
                mb={4}
                onClick={() => setSelectedComputeResource({ hostName: "" } as ComputeResource)}
              >
                Create New Compute Resource
              </Button>
              <ComputeResourceForm
                resources={computeResources}
                selectedResource={selectedComputeResource}
                onSelect={handleComputeResourceSelect}
                onSave={handleComputeResourceSave}
                loading={loading}
              />
            </Box>
          </TabPanel>

          <TabPanel>
            <Box>
              <Button
                mb={4}
                onClick={() => setSelectedStorageResource({ hostName: "" } as StorageResource)}
              >
                Create New Storage Resource
              </Button>
              <StorageResourceForm
                resources={storageResources}
                selectedResource={selectedStorageResource}
                onSelect={handleStorageResourceSelect}
                onSave={handleStorageResourceSave}
                loading={loading}
              />
            </Box>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Container>
  );
};

