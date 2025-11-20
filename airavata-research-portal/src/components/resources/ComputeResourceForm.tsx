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
  FormControl,
  FormLabel,
  Input,
  Select,
  Textarea,
  VStack,
  HStack,
  Switch,
  NumberInput,
  NumberInputField,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  useToast,
} from "@chakra-ui/react";
import { useState, useEffect } from "react";
import { ComputeResource, ResourceName } from "@/interfaces/ComputeResourceType";
import { computeResourceApi } from "@/lib/resourceApi";
import { QueueManagement } from "./QueueManagement";

interface ComputeResourceFormProps {
  resources: ResourceName[];
  selectedResource: ComputeResource | null;
  onSelect: (id: string) => void;
  onSave: () => void;
  loading: boolean;
}

export const ComputeResourceForm = ({
  resources,
  selectedResource,
  onSelect,
  onSave,
  loading,
}: ComputeResourceFormProps) => {
  const [formData, setFormData] = useState<ComputeResource>({
    hostName: "",
  } as ComputeResource);
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  useEffect(() => {
    if (selectedResource) {
      setFormData(selectedResource);
    } else {
      setFormData({ hostName: "" } as ComputeResource);
    }
  }, [selectedResource]);

  const handleChange = (field: keyof ComputeResource, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (formData.computeResourceId) {
        await computeResourceApi.update(formData.computeResourceId, formData);
        toast({
          title: "Success",
          description: "Compute resource updated successfully",
          status: "success",
          duration: 3000,
        });
      } else {
        await computeResourceApi.create(formData);
        toast({
          title: "Success",
          description: "Compute resource created successfully",
          status: "success",
          duration: 3000,
        });
      }
      onSave();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.error || "Failed to save compute resource",
        status: "error",
        duration: 5000,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!formData.computeResourceId) return;
    if (!confirm("Are you sure you want to delete this compute resource?")) return;

    setSaving(true);
    try {
      await computeResourceApi.delete(formData.computeResourceId);
      toast({
        title: "Success",
        description: "Compute resource deleted successfully",
        status: "success",
        duration: 3000,
      });
      onSave();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.error || "Failed to delete compute resource",
        status: "error",
        duration: 5000,
      });
    } finally {
      setSaving(false);
    }
  };

  if (!selectedResource) {
    return (
      <Box>
        {resources.length > 0 ? (
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>ID</Th>
                <Th>Name</Th>
                <Th>Actions</Th>
              </Tr>
            </Thead>
            <Tbody>
              {resources.map((resource) => (
                <Tr key={resource.id}>
                  <Td>{resource.id}</Td>
                  <Td>{resource.name}</Td>
                  <Td>
                    <Button size="sm" onClick={() => onSelect(resource.id)}>
                      Edit
                    </Button>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        ) : (
          <Box p={4} textAlign="center">
            No compute resources found. Click "Create New Compute Resource" to add one.
          </Box>
        )}
      </Box>
    );
  }

  return (
    <Box>
      <VStack spacing={4} align="stretch">
        <FormControl>
          <FormLabel>Host Name *</FormLabel>
          <Input
            value={formData.hostName || ""}
            onChange={(e) => handleChange("hostName", e.target.value)}
            placeholder="e.g., login.example.com"
          />
        </FormControl>

        <FormControl>
          <FormLabel>Resource Description</FormLabel>
          <Textarea
            value={formData.resourceDescription || ""}
            onChange={(e) => handleChange("resourceDescription", e.target.value)}
            placeholder="Description of the compute resource"
          />
        </FormControl>

        <FormControl>
          <FormLabel>Enabled</FormLabel>
          <Switch
            isChecked={formData.enabled ?? true}
            onChange={(e) => handleChange("enabled", e.target.checked)}
          />
        </FormControl>

        <HStack>
          <FormControl>
            <FormLabel>CPUs Per Node</FormLabel>
            <NumberInput
              value={formData.cpusPerNode || ""}
              onChange={(_, value) => handleChange("cpusPerNode", value)}
            >
              <NumberInputField />
            </NumberInput>
          </FormControl>

          <FormControl>
            <FormLabel>Max Memory Per Node (MB)</FormLabel>
            <NumberInput
              value={formData.maxMemoryPerNode || ""}
              onChange={(_, value) => handleChange("maxMemoryPerNode", value)}
            >
              <NumberInputField />
            </NumberInput>
          </FormControl>
        </HStack>

        <HStack>
          <FormControl>
            <FormLabel>Default Node Count</FormLabel>
            <NumberInput
              value={formData.defaultNodeCount || ""}
              onChange={(_, value) => handleChange("defaultNodeCount", value)}
            >
              <NumberInputField />
            </NumberInput>
          </FormControl>

          <FormControl>
            <FormLabel>Default CPU Count</FormLabel>
            <NumberInput
              value={formData.defaultCPUCount || ""}
              onChange={(_, value) => handleChange("defaultCPUCount", value)}
            >
              <NumberInputField />
            </NumberInput>
          </FormControl>

          <FormControl>
            <FormLabel>Default Walltime (minutes)</FormLabel>
            <NumberInput
              value={formData.defaultWalltime || ""}
              onChange={(_, value) => handleChange("defaultWalltime", value)}
            >
              <NumberInputField />
            </NumberInput>
          </FormControl>
        </HStack>

        {formData.computeResourceId && (
          <QueueManagement
            computeResourceId={formData.computeResourceId}
            queues={formData.batchQueues || []}
            onQueuesChange={(queues) => handleChange("batchQueues", queues)}
          />
        )}

        <HStack>
          <Button
            colorScheme="blue"
            onClick={handleSave}
            isLoading={saving}
            loadingText="Saving..."
          >
            {formData.computeResourceId ? "Update" : "Create"}
          </Button>
          {formData.computeResourceId && (
            <Button colorScheme="red" onClick={handleDelete} isLoading={saving}>
              Delete
            </Button>
          )}
          <Button onClick={() => onSelect("")}>Back to List</Button>
        </HStack>
      </VStack>
    </Box>
  );
};

