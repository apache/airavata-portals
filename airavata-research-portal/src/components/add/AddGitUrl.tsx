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

import {Button, Code, Input, Text, VStack} from "@chakra-ui/react";
import {useState} from "react";
import yaml from "js-yaml";
import {CreateResourceRequest} from "@/interfaces/Requests/CreateResourceRequest";
import {isPrivacyEnum, PrivacyEnum} from "@/interfaces/PrivacyEnum.ts";
import {toaster} from "@/components/ui/toaster.tsx";

export const AddGitUrl = ({
                            nextStage,
                            createResourceRequest,
                            setCreateResourceRequest,
                            githubUrl,
                            setGithubUrl,
                          }: {
  nextStage: () => void;
  createResourceRequest: CreateResourceRequest;
  setCreateResourceRequest: (data: CreateResourceRequest) => void;
  githubUrl: string;
  setGithubUrl: (url: string) => void;
}) => {
  const [loadingPull, setLoadingPull] = useState(false);

  const onPullCybershuttleYml = async () => {
    try {
      setLoadingPull(true);
      // eslint-disable-next-line no-useless-escape
      const match = githubUrl.match(/github\.com\/([^\/]+)\/([^\/]+)(\.git)?/);
      if (!match) {
        alert("Invalid GitHub URL format.");
        return;
      }

      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const [_, owner, repo] = match;

      const tryFetch = async (branch: string) => {
        const rawUrl = `https://raw.githubusercontent.com/${owner}/${repo}/${branch}/cybershuttle.yml?ts=${Date.now()}`;
        const res = await fetch(rawUrl);
        if (!res.ok) throw new Error(`Branch ${branch} not found`);
        return res.text();
      };

      let fileContent = "";
      try {
        fileContent = await tryFetch("main");
      } catch {
        fileContent = await tryFetch("master");
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const parsed = yaml.load(fileContent) as any;

      console.log(parsed);
      if (!isPrivacyEnum(parsed.project.privacy)) {
        toaster.create({
          title: "Invalid `privacy` field",
          description: `Received '${parsed.privacy}'. Valid values are 'PUBLIC' or 'PRIVATE'`,
          type: "error"
        })
        return;
      }
      setCreateResourceRequest({
        ...createResourceRequest,
        name: parsed.project.name,
        headerImage: "image.png",
        description: parsed.project.description,
        tags: parsed.project.tags,
        authors: parsed.project.authors,
        privacy: parsed.project.privacy as PrivacyEnum
      });
      nextStage();
    } catch (error) {
      console.error("Error fetching cybershuttle.yml:", error);
      alert("Failed to fetch cybershuttle.yml. Please check the URL.");
    } finally {
      setLoadingPull(false);
    }
  };

  return (
      <VStack alignItems="flex-start">
        <Text>Paste GitHub Url</Text>
        <Text fontSize="sm" color="gray.500">
          We&apos;ll pull the <Code>cybershuttle.yml</Code> file from the
          repository to auto-populate the project fields.
        </Text>
        <Input
            placeholder="https://github.com/username/repo"
            value={githubUrl}
            onChange={(e) => {
              let githubUrl = e.target.value;
              if (githubUrl.endsWith(".git")) {
                githubUrl = githubUrl.replace(".git", "");
              }
              setGithubUrl(githubUrl);
            }}
            mt={2}
        />
        <Button
            width="full"
            loading={loadingPull}
            onClick={onPullCybershuttleYml}
            mt={4}
            colorScheme="blue"
            disabled={!githubUrl}
        >
          Pull cybershuttle.yml file
        </Button>
      </VStack>
  );
};
