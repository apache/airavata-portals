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

import {useEffect, useState} from "react";
import {Box, Button, Code, HStack, Input, Spinner, Text, VStack} from "@chakra-ui/react";
import {ResourceTypeEnum} from "@/interfaces/ResourceTypeEnum.ts";
import {toaster} from "@/components/ui/toaster.tsx";
import {useNavigate} from "react-router";
import {Tag as TagEntity} from "@/interfaces/TagType.tsx";
import api from "@/lib/api.ts";
import {CONTROLLER} from "@/lib/controller.ts";
import {resourceTypeToColor} from "@/lib/util.ts";
import {FaCheck} from "react-icons/fa";
import {Resource} from "@/interfaces/ResourceType.ts";

const getResources = async (
    types: ResourceTypeEnum[],
    stringTagsArr: string[],
    searchText: string
) => {
  const response = await api.get(`${CONTROLLER.resources}/public`, {
    params: {
      type: types.join(","),
      tag: stringTagsArr.join(","),
      nameSearch: searchText,
      pageNumber: 0,
      pageSize: 100,
    },
  });
  return response.data;
};

const getTags = async () => {
  try {
    const response = await api.get(`${CONTROLLER.resources}/public/tags/all`);
    return response.data;
  } catch (error) {
    console.error("Error fetching:", error);
  }
};

export const ResourceFilters = ({setResources, resources}: {
  setResources: (resources: Resource[]) => void,
  resources: Resource[]
}) => {
  const [searchText, setSearchText] = useState("");
  const [hydrated, setHydrated] = useState(false);
  const [tags, setTags] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [resourceTypes, setResourceTypes] = useState<ResourceTypeEnum[]>([]);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const labels = [
    ResourceTypeEnum.REPOSITORY,
    ResourceTypeEnum.NOTEBOOK,
    ResourceTypeEnum.DATASET,
    ResourceTypeEnum.MODEL,
  ];

  // Debounce the callback to the parent
  useEffect(() => {
    const handler = setTimeout(() => {
      setSearchText(searchText);
    }, 400);

    return () => {
      clearTimeout(handler);
    };
  }, [searchText, setSearchText]);

  const updateURLWithResourceTypes = (
      updatedResourceTypes: ResourceTypeEnum[]
  ) => {
    const params = new URLSearchParams(location.search);

    if (updatedResourceTypes.length > 0) {
      params.set(
          "resourceTypes",
          updatedResourceTypes.map((type) => type).join(",")
      );
    } else {
      params.delete("resourceTypes");
    }

    navigate(
        {pathname: location.pathname, search: params.toString()},
        {replace: true}
    );
  };

  const updateURLWithTags = (updatedTags: string[]) => {
    const params = new URLSearchParams(location.search);

    if (updatedTags.length > 0) {
      params.set("tags", updatedTags.join(","));
    } else {
      params.delete("tags");
    }

    navigate(
        {pathname: location.pathname, search: params.toString()},
        {replace: true}
    );
  };

  const updateURLWithSearchText = (searchText: string) => {
    const params = new URLSearchParams(location.search);
    if (searchText.length > 0) {
      params.set("searchText", searchText);
    } else {
      params.delete("searchText");
    }

    navigate(
        {pathname: location.pathname, search: params.toString()},
        {replace: true}
    );
  }

  useEffect(() => {
    if (!hydrated) return;
    setLoading(true);

    const handler = setTimeout(() => {
      updateURLWithSearchText(searchText);

      async function fetchResources() {
        try {
          const resources = await getResources(resourceTypes, tags, searchText);
          setResources(resources.content);
        } catch {
          toaster.create({
            type: "error",
            title: "Error fetching resources",
            description: "An error occurred while fetching resources.",
          });
        } finally {
          setLoading(false);
        }
      }

      fetchResources();
    }, 200);

    return () => clearTimeout(handler);
  }, [resourceTypes, tags, hydrated, searchText]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const tagsParam = params.get("tags");
    if (tagsParam) {
      const initialTags = tagsParam.split(",");
      setTags(initialTags);
    } else {
      setTags([]);
    }

    const resourceTypesParam = params.get("resourceTypes");
    if (resourceTypesParam) {
      const initialResourceTypes = resourceTypesParam.split(
          ","
      ) as ResourceTypeEnum[];
      initialResourceTypes.forEach((type) => {
        if (
            !Object.values(ResourceTypeEnum).includes(type as ResourceTypeEnum)
        ) {
          toaster.create({
            type: "error",
            title: "Invalid resource type",
            description: `Invalid resource type: ${type}. Valid types are: ${Object.values(
                ResourceTypeEnum
            ).join(", ")}`,
          });
          return;
        }
      });

      const searchTextParam = params.get("searchText");
      if (searchTextParam) {
        setSearchText(searchTextParam);
      }

      setResourceTypes(initialResourceTypes);
    } else {
      setResourceTypes([]);
    }

    setHydrated(true);
  }, [location.search]);

  useEffect(() => {
    async function fetchTags() {
      const tags: TagEntity[] = await getTags();
      const suggestedTags = tags.map(tag => tag.value);

      setSuggestions(suggestedTags);
    }

    fetchTags();
  }, []);

  return (
      <>
        <Box mt={4} maxWidth="1000px" mx="auto">
          <VStack alignItems={'flex-start'}>
            <Text fontSize="sm" color="gray.500" fontWeight="bold">
              Search by resource title
            </Text>
            <Input
                rounded={'lg'}
                placeholder={'Search by resource title'}
                value={searchText}
                onChange={(e) => {
                  setSearchText(e.target.value)
                }}
            />
          </VStack>

          <VStack mt={2} alignItems='flex-start'>
            <Text fontSize="sm" color="gray.500" fontWeight="bold">
              Tags Filter
            </Text>

            <HStack wrap={'wrap'}>
              {
                suggestions.map((tag) => {
                  const isCurrentlyIncluded = tags.includes(tag);
                  return (
                      <Button
                          key={tag}
                          size={'xs'}
                          bg={isCurrentlyIncluded ? 'blue.200' : "transparent"}
                          color={"blue.600"}
                          borderColor={'blue.400'}
                          _hover={{
                            bg: 'blue.400',
                          }}
                          rounded={'lg'}
                          onClick={() => {
                            setTags((prev) => {
                              let newTags = [...prev, tag];
                              if (isCurrentlyIncluded) {
                                newTags = prev.filter((shouldKeepTag) => tag != shouldKeepTag)
                              }
                              updateURLWithTags(newTags);
                              return newTags;
                            });
                          }}
                      >
                        {tag}
                      </Button>
                  )
                })
              }
            </HStack>

          </VStack>


          <VStack mt={2} alignItems='flex-start'>
            <Text fontSize="sm" color="gray.500" fontWeight="bold">
              Resource Filter
            </Text>
            <HStack wrap="wrap">
              {labels.map((type) => {
                const isSelected = resourceTypes.includes(type);
                const color = resourceTypeToColor(type);
                return (
                    <Button
                        key={type}
                        variant="outline"
                        color={color + ".600"}
                        bg={isSelected ? color + ".100" : "white"}
                        rounded={'lg'}
                        _hover={{
                          bg: isSelected ? color + ".200" : "gray.100",
                          color: isSelected ? color + ".700" : "black",
                        }}
                        borderColor={color + ".200"}
                        size="sm"
                        onClick={() => {
                          let newResourceTypes = [...resourceTypes, type];

                          if (isSelected) {
                            newResourceTypes = resourceTypes.filter(
                                (t) => t !== type
                            );
                          }
                          setResourceTypes(newResourceTypes);
                          updateURLWithResourceTypes(newResourceTypes);
                        }}
                    >
                      {type}
                      {isSelected && <FaCheck color={color}/>}
                    </Button>
                );
              })}
            </HStack>
          </VStack>
        </Box>

        {loading && (
            <Box textAlign="center" mt={2}>
              <Spinner size={'lg'}/>
            </Box>
        )}

        {resources.length === 0 && (
            <Box textAlign="center" color="gray.500">
              <Text textAlign="center" mt={8} mb={4}>
                No resources found with the following criteria:
              </Text>
              <Text>
                Tags:{" "}
                {tags.length > 0 ? (
                    <>
                      {tags.map((tag) => (
                          <Code key={tag} colorScheme="blue" mr={1}>
                            {tag}
                          </Code>
                      ))}
                    </>
                ) : (
                    <Text as="span">None</Text>
                )}
              </Text>

              <Text>
                Resource Types:{" "}
                {resourceTypes.length > 0 ? (
                    <>
                      {resourceTypes.map((type) => (
                          <Code key={type} colorScheme="blue" mr={1}>
                            {type}
                          </Code>
                      ))}
                    </>
                ) : (
                    <Text as="span">None</Text>
                )}
              </Text>
            </Box>
        )}
      </>
  );
};