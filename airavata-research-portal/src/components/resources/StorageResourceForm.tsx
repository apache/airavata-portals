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
  Textarea,
  VStack,
  HStack,
  Switch,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  useToast,
} from "@chakra-ui/react";
import { useState, useEffect } from "react";
import { StorageResource } from "@/interfaces/StorageResourceType";
import { ResourceName } from "@/interfaces/ComputeResourceType";
import { storageResourceApi } from "@/lib/resourceApi";

interface StorageResourceFormProps {
  resources: ResourceName[];
  selectedResource: StorageResource | null;
  onSelect: (id: string) => void;
  onSave: () => void;
  loading: boolean;
}

export const StorageResourceForm = ({
  resources,
  selectedResource,
  onSelect,
  onSave,
  loading,
}: StorageResourceFormProps) => {
  const [formData, setFormData] = useState<StorageResource>({
    hostName: "",
  } as StorageResource);
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  useEffect(() => {
    if (selectedResource) {
      setFormData(selectedResource);
    } else {
      setFormData({ hostName: "" } as StorageResource);
    }
  }, [selectedResource]);

  const handleChange = (field: keyof StorageResource, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (formData.storageResourceId) {
        await storageResourceApi.update(formData.storageResourceId, formData);
        toast({
          title: "Success",
          description: "Storage resource updated successfully",
          status: "success",
          duration: 3000,
        });
      } else {
        await storageResourceApi.create(formData);
        toast({
          title: "Success",
          description: "Storage resource created successfully",
          status: "success",
          duration: 3000,
        });
      }
      onSave();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.error || "Failed to save storage resource",
        status: "error",
        duration: 5000,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!formData.storageResourceId) return;
    if (!confirm("Are you sure you want to delete this storage resource?")) return;

    setSaving(true);
    try {
      await storageResourceApi.delete(formData.storageResourceId);
      toast({
        title: "Success",
        description: "Storage resource deleted successfully",
        status: "success",
        duration: 3000,
      });
      onSave();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.error || "Failed to delete storage resource",
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
            No storage resources found. Click "Create New Storage Resource" to add one.
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
            placeholder="e.g., storage.example.com"
          />
        </FormControl>

        <FormControl>
          <FormLabel>Storage Resource Description</FormLabel>
          <Textarea
            value={formData.storageResourceDescription || ""}
            onChange={(e) => handleChange("storageResourceDescription", e.target.value)}
            placeholder="Description of the storage resource"
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
          <Button
            colorScheme="blue"
            onClick={handleSave}
            isLoading={saving}
            loadingText="Saving..."
          >
            {formData.storageResourceId ? "Update" : "Create"}
          </Button>
          {formData.storageResourceId && (
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

