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
  Textarea,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  useToast,
} from "@chakra-ui/react";
import { useState } from "react";
import { BatchQueue } from "@/interfaces/ComputeResourceType";
import { computeResourceApi } from "@/lib/resourceApi";

interface QueueManagementProps {
  computeResourceId: string;
  queues: BatchQueue[];
  onQueuesChange: (queues: BatchQueue[]) => void;
}

export const QueueManagement = ({
  computeResourceId,
  queues,
  onQueuesChange,
}: QueueManagementProps) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [editingQueue, setEditingQueue] = useState<BatchQueue | null>(null);
  const [queueForm, setQueueForm] = useState<BatchQueue>({
    queueName: "",
  } as BatchQueue);
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  const handleAddQueue = () => {
    setEditingQueue(null);
    setQueueForm({ queueName: "" } as BatchQueue);
    onOpen();
  };

  const handleEditQueue = (queue: BatchQueue) => {
    setEditingQueue(queue);
    setQueueForm({ ...queue });
    onOpen();
  };

  const handleDeleteQueue = async (queueName: string) => {
    if (!confirm(`Are you sure you want to delete queue "${queueName}"?`)) return;

    setSaving(true);
    try {
      await computeResourceApi.deleteQueue(computeResourceId, queueName);
      const updatedQueues = queues.filter((q) => q.queueName !== queueName);
      onQueuesChange(updatedQueues);
      toast({
        title: "Success",
        description: "Queue deleted successfully",
        status: "success",
        duration: 3000,
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.error || "Failed to delete queue",
        status: "error",
        duration: 5000,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleSaveQueue = async () => {
    if (!queueForm.queueName) {
      toast({
        title: "Error",
        description: "Queue name is required",
        status: "error",
        duration: 3000,
      });
      return;
    }

    setSaving(true);
    try {
      if (editingQueue) {
        await computeResourceApi.updateQueue(computeResourceId, editingQueue.queueName, queueForm);
        const updatedQueues = queues.map((q) =>
          q.queueName === editingQueue.queueName ? queueForm : q
        );
        onQueuesChange(updatedQueues);
        toast({
          title: "Success",
          description: "Queue updated successfully",
          status: "success",
          duration: 3000,
        });
      } else {
        await computeResourceApi.addQueue(computeResourceId, queueForm);
        onQueuesChange([...queues, queueForm]);
        toast({
          title: "Success",
          description: "Queue added successfully",
          status: "success",
          duration: 3000,
        });
      }
      onClose();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.error || "Failed to save queue",
        status: "error",
        duration: 5000,
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box>
      <HStack mb={4}>
        <Button size="sm" onClick={handleAddQueue}>
          Add Queue
        </Button>
      </HStack>

      <Table variant="simple">
        <Thead>
          <Tr>
            <Th>Queue Name</Th>
            <Th>Description</Th>
            <Th>Max Runtime</Th>
            <Th>Max Nodes</Th>
            <Th>Default Queue</Th>
            <Th>Actions</Th>
          </Tr>
        </Thead>
        <Tbody>
          {queues.map((queue) => (
            <Tr key={queue.queueName}>
              <Td>{queue.queueName}</Td>
              <Td>{queue.queueDescription || "-"}</Td>
              <Td>{queue.maxRunTime || "-"}</Td>
              <Td>{queue.maxNodes || "-"}</Td>
              <Td>{queue.isDefaultQueue ? "Yes" : "No"}</Td>
              <Td>
                <HStack>
                  <Button size="sm" onClick={() => handleEditQueue(queue)}>
                    Edit
                  </Button>
                  <Button
                    size="sm"
                    colorScheme="red"
                    onClick={() => handleDeleteQueue(queue.queueName)}
                  >
                    Delete
                  </Button>
                </HStack>
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>

      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>{editingQueue ? "Edit Queue" : "Add Queue"}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <FormControl isRequired>
                <FormLabel>Queue Name</FormLabel>
                <Input
                  value={queueForm.queueName || ""}
                  onChange={(e) => setQueueForm({ ...queueForm, queueName: e.target.value })}
                  isDisabled={!!editingQueue}
                />
              </FormControl>

              <FormControl>
                <FormLabel>Queue Description</FormLabel>
                <Textarea
                  value={queueForm.queueDescription || ""}
                  onChange={(e) =>
                    setQueueForm({ ...queueForm, queueDescription: e.target.value })
                  }
                />
              </FormControl>

              <HStack>
                <FormControl>
                  <FormLabel>Max Runtime (hours)</FormLabel>
                  <NumberInput
                    value={queueForm.maxRunTime || ""}
                    onChange={(_, value) =>
                      setQueueForm({ ...queueForm, maxRunTime: value })
                    }
                  >
                    <NumberInputField />
                  </NumberInput>
                </FormControl>

                <FormControl>
                  <FormLabel>Max Nodes</FormLabel>
                  <NumberInput
                    value={queueForm.maxNodes || ""}
                    onChange={(_, value) =>
                      setQueueForm({ ...queueForm, maxNodes: value })
                    }
                  >
                    <NumberInputField />
                  </NumberInput>
                </FormControl>
              </HStack>

              <HStack>
                <FormControl>
                  <FormLabel>Max Processors</FormLabel>
                  <NumberInput
                    value={queueForm.maxProcessors || ""}
                    onChange={(_, value) =>
                      setQueueForm({ ...queueForm, maxProcessors: value })
                    }
                  >
                    <NumberInputField />
                  </NumberInput>
                </FormControl>

                <FormControl>
                  <FormLabel>Max Jobs in Queue</FormLabel>
                  <NumberInput
                    value={queueForm.maxJobsInQueue || ""}
                    onChange={(_, value) =>
                      setQueueForm({ ...queueForm, maxJobsInQueue: value })
                    }
                  >
                    <NumberInputField />
                  </NumberInput>
                </FormControl>
              </HStack>

              <HStack>
                <FormControl>
                  <FormLabel>Max Memory (MB)</FormLabel>
                  <NumberInput
                    value={queueForm.maxMemory || ""}
                    onChange={(_, value) =>
                      setQueueForm({ ...queueForm, maxMemory: value })
                    }
                  >
                    <NumberInputField />
                  </NumberInput>
                </FormControl>

                <FormControl>
                  <FormLabel>CPU Per Node</FormLabel>
                  <NumberInput
                    value={queueForm.cpuPerNode || ""}
                    onChange={(_, value) =>
                      setQueueForm({ ...queueForm, cpuPerNode: value })
                    }
                  >
                    <NumberInputField />
                  </NumberInput>
                </FormControl>
              </HStack>

              <HStack>
                <FormControl>
                  <FormLabel>Default Node Count</FormLabel>
                  <NumberInput
                    value={queueForm.defaultNodeCount || ""}
                    onChange={(_, value) =>
                      setQueueForm({ ...queueForm, defaultNodeCount: value })
                    }
                  >
                    <NumberInputField />
                  </NumberInput>
                </FormControl>

                <FormControl>
                  <FormLabel>Default CPU Count</FormLabel>
                  <NumberInput
                    value={queueForm.defaultCPUCount || ""}
                    onChange={(_, value) =>
                      setQueueForm({ ...queueForm, defaultCPUCount: value })
                    }
                  >
                    <NumberInputField />
                  </NumberInput>
                </FormControl>
              </HStack>

              <FormControl>
                <FormLabel>Default Walltime (minutes)</FormLabel>
                <NumberInput
                  value={queueForm.defaultWalltime || ""}
                  onChange={(_, value) =>
                    setQueueForm({ ...queueForm, defaultWalltime: value })
                  }
                >
                  <NumberInputField />
                </NumberInput>
              </FormControl>

              <FormControl>
                <FormLabel>Queue Specific Macros</FormLabel>
                <Textarea
                  value={queueForm.queueSpecificMacros || ""}
                  onChange={(e) =>
                    setQueueForm({ ...queueForm, queueSpecificMacros: e.target.value })
                  }
                  placeholder="Comma-separated macros"
                />
              </FormControl>

              <FormControl>
                <FormLabel>Is Default Queue</FormLabel>
                <Switch
                  isChecked={queueForm.isDefaultQueue || false}
                  onChange={(e) =>
                    setQueueForm({ ...queueForm, isDefaultQueue: e.target.checked })
                  }
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button colorScheme="blue" onClick={handleSaveQueue} isLoading={saving}>
              {editingQueue ? "Update" : "Add"}
            </Button>
            <Button onClick={onClose} ml={2}>
              Cancel
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};



