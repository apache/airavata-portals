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

import {Resource} from "@/interfaces/ResourceType.ts";
import {ResourceOptionButton} from "@/components/resources/ResourceOptions.tsx";
import {Box} from "@chakra-ui/react";
import {toaster} from "@/components/ui/toaster.tsx";
import {useEffect, useState} from "react";
import {BsStar, BsStarFill} from "react-icons/bs";
import {useAuth} from "react-oidc-context";

export const StarResourceButton = ({
                                     resource,
                                     onSuccess,
                                   }: {
  resource: Resource,
  onSuccess: (resourceId: string) => void,
}) => {
  const [changeStarLoading, setChangeStarLoading] = useState(false);
  const [initialLoad, setinitialLoad] = useState(false);
  const [starred, setStarred] = useState(false);
  const auth = useAuth();

  const getApiEndpoint = (resourceType: string, resourceId: string) => {
    const typeMap: { [key: string]: string } = {
      'MODEL': 'models',
      'DATASET': 'datasets', 
      'NOTEBOOK': 'notebooks',
      'REPOSITORY': 'repositories',
      'STORAGE': 'storage-resources',
      'COMPUTE': 'compute-resources'
    };
    return `http://localhost:8080/api/${typeMap[resourceType] || 'models'}/${resourceId}/star`;
  };

  useEffect(() => {
    if (!auth.user?.profile.email) return;
    
    async function getWhetherUserStarred() {
      try {
        setinitialLoad(true);
        const endpoint = getApiEndpoint(resource.type, resource.id);
        const response = await fetch(`${endpoint}?userEmail=${encodeURIComponent(auth.user?.profile.email || '')}`);
        const isStarred = await response.json();
        setStarred(isStarred);
      } catch (error) {
        console.error('Error checking star status:', error);
      } finally {
        setinitialLoad(false);
      }
    }

    getWhetherUserStarred();
  }, [resource.id, resource.type, auth.user?.profile.email]);

  const handleStarResource = async () => {
    if (!auth.user?.profile.email) {
      toaster.create({
        title: "Please log in to star resources",
        type: "error",
      });
      return;
    }

    try {
      setChangeStarLoading(true);
      const endpoint = getApiEndpoint(resource.type, resource.id);
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          userEmail: auth.user.profile.email,
          userName: auth.user.profile.name || 'User'
        })
      });
      
      const newStarredState = await response.json();
      
      toaster.create({
        title: newStarredState ? "Starred" : "Unstarred",
        description: resource.name,
        type: "success",
      })
      
      setStarred(newStarredState);
      
      if (!newStarredState) {
        onSuccess(resource.id || "INVALID");
      }
    } catch (error) {
      console.error('Error starring resource:', error);
      toaster.create({
        title: "Error updating star status",
        type: "error",
      });
    } finally {
      setChangeStarLoading(false);
    }
  }

  if (initialLoad) {
    return null;
  }

  return (
      <>
        <ResourceOptionButton
            gap={2}
            _hover={{
              cursor: 'pointer',
              bg: 'blue.200',
            }}
            color={'black'}
            onClick={handleStarResource}
            loading={changeStarLoading}
        >
          {
            starred ? <BsStarFill color={'#EFBF04'}/> : <BsStar/>
          }
          <Box>
            {
              starred ? "Unstar" : "Star"
            }
          </Box>
        </ResourceOptionButton>
      </>
  )
}