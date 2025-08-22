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

console.log('🚨 researchApi.ts module is loading');

import axios, { AxiosInstance } from "axios";
import { User } from 'oidc-client-ts';
import { V2_API_URL, CLIENT_ID } from './constants';

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

console.log('🚀 researchApi interceptors are being registered');

// Request interceptor for authentication - JWT ONLY
researchApi.interceptors.request.use(
  async (config) => {
    const timestamp = new Date().toISOString();
    console.group(`🔐 [${timestamp}] researchApi Authentication Check`);
    console.log('📡 Request URL:', config.url);
    console.log('🎯 Request Method:', config.method?.toUpperCase());
    console.log('🏠 Window Origin:', window.location.origin);
    console.log('⚙️ Base URL:', config.baseURL);
    
    // JWT authentication - NO FALLBACK
    try {
      // Correct OIDC localStorage key format: oidc.user:<authority>:<client_id>
      const oidcStorageKey = `oidc.user:https://auth.dev.cybershuttle.org/realms/default:${CLIENT_ID}`;
      console.log('🔍 OIDC Key:', oidcStorageKey);
      
      // Show ALL localStorage keys for debugging
      console.log('🗄️ localStorage keys:', Object.keys(localStorage));
      
      const oidcStorage = localStorage.getItem(oidcStorageKey);
      console.log('📦 OIDC storage found:', !!oidcStorage);
      
      if (oidcStorage) {
        console.log('✅ OIDC storage found, parsing...');
        try {
          const user = JSON.parse(oidcStorage);
          console.log('👤 User object keys:', Object.keys(user || {}));
          console.log('🕐 Token expires at:', user?.expires_at ? new Date(user.expires_at * 1000).toISOString() : 'N/A');
          console.log('🕐 Current time:', new Date().toISOString());
          
          if (user && user.access_token) {
            const tokenPreview = user.access_token.substring(0, 20) + '...';
            const tokenLength = user.access_token.length;
            console.log('🎫 JWT token found:', tokenPreview);
            console.log('📏 Token length:', tokenLength);
            console.log('👤 User email:', user.profile?.email || 'N/A');
            console.log('🆔 User subject:', user.profile?.sub || 'N/A');
            console.log('🌍 User preferred_username:', user.profile?.preferred_username || 'N/A');
            console.log('🔑 User roles:', user.profile?.roles || 'N/A');
            
            // Check if token is expired
            if (user.expires_at && user.expires_at < Date.now() / 1000) {
              console.error('💀 JWT token is EXPIRED!');
              console.log('⏰ Token expired at:', new Date(user.expires_at * 1000).toISOString());
              console.log('⏰ Current time:', new Date().toISOString());
            } else {
              console.log('✅ JWT token is valid (not expired)');
            }
            
            // Set authorization headers
            config.headers.Authorization = `Bearer ${user.access_token}`;
            
            const claims = {
              "userName": user.profile?.email || user.profile?.sub || user.profile?.preferred_username,
              "gatewayID": "default",
            };
            config.headers["X-Claims"] = JSON.stringify(claims);
            
            console.log('✨ Authentication Method: JWT TOKEN ONLY');
            console.log('📤 Authorization Header:', `Bearer ${tokenPreview}`);
            console.log('📤 X-Claims Header:', claims);
            console.log('✅ Request authenticated successfully');
            console.groupEnd();
            return config;
          } else {
            console.error('❌ No access_token found in user object');
            console.log('🔍 User object structure:', JSON.stringify(user, null, 2));
          }
        } catch (parseError) {
          console.error('💥 Failed to parse OIDC storage JSON:', parseError);
          console.log('📄 Raw OIDC storage:', oidcStorage.substring(0, 200) + '...');
        }
      } else {
        console.error('❌ No OIDC storage found');
      }
    } catch (error) {
      console.error('💥 JWT token processing error:', error);
    }
    
    console.error('🚫 NO AUTHENTICATION - Request will fail with 401');
    
    console.groupEnd();
    return config;
  },
  (error) => {
    const timestamp = new Date().toISOString();
    console.error(`🔥 [${timestamp}] researchApi request interceptor error:`, error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling with detailed logging
researchApi.interceptors.response.use(
  (response) => {
    const timestamp = new Date().toISOString();
    console.group(`✅ [${timestamp}] researchApi Response Success`);
    console.log('📡 URL:', response.config?.url);
    console.log('🎯 Method:', response.config?.method?.toUpperCase());
    console.log('📊 Status:', response.status);
    console.log('📋 Status Text:', response.statusText);
    console.log('📦 Data Type:', typeof response.data);
    console.log('📏 Data Length:', Array.isArray(response.data) ? response.data.length : 'N/A');
    console.groupEnd();
    return response;
  },
  (error) => {
    const timestamp = new Date().toISOString();
    console.group(`❌ [${timestamp}] researchApi Response Error`);
    console.error('🔥 Error Details:', error);
    console.log('📡 URL:', error.config?.url);
    console.log('🎯 Method:', error.config?.method?.toUpperCase());
    console.log('📊 Status:', error.response?.status);
    console.log('📋 Status Text:', error.response?.statusText);
    console.log('💬 Error Message:', error.message);
    
    if (error.response) {
      console.log('📦 Response Data:', error.response.data);
      console.log('📋 Response Headers:', error.response.headers);
      
      if (error.response.status === 401) {
        console.error('🚫 AUTHENTICATION FAILED (401)');
      } else if (error.response.status === 403) {
        console.error('🚫 AUTHORIZATION FAILED (403)');
      } else if (error.response.status >= 500) {
        console.error('💥 SERVER ERROR (5xx)');
      }
    } else if (error.request) {
      console.error('📡 Network Error - No Response Received');
      console.error('🌐 Request was made but no response received');
      console.error('💡 Possible causes:');
      console.error('   1. research-service backend is not running');
      console.error('   2. Network connectivity issues');
      console.error('   3. CORS configuration problems');
      console.error('   4. Wrong backend URL in V2_API_URL');
    } else {
      console.error('⚙️ Request Setup Error');
      console.error('💡 Error occurred while setting up the request');
    }
    
    console.groupEnd();
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
