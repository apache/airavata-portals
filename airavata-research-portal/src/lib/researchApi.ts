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

import axios, { AxiosInstance } from "axios";
import { User } from 'oidc-client-ts';
import { V2_API_URL } from './constants';

// Research Service API configuration for v2 infrastructure resources
const RESEARCH_API_BASE_URL = "http://localhost:8080"; // Airavata research-service port

// User provider for authentication
let getUser: (() => Promise<User | null>) | null = null;

export const setV2UserProvider = (provider: () => Promise<User | null>) => {
  getUser = provider;
};

// Create axios instance for research service API
const researchApi: AxiosInstance = axios.create({
  baseURL: V2_API_URL || `${RESEARCH_API_BASE_URL}/api/v2/rf`,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// Request interceptor for authentication - prioritize JWT tokens
researchApi.interceptors.request.use(
  async (config) => {
    // Try JWT authentication first
    try {
      const oidcStorage = localStorage.getItem(`oidc.user:${window.location.origin}/oauth_callback`);
      if (oidcStorage) {
        const user = JSON.parse(oidcStorage);
        if (user && user.access_token) {
          config.headers.Authorization = `Bearer ${user.access_token}`;
          config.headers["X-Claims"] = JSON.stringify({
            "userName": user.profile.email || user.profile.sub,
            "gatewayID": "default",
          });
          return config;
        }
      }
    } catch (error) {
      console.warn('Failed to add JWT token to researchApi request:', error);
    }
    
    // Fallback to dev API key for development
    const devApiKey = import.meta.env.VITE_DEV_API_KEY;
    if (devApiKey) {
      config.headers["X-API-Key"] = devApiKey;
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
researchApi.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("Research API Error:", error.response?.data || error.message);
    return Promise.reject(error);
  },
);

// Research API service functions for v2 infrastructure resources
export const researchApiService = {
  // Compute Resources V2 endpoints
  async getComputeResources(params?: {
    pageNumber?: number;
    pageSize?: number;
    nameSearch?: string;
    tag?: string[];
  }) {
    const queryParams = new URLSearchParams();
    if (params?.pageNumber !== undefined)
      queryParams.append("pageNumber", params.pageNumber.toString());
    if (params?.pageSize !== undefined)
      queryParams.append("pageSize", params.pageSize.toString());
    if (params?.nameSearch) queryParams.append("nameSearch", params.nameSearch);
    if (params?.tag) {
      params.tag.forEach((t) => queryParams.append("tag", t));
    }

    const fullUrl = `/compute-resources/?${queryParams}`;
    console.log(
      "🌐 Research API calling:",
      `${researchApi.defaults.baseURL}${fullUrl}`,
    );

    const response = await researchApi.get(fullUrl);
    return response.data;
  },

  async getComputeResourceById(id: string) {
    const response = await researchApi.get(`/compute-resources/${id}`);
    return response.data;
  },

  async createComputeResource(computeResource: any) {
    const response = await researchApi.post(
      "/compute-resources/",
      computeResource,
    );
    return response.data;
  },

  async updateComputeResource(id: string, computeResource: any) {
    const response = await researchApi.put(
      `/compute-resources/${id}`,
      computeResource,
    );
    return response.data;
  },

  async deleteComputeResource(id: string) {
    const response = await researchApi.delete(`/compute-resources/${id}`);
    return response.data;
  },

  async searchComputeResources(keyword: string) {
    const response = await researchApi.get(
      `/compute-resources/search?keyword=${encodeURIComponent(keyword)}`,
    );
    return response.data;
  },

  async getComputeResourcesByType(computeType: string) {
    const response = await researchApi.get(
      `/compute-resources/type/${computeType}`,
    );
    return response.data;
  },

  async starComputeResource(id: string) {
    const response = await researchApi.post(`/compute-resources/${id}/star`);
    return response.data;
  },

  async checkComputeResourceStarred(id: string) {
    const response = await researchApi.get(`/compute-resources/${id}/star`);
    return response.data;
  },

  async getComputeResourceStarCount(id: string) {
    const response = await researchApi.get(
      `/compute-resources/${id}/stars/count`,
    );
    return response.data;
  },

  // Storage Resources V2 endpoints
  async getStorageResources(params?: {
    pageNumber?: number;
    pageSize?: number;
    nameSearch?: string;
    tag?: string[];
  }) {
    const queryParams = new URLSearchParams();
    if (params?.pageNumber !== undefined)
      queryParams.append("pageNumber", params.pageNumber.toString());
    if (params?.pageSize !== undefined)
      queryParams.append("pageSize", params.pageSize.toString());
    if (params?.nameSearch) queryParams.append("nameSearch", params.nameSearch);
    if (params?.tag) {
      params.tag.forEach((t) => queryParams.append("tag", t));
    }

    const fullUrl = `/storage-resources/?${queryParams}`;
    console.log(
      "🌐 Research API calling:",
      `${researchApi.defaults.baseURL}${fullUrl}`,
    );

    const response = await researchApi.get(fullUrl);
    return response.data;
  },

  async getStorageResourceById(id: string) {
    const response = await researchApi.get(`/storage-resources/${id}`);
    return response.data;
  },

  async createStorageResource(storageResource: any) {
    const response = await researchApi.post(
      "/storage-resources/",
      storageResource,
    );
    return response.data;
  },

  async updateStorageResource(id: string, storageResource: any) {
    const response = await researchApi.put(
      `/storage-resources/${id}`,
      storageResource,
    );
    return response.data;
  },

  async deleteStorageResource(id: string) {
    const response = await researchApi.delete(`/storage-resources/${id}`);
    return response.data;
  },

  async searchStorageResources(keyword: string) {
    const response = await researchApi.get(
      `/storage-resources/search?keyword=${encodeURIComponent(keyword)}`,
    );
    return response.data;
  },

  async getStorageResourcesByType(storageType: string) {
    const response = await researchApi.get(
      `/storage-resources/type/${storageType}`,
    );
    return response.data;
  },

  async starStorageResource(id: string) {
    const response = await researchApi.post(`/storage-resources/${id}/star`);
    return response.data;
  },

  async checkStorageResourceStarred(id: string) {
    const response = await researchApi.get(`/storage-resources/${id}/star`);
    return response.data;
  },

  async getStorageResourceStarCount(id: string) {
    const response = await researchApi.get(
      `/storage-resources/${id}/stars/count`,
    );
    return response.data;
  },

};

export default researchApi;
