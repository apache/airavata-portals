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
  Input,
  Textarea,
  Heading,
} from "@chakra-ui/react";
import { useState } from "react";
import { useNavigate } from "react-router";
import { adminApiService } from "../../lib/adminApi";

export const AddNotebookForm = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    category: "",
    tags: "",
    authors: "",
  });

  const categories = [
    "computer_vision",
    "cyber_security", 
    "finance",
    "healthcare",
    "nlp",
    "life_sciences"
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const notebook = {
        title: formData.title,
        description: formData.description,
        category: formData.category,
        tags: formData.tags.split(",").map(tag => tag.trim()).filter(tag => tag),
        authors: formData.authors.split(",").map(author => author.trim()).filter(author => author),
        starCount: 0
      };

      await adminApiService.createNotebook(notebook);
      navigate("/resources/notebooks");
    } catch (error) {
      console.error("Failed to create notebook:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <Box bg="gray.50" minH="100vh">
      <Container maxW="800px" py={10}>
        <VStack spacing={8} align="stretch">
          {/* Header */}
          <Box>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/resources/notebooks")}
              color="gray.600"
              mb={4}
            >
              ← Back to Notebooks
            </Button>
            <Heading size="lg" color="gray.800">
              Create New Notebook
            </Heading>
            <Text color="gray.600" mt={2}>
              Add a new Jupyter notebook to your research environment
            </Text>
          </Box>

          {/* Form */}
          <Box bg="white" borderRadius="lg" p={8} border="1px solid" borderColor="gray.200">
            <form onSubmit={handleSubmit}>
              <VStack spacing={6} align="stretch">
                <Box>
                  <Text fontSize="sm" fontWeight="medium" color="gray.700" mb={2}>
                    Title *
                  </Text>
                  <Input
                    value={formData.title}
                    onChange={(e) => handleInputChange("title", e.target.value)}
                    placeholder="Enter notebook title"
                    required
                  />
                </Box>

                <Box>
                  <Text fontSize="sm" fontWeight="medium" color="gray.700" mb={2}>
                    Description *
                  </Text>
                  <Textarea
                    value={formData.description}
                    onChange={(e) => handleInputChange("description", e.target.value)}
                    placeholder="Describe what this notebook does"
                    rows={4}
                    required
                  />
                </Box>

                <Box>
                  <Text fontSize="sm" fontWeight="medium" color="gray.700" mb={2}>
                    Category *
                  </Text>
                  <Box as="select" 
                    value={formData.category}
                    onChange={(e) => handleInputChange("category", e.target.value)}
                    required
                    p={2}
                    border="1px solid"
                    borderColor="gray.200"
                    borderRadius="md"
                    bg="white"
                    w="full"
                  >
                    <option value="">Select a category</option>
                    {categories.map((category) => (
                      <option key={category} value={category}>
                        {category.replace("_", " ").replace(/\b\w/g, l => l.toUpperCase())}
                      </option>
                    ))}
                  </Box>
                </Box>

                <Box>
                  <Text fontSize="sm" fontWeight="medium" color="gray.700" mb={2}>
                    Tags
                  </Text>
                  <Input
                    value={formData.tags}
                    onChange={(e) => handleInputChange("tags", e.target.value)}
                    placeholder="machine-learning, python, jupyter (comma separated)"
                  />
                  <Text fontSize="sm" color="gray.500" mt={1}>
                    Separate multiple tags with commas
                  </Text>
                </Box>

                <Box>
                  <Text fontSize="sm" fontWeight="medium" color="gray.700" mb={2}>
                    Authors
                  </Text>
                  <Input
                    value={formData.authors}
                    onChange={(e) => handleInputChange("authors", e.target.value)}
                    placeholder="author1@example.com, author2@example.com (comma separated)"
                  />
                  <Text fontSize="sm" color="gray.500" mt={1}>
                    Separate multiple authors with commas
                  </Text>
                </Box>

                <HStack spacing={4} pt={4}>
                  <Button
                    type="submit"
                    bg="#60b4f7"
                    color="white"
                    _hover={{ bg: "#4a9ce6" }}
                    loading={loading}
                  >
                    {loading ? "Creating..." : "Create Notebook"}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => navigate("/resources/notebooks")}
                  >
                    Cancel
                  </Button>
                </HStack>
              </VStack>
            </form>
          </Box>
        </VStack>
      </Container>
    </Box>
  );
};