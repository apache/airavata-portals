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
import {Container, Heading, SimpleGrid, Text,} from "@chakra-ui/react";
import {useState} from "react";
import "./TagInput.css";
import {Resource} from "@/interfaces/ResourceType";
import {ResourceCard} from "../home/ResourceCard";
import {ResourceFilters} from "@/components/resources/ResourceFilters.tsx";

export const Resources = () => {
  const [resources, setResources] = useState<Resource[]>([]);

  return (
      <>
        <Container maxW="container.lg" mt={8}>
          <Heading
              textAlign="center"
              fontSize={{base: "4xl", md: "5xl"}}
              fontWeight="black"
              lineHeight={1.2}
          >
            Research Catalog
          </Heading>
          <Text mt={2} textAlign="center">
            Browse models, notebooks, repositories, and datasets. Created by
            scientists and prepared for
            <Text as="span" color="blue.600" fontWeight="bold">
              {" "}
              execution in local and remote machines
            </Text>
            .
          </Text>

          <ResourceFilters
              resources={resources}
              setResources={setResources}
          />

          <SimpleGrid
              columns={{base: 1, md: 2, lg: 4}}
              mt={4}
              gap={2}
              justifyContent="space-around"
          >
            {resources.map((resource: Resource) => {
              return (
                  <ResourceCard
                      resource={resource}
                      key={resource.id}
                  />
              );
            })}
          </SimpleGrid>
        </Container>
      </>
  );
};
